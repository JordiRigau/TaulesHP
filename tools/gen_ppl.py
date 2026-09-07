# -*- coding: utf-8 -*-
"""Genera los ficheros de datos PPL para la HP Prime desde data/master.json.

Uso:
    python tools/gen_ppl.py                 # sustancias por defecto
    python tools/gen_ppl.py AIGUA AMONIAC   # las que se indiquen
    python tools/gen_ppl.py --all
    python tools/gen_ppl.py --list

El bloque de datos PPL NUNCA se edita a mano: si un valor esta mal, se corrige
el maestro (o el extractor) y se vuelve a generar.

Formato generado, igual para sustancias puras y mezclas para que el codigo PPL
tenga un solo camino (en una pura, las dos columnas de burbuja y rocio llevan
el mismo valor):

    <K>ST : matriz n x 11  [T, Pl, Pv, vl, vv, ul, uv, hl, hv, sl, sv]
    <K>SP : matriz n x 11  [P, Tl, Tv, vl, vv, ul, uv, hl, hv, sl, sv]
    <K>IX : matriz m x 4   [P, fila_inicial, n_filas, filas_rama_liquida]
    <K>IS : matriz N x 5   [T, v, u, h, s]   (todas las isobaras seguidas)
    <K>MD : lista          {nombre, unidadT(0=C,1=K), mezcla, Tc_K,
                            Pc_MPa, M_g_mol, omega, vc_m3kg}
"""
from __future__ import unicode_literals
import io, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import load, PROPS
from engine import branches

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'ppl')

# Por defecto solo las sustancias habituales de la asignatura: meter las 14
# multiplica por cinco el tiempo de compilacion en la calculadora sin que
# normalmente se usen.
DEFAULT = ['AIGUA', 'AMONIAC', 'R134A']

SAT_COLS = ['vl', 'vv', 'ul', 'uv', 'hl', 'hv', 'sl', 'sv']


def num(x):
    """Numero en el formato mas corto que conserva el valor exacto.

    repr() da la representacion mas corta que reconstruye el mismo float, asi
    que no se pierde ni un digito de los tabulados. Se pasa a mayusculas
    porque PPL espera el exponente como 'E'.
    """
    if x is None:
        return '0'
    s = repr(float(x))
    if s.endswith('.0'):
        s = s[:-2]
    return s.upper().replace('E+', 'E')


def mat(rows):
    return '[' + ','.join('[' + ','.join(num(v) for v in r) + ']'
                          for r in rows) + ']'


def gen_substance(sub):
    K = sub['key'][:6]
    out = []
    out.append('// %s  -- generado por tools/gen_ppl.py, NO EDITAR' % sub['name'])
    out.append('// unidades: P[MPa] T[%s] v[m3/kg] u,h[kJ/kg] s[kJ/(kg K)]'
               % sub['T_unit'])

    st = [[r['T'], r['Pl'], r['Pv']] + [r[c] for c in SAT_COLS]
          for r in sub['sat_by_T']]
    sp = [[r['P'], r['Tl'], r['Tv']] + [r[c] for c in SAT_COLS]
          for r in sub['sat_by_P']]

    ix, iso = [], []
    for b in sub['isobars']:
        liq, vap = branches(b)
        start = len(iso) + 1                      # PPL indexa desde 1
        for r in b['rows']:
            iso.append([r['T'], r['v'], r['u'], r['h'], r['s']])
        ix.append([b['P'], start, len(b['rows']), len(liq)])

    out.append('EXPORT %sST:=%s;' % (K, mat(st) if st else '[[0]]'))
    out.append('EXPORT %sSP:=%s;' % (K, mat(sp) if sp else '[[0]]'))
    out.append('EXPORT %sIX:=%s;' % (K, mat(ix) if ix else '[[0,0,0,0]]'))
    out.append('EXPORT %sIS:=%s;' % (K, mat(iso) if iso else '[[0,0,0,0,0]]'))
    # Metadatos. Los indices 6 y 7 (masa molar y factor acentrico) no los usa
    # la app de tablas, pero son justo lo que hace falta para gases: R = Ru/M,
    # y Tc/Pc/omega dan el factor de compresibilidad generalizado.
    out.append('EXPORT %sMD:={"%s",%d,%d,%s,%s,%s,%s,%s};'
               % (K, sub['name'].replace('"', "'"),
                  1 if sub['T_unit'] == 'K' else 0,
                  1 if sub['blend'] else 0,
                  num(sub['Tc_K']), num(sub['Pc_MPa']),
                  num(sub['molar_mass']), num(sub['omega']),
                  num(sub['vc'])))
    return '\n'.join(out) + '\n'


def main(argv):
    subs = {s['key']: s for s in load()}
    if '--list' in argv:
        for k in sorted(subs):
            s = subs[k]
            n = (len(s['sat_by_T']) * 11 + len(s['sat_by_P']) * 11
                 + sum(len(b['rows']) * 5 for b in s['isobars']))
            print('%-18s %-28s %6d valores' % (k, s['name'], n))
        return 0

    if '--all' in argv:
        # Las habituales primero: el desplegable se recorre en este orden y
        # en un examen no interesa bajar diez posiciones para llegar al
        # R-134a. El resto van detras, alfabeticamente.
        keys = DEFAULT + [k for k in sorted(subs) if k not in DEFAULT]
    else:
        keys = [a for a in argv[1:] if not a.startswith('--')] or DEFAULT

    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)

    total = 0
    made = []
    for k in keys:
        if k not in subs:
            print('AVISO: sustancia desconocida %r (usa --list)' % k)
            continue
        txt = gen_substance(subs[k])
        path = os.path.join(OUTDIR, 'TDAT_%s.txt' % k[:6])
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(txt)
        total += len(txt)
        made.append((k[:6], subs[k]['name'], len(txt)))
        print('%-28s -> %-24s %7.1f KB'
              % (subs[k]['name'], os.path.basename(path), len(txt) / 1024.0))

    # registro de sustancias cargadas, para que el programa principal sepa
    # que hay disponible sin tener que probar variable por variable
    reg = ['// generado por tools/gen_ppl.py, NO EDITAR',
           'EXPORT TSUBS:={%s};' % ','.join('"%s"' % m[0] for m in made),
           'EXPORT TNAMS:={%s};' % ','.join('"%s"' % m[1].replace('"', "'")
                                            for m in made)]
    with io.open(os.path.join(OUTDIR, 'TDAT_REG.txt'), 'w',
                 encoding='utf-8') as f:
        f.write('\n'.join(reg) + '\n')

    print('-' * 60)
    print('total %.1f KB en %d sustancias' % (total / 1024.0, len(made)))
    print('el .hpprgm que se arrastra a la calculadora: tools/build_hp.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
