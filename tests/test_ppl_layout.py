# -*- coding: utf-8 -*-
"""Comprueba los ficheros de datos PPL generados, sin necesidad de la Prime.

Que compile en la calculadora no garantiza que los indices esten bien. Lo que
mas facilmente se rompe al pasar el motor a PPL es la ARITMETICA DE INDICES:
las matrices son 1-based, las isobaras van una detras de otra en una sola
matriz y cada una se parte en rama liquida y rama vapor con un contador.

Este arnes lee los .hpprgm generados, reimplementa el acceso EXACTAMENTE como
lo hace TERMO.hpprgm (mismos indices, mismo 1-based) y compara el resultado
con el motor de referencia. Asi un desfase de una fila se ve aqui y no en el
examen.
"""
from __future__ import unicode_literals
import io, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import engine as E
from model import PROPS

PPLDIR = os.path.join(ROOT, 'ppl')

PASS, FAIL = [], []


def note(ok, msg):
    (PASS if ok else FAIL).append(msg)


# ------------------------------------------------------- lectura del .hpprgm
def parse_matrix(txt):
    rows = []
    for m in re.finditer(r'\[([^\[\]]+)\]', txt):
        rows.append([float(x) for x in m.group(1).split(',')])
    return rows


def load_ppl(key):
    path = os.path.join(PPLDIR, 'TDAT_%s.hpprgm' % key)
    src = io.open(path, encoding='utf-8').read()
    out = {}
    for name in ('ST', 'SP', 'IX', 'IS'):
        m = re.search(r'EXPORT\s+\w*%s\s*:=\s*(\[\[.*?\]\])\s*;' % name, src, re.S)
        if not m:
            raise AssertionError('no encuentro %s en %s' % (name, path))
        out[name] = parse_matrix(m.group(1))
    m = re.search(r'EXPORT\s+\w*MD\s*:=\s*\{(.*?)\};', src, re.S)
    out['MD'] = m.group(1)
    return out


# ------------------------------- replica del acceso tal cual lo hace el PPL
def ppl_brk(M, c, x, r0, n):
    """TBRK: 1-based, devuelve 0 si x cae fuera del rango (no extrapola)."""
    if n < 2:
        return 0
    if x < M[r0 - 1][c - 1] - 1e-9:
        return 0
    if x > M[r0 + n - 2][c - 1] + 1e-9:
        return 0
    lo, hi = r0, r0 + n - 1
    while hi - lo > 1:
        mid = int((lo + hi) / 2)
        if M[mid - 1][c - 1] <= x:
            lo = mid
        else:
            hi = mid
    return lo


def ppl_isot(D, k, T, ph):
    """TISOT: interpola dentro de la isobara k (1-based) en la rama ph."""
    IX, IS = D['IX'], D['IS']
    r0 = int(IX[k - 1][1]); nn = int(IX[k - 1][2]); nl = int(IX[k - 1][3])
    if ph == 0:
        if nl < 2:
            return None
        i = ppl_brk(IS, 1, T, r0, nl)
    else:
        if nn - nl < 2:
            return None
        i = ppl_brk(IS, 1, T, r0 + nl, nn - nl)
    if i == 0:
        return None
    a, b = IS[i - 1], IS[i]
    f = 0.0 if b[0] == a[0] else (T - a[0]) / (b[0] - a[0])
    return [a[j] + f * (b[j] - a[j]) for j in range(1, 5)]


def ppl_satp(D, P):
    SP = D['SP']
    i = ppl_brk(SP, 1, P, 1, len(SP))
    if i == 0:
        return None
    a, b = SP[i - 1], SP[i]
    f = 0.0 if b[0] == a[0] else (P - a[0]) / (b[0] - a[0])
    return [a[j] + f * (b[j] - a[j]) for j in range(1, 11)]


# ----------------------------------------------------------------- pruebas
def test_layout_consistency(key, sub, D):
    """El indice debe cubrir la matriz de isobaras sin huecos ni solapes."""
    IX, IS = D['IX'], D['IS']
    if not sub['isobars']:
        # El mercurio no tiene isobaras ni tabla por P: el generador escribe
        # una matriz de relleno porque PPL no admite una matriz vacia.
        note(len(IX) == 1 and IX[0] == [0, 0, 0, 0],
             '%s: sin isobaras, IX es el relleno' % key)
        note(len(D['ST']) == len(sub['sat_by_T']),
             '%s: ST %d filas vs %d' % (key, len(D['ST']), len(sub['sat_by_T'])))
        return
    note(len(IX) == len(sub['isobars']),
         '%s: %d isobaras en IX vs %d en el maestro'
         % (key, len(IX), len(sub['isobars'])))
    expect = 1
    total = 0
    for k, row in enumerate(IX):
        P, r0, nn, nl = row[0], int(row[1]), int(row[2]), int(row[3])
        b = sub['isobars'][k]
        note(abs(P - b['P']) < 1e-12,
             '%s isobara %d: P=%s vs %s' % (key, k, P, b['P']))
        note(r0 == expect,
             '%s isobara %s: empieza en %d, se esperaba %d' % (key, P, r0, expect))
        note(nn == len(b['rows']),
             '%s isobara %s: %d filas vs %d' % (key, P, nn, len(b['rows'])))
        liq, vap = E.branches(b)
        note(nl == len(liq),
             '%s isobara %s: rama liquida %d vs %d' % (key, P, nl, len(liq)))
        expect += nn
        total += nn
    note(total == len(IS),
         '%s: IX suma %d filas, IS tiene %d' % (key, total, len(IS)))
    note(len(D['ST']) == len(sub['sat_by_T']),
         '%s: ST %d filas vs %d' % (key, len(D['ST']), len(sub['sat_by_T'])))
    note(len(D['SP']) == len(sub['sat_by_P']),
         '%s: SP %d filas vs %d' % (key, len(D['SP']), len(sub['sat_by_P'])))


def test_values_roundtrip(key, sub, D):
    """Cada valor tabulado debe llegar intacto al fichero PPL."""
    worst = 0.0
    for k, b in enumerate(sub['isobars']):
        r0 = int(D['IX'][k][1])
        for j, r in enumerate(b['rows']):
            got = D['IS'][r0 - 1 + j]
            for c, p in enumerate(['T'] + PROPS):
                a = r[p]
                if a is None:
                    continue
                d = abs(got[c] - a)
                worst = max(worst, d / (abs(a) + 1e-12))
    note(worst < 1e-15,
         '%s: peor desviacion relativa al serializar = %.3g' % (key, worst))


def test_against_engine(key, sub, D, n=400):
    """El acceso PPL y el motor deben dar lo mismo en puntos al azar."""
    rnd = random.Random(20250819)
    bad = 0
    checked = 0
    if not sub['isobars']:
        note(True, '%s: sin isobaras, nada que comparar' % key)
        return
    for _ in range(n):
        k = rnd.randrange(len(sub['isobars']))
        b = sub['isobars'][k]
        liq, vap = E.branches(b)
        rows = vap if (vap and rnd.random() < 0.7) else liq
        if len(rows) < 2:
            continue
        i = rnd.randrange(len(rows) - 1)
        T = rows[i]['T'] + rnd.random() * (rows[i + 1]['T'] - rows[i]['T'])
        ph = 1 if rows is vap else 0
        got = ppl_isot(D, k + 1, T, ph)
        try:
            exp = E.iso_at_T(b, T, E.VAPOR if ph else E.LIQUID)
        except E.FueraDeRango:
            continue
        checked += 1
        if got is None:
            bad += 1
            continue
        for c, p in enumerate(PROPS):
            if abs(got[c] - exp[p]) > 1e-9 * (abs(exp[p]) + 1):
                bad += 1
                break
    note(bad == 0 and checked > 50,
         '%s: %d/%d puntos coinciden con el motor' % (key, checked - bad, checked))


def test_satp_against_engine(key, sub, D, n=200):
    rnd = random.Random(7)
    if not sub['sat_by_P']:
        return
    Ps = [r['P'] for r in sub['sat_by_P']]
    bad = 0
    for _ in range(n):
        P = rnd.uniform(Ps[0], Ps[-1])
        got = ppl_satp(D, P)
        exp = E.sat_at_P(sub, P)
        order = ['Tl', 'Tv', 'vl', 'vv', 'ul', 'uv', 'hl', 'hv', 'sl', 'sv']
        for c, kk in enumerate(order):
            if abs(got[c] - exp[kk]) > 1e-9 * (abs(exp[kk]) + 1):
                bad += 1
                break
    note(bad == 0, '%s: saturacion por P coincide en %d puntos (%d fallos)'
         % (key, n, bad))


def test_merged_matches(subs):
    """La version compacta (ppl/compacte/) ha de portar EXACTAMENT els
    mateixos blocs de dades que els fitxers per substancia.

    Es un fitxer generat a part, i si algun dia es toca un dels dos camins
    sense l'altre, aqui es veu de seguida.
    """
    mp = os.path.join(PPLDIR, 'compacte', 'TDAT.txt')
    if not os.path.isfile(mp):
        return
    merged = io.open(mp, encoding='utf-8').read()
    falta = 0
    for f in sorted(os.listdir(PPLDIR)):
        if not (f.startswith('TDAT_') and f.endswith('.hpprgm')):
            continue
        if f == 'TDAT_REG.hpprgm':
            continue
        for line in io.open(os.path.join(PPLDIR, f), encoding='utf-8').read().split(chr(10)):
            if line.startswith('EXPORT') and line not in merged:
                falta += 1
    note(falta == 0,
         'compacte/TDAT.txt: %d blocs de dades no coincideixen' % falta)


def main():
    subs = E.substances()
    files = [f for f in os.listdir(PPLDIR)
             if f.startswith('TDAT_') and not f.endswith('REG.hpprgm')]
    if not files:
        print('No hay ficheros generados: ejecuta tools/gen_ppl.py')
        return 1
    for f in sorted(files):
        key = f[5:-7]
        sub = None
        for s in subs.values():
            if s['key'][:6] == key:
                sub = s
                break
        if sub is None:
            note(False, 'no se encuentra la sustancia del fichero %s' % f)
            continue
        D = load_ppl(key)
        test_layout_consistency(key, sub, D)
        test_values_roundtrip(key, sub, D)
        test_against_engine(key, sub, D)
        test_satp_against_engine(key, sub, D)

    test_merged_matches(subs)

    print('PASS: %d' % len(PASS))
    print('FAIL: %d' % len(FAIL))
    for x in FAIL:
        print('  FAIL ' + x)
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
