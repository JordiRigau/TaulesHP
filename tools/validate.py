# -*- coding: utf-8 -*-
"""Validacion de data/master.json contra criterios INDEPENDIENTES del extractor.

No comprueba "que el extractor hizo lo que dice", sino que los numeros
cumplen fisica y estructura conocidas de antemano. Los fallos aqui pueden ser
de extraccion o erratas del propio PDF; el informe distingue ambos casos.
"""
from __future__ import unicode_literals
import io, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import load, interp, PROPS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'data', 'validation_report.txt')

issues = []


def bad(sub, kind, msg):
    issues.append((sub['name'], kind, msg))


# ---------------------------------------------------------------- estructura
def check_units(sub):
    if sub['T_unit'] not in ('C', 'K'):
        bad(sub, 'UNIDADES', 'unidad de T no unica: %s' % sub['T_unit'])


def check_completeness(sub):
    for tag, rows in (('sat_by_T', sub['sat_by_T']), ('sat_by_P', sub['sat_by_P'])):
        for r in rows:
            miss = [k for k, v in r.items() if v is None]
            if miss:
                bad(sub, 'HUECO', '%s fila %s: faltan %s'
                    % (tag, r.get('T', r.get('P')), sorted(miss)))
    for b in sub['isobars']:
        for r in b['rows']:
            miss = [k for k, v in r.items() if v is None]
            if miss:
                bad(sub, 'HUECO', 'isobara %s T=%s: faltan %s'
                    % (b['P'], r['T'], sorted(miss)))


# ------------------------------------------------------------------- fisica
def check_phase_order(sub):
    """v_v>v_l, u_v>u_l, h_v>h_l, s_v>s_l salvo en el punto critico."""
    Tc = sub['Tc_K']
    for tag, rows, key in (('sat(T)', sub['sat_by_T'], 'T'),
                           ('sat(P)', sub['sat_by_P'], 'P')):
        for r in rows:
            crit = False
            if tag == 'sat(T)' and Tc is not None:
                Tk = r['T'] + 273.15 if sub['T_unit'] == 'C' else r['T']
                crit = abs(Tk - Tc) < 0.6
            if tag == 'sat(P)' and sub['Pc_MPa'] is not None:
                crit = abs(r['P'] - sub['Pc_MPa']) < 0.02 * sub['Pc_MPa']
            for p in PROPS:
                a, b = r[p + 'l'], r[p + 'v']
                if a is None or b is None:
                    continue
                if crit:
                    continue
                if b <= a:
                    bad(sub, 'FASE', '%s %s=%s: %s_v(%.6g) <= %s_l(%.6g)'
                        % (tag, key, r[key], p, b, p, a))


def check_positive(sub):
    for r in sub['sat_by_T']:
        for k in ('vl', 'vv', 'Pl', 'Pv'):
            if r[k] is not None and r[k] <= 0:
                bad(sub, 'SIGNO', 'sat(T) T=%s: %s=%s no positivo' % (r['T'], k, r[k]))
    for b in sub['isobars']:
        for r in b['rows']:
            if r['v'] is not None and r['v'] <= 0:
                bad(sub, 'SIGNO', 'isobara %s T=%s: v=%s' % (b['P'], r['T'], r['v']))


# ------------------------------------------------------------- monotonias
def check_monotonic(sub):
    rows = sub['sat_by_T']
    for i in range(len(rows) - 1):
        if rows[i + 1]['T'] <= rows[i]['T']:
            bad(sub, 'ORDEN', 'sat(T): T no creciente en %s -> %s'
                % (rows[i]['T'], rows[i + 1]['T']))
        if rows[i + 1]['Pl'] <= rows[i]['Pl']:
            bad(sub, 'ORDEN', 'sat(T): P_sat no creciente en T=%s (%s -> %s)'
                % (rows[i]['T'], rows[i]['Pl'], rows[i + 1]['Pl']))
    rows = sub['sat_by_P']
    for i in range(len(rows) - 1):
        if rows[i + 1]['P'] <= rows[i]['P']:
            bad(sub, 'ORDEN', 'sat(P): P no creciente en %s' % rows[i]['P'])
    for b in sub['isobars']:
        rs = b['rows']
        for i in range(len(rs) - 1):
            if rs[i + 1]['T'] < rs[i]['T']:
                bad(sub, 'ORDEN', 'isobara %s: T decrece en %s' % (b['P'], rs[i]['T']))


def check_isobar_s_monotone(sub):
    """s y h deben crecer con T a P constante (necesario para la busqueda
    inversa: si no son monotonas, la inversa no es unica)."""
    for b in sub['isobars']:
        rs = b['rows']
        for p in ('h', 's'):
            for i in range(len(rs) - 1):
                a, c = rs[i][p], rs[i + 1][p]
                if a is None or c is None:
                    continue
                if c < a - 1e-9:
                    bad(sub, 'MONOT-%s' % p.upper(),
                        'isobara %s MPa: %s decrece entre T=%s y T=%s (%.6g -> %.6g)'
                        % (b['P'], p, rs[i]['T'], rs[i + 1]['T'], a, c))


# --------------------------------------------- redundancia sat(T) vs sat(P)
def check_sat_redundancy(sub):
    """Las dos tablas de saturacion describen la MISMA curva.

    Se reconstruye T_sat(P) interpolando linealmente la tabla por T y se
    compara con la tabla por P. La desviacion mide el error que se cometeria
    si la app guardase solo una de las dos, que es justo la decision de
    arquitectura en juego (P_sat(T) es exponencial, no lineal).
    """
    st, sp = sub['sat_by_T'], sub['sat_by_P']
    if not st or not sp:
        return None
    Ps = [r['Pl'] for r in st]
    Ts = [r['T'] for r in st]
    worst = (0.0, None)
    errs = []
    for r in sp:
        Tint = interp(r['P'], Ps, Ts)
        if Tint is None:
            continue
        e = abs(Tint - r['Tl'])
        errs.append(e)
        if e > worst[0]:
            worst = (e, r['P'])
    if errs:
        mean = sum(errs) / len(errs)
        sub['_redund'] = (mean, worst[0], worst[1], len(errs))
    return sub.get('_redund')


# ------------------------------- continuidad isobara <-> curva de saturacion
def check_isobar_sat_continuity(sub, tol_rel=0.02):
    """En cada isobara, las dos filas con la misma T son el liquido y el vapor
    saturados a esa P: deben coincidir con la tabla de saturacion por P."""
    sp = sub['sat_by_P']
    if not sp:
        return
    Ps = [r['P'] for r in sp]
    for b in sub['isobars']:
        # Cerca del punto critico la curva de saturacion se vuelve casi
        # vertical y la interpolacion lineal de referencia deja de valer como
        # patron de comparacion. No es un fallo de extraccion.
        if sub['Pc_MPa'] and b['P'] > 0.9 * sub['Pc_MPa']:
            continue
        rs = b['rows']
        dup = [i for i in range(len(rs) - 1)
               if abs(rs[i + 1]['T'] - rs[i]['T']) < 1e-9]
        if not dup:
            continue
        i = dup[0]
        liq, vap = rs[i], rs[i + 1]
        if liq['v'] > vap['v']:
            liq, vap = vap, liq
        for p in PROPS:
            for tag, row in (('l', liq), ('v', vap)):
                ref = interp(b['P'], Ps, [r[p + tag] for r in sp])
                if ref is None or row[p] is None:
                    continue
                den = max(abs(ref), 1e-6)
                if abs(row[p] - ref) / den > tol_rel:
                    bad(sub, 'CONTINUIDAD',
                        'isobara %s MPa: %s_%s tabla=%.6g vs saturacion=%.6g'
                        % (b['P'], p, tag, row[p], ref))


def split_at_phase_jump(rows, tol=1e-9):
    """Parte una isobara en tramos continuos, cortando en el salto de fase
    (las dos filas consecutivas con la misma T: liquido y vapor saturados)."""
    segs, cur = [], []
    for i, r in enumerate(rows):
        cur.append(r)
        if i + 1 < len(rows) and abs(rows[i + 1]['T'] - r['T']) <= tol:
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return segs


# --------------------------------------------------- deteccion de erratas
def _direction_breaks(ys, max_break_frac=0.15):
    """Indices que van contra el sentido dominante de la serie.

    El sentido se DEDUCE de los datos en vez de imponerlo. Hace falta porque
    no todas las columnas tienen el mismo sentido en todas las sustancias:
    el benceno es un fluido retrogrado ("seco") y su s_v CRECE con T, al
    reves que en el agua o el amoniaco. Imponer un sentido fijo marcaria
    esa fisica real como si fuera una errata.

    Si demasiados tramos van al reves, la columna no es monotona (p.ej. h_v,
    que pasa por un maximo) y se descarta entera en vez de generar ruido.
    """
    d = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    up = sum(1 for x in d if x > 0)
    dn = sum(1 for x in d if x < 0)
    if up + dn < 3:
        return []
    sign = 1 if up >= dn else -1
    breaks = [i for i, x in enumerate(d) if x * sign < 0]
    if len(breaks) > max_break_frac * len(d):
        return []
    return breaks


def _spikes(ys, factor=3.0):
    """Picos de un solo punto: la serie sale y vuelve inmediatamente.

    Sirve para columnas unimodales, donde no se puede exigir un sentido.
    Una errata da un pico estrecho (los dos vecinos casi coinciden entre si
    mientras los saltos hasta el punto son grandes); un maximo fisico, en
    cambio, es un giro suave en el que los vecinos ya estan separados.
    """
    steps = sorted(abs(ys[i + 1] - ys[i]) for i in range(len(ys) - 1))
    if not steps:
        return []
    typical = steps[len(steps) // 2]
    out = []
    for i in range(1, len(ys) - 1):
        a, b, c = ys[i - 1], ys[i], ys[i + 1]
        d1, d2 = b - a, c - b
        if d1 * d2 >= 0:
            continue
        # El maximo fisico real de u_v/h_v es un giro casi simetrico y muy
        # plano (c ~ a), que dispararia la prueba de estrechez por division
        # entre casi cero. Se exige ademas que el pico sea grande frente al
        # paso tipico de la columna: una errata lo es, un maximo suave no.
        if (min(abs(d1), abs(d2)) > factor * abs(c - a)
                and min(abs(d1), abs(d2)) > 3.0 * typical):
            out.append(i)
    return out


def check_outliers(sub):
    """Busca erratas del PDF como roturas aisladas de monotonia.

    Una errata tipografica rompe el sentido de una columna que por lo demas
    es monotona; ese perfil (una rotura suelta entre decenas de tramos
    coherentes) es lo que se busca aqui. No hay umbral de magnitud, asi que
    funciona igual en columnas que recorren nueve ordenes de magnitud
    (v_v del mercurio) que en las que rondan el cero.
    """
    rows = sub['sat_by_T']
    if len(rows) > 4:
        # se excluye la ultima fila: es el punto critico, donde todas las
        # columnas de liquido y vapor convergen y la monotonia no aplica.
        body = rows[:-1]
        for key in ('Pl', 'vl', 'vv', 'ul', 'hl', 'sl', 'sv'):
            ys = [r.get(key) for r in body]
            if any(y is None for y in ys):
                continue
            for i in _direction_breaks(ys):
                bad(sub, 'ERRATA?', 'sat(T) entre T=%s y T=%s: %s rompe la '
                    'monotonia (%.6g -> %.6g)'
                    % (body[i]['T'], body[i + 1]['T'], key, ys[i], ys[i + 1]))
        # u_v y h_v son unimodales (maximo antes del punto critico), asi que
        # no admiten prueba de sentido; se buscan picos de un solo punto.
        for key in ('uv', 'hv'):
            ys = [r.get(key) for r in body]
            if any(y is None for y in ys):
                continue
            for i in _spikes(ys):
                bad(sub, 'ERRATA?', 'sat(T) T=%s: %s=%.6g es un pico aislado '
                    '(vecinos %.6g / %.6g)'
                    % (body[i]['T'], key, ys[i], ys[i - 1], ys[i + 1]))

    for b in sub['isobars']:
        # Dentro de una isobara y de una misma fase, v, u, h y s crecen con T
        # (c_p > 0). Esa monotonia es ademas la que hace unica la busqueda
        # inversa de T dado h o s, asi que conviene verificarla de verdad.
        for seg in split_at_phase_jump(b['rows']):
            if len(seg) < 4:
                continue
            for key in ('v', 'u', 'h', 's'):
                ys = [r[key] for r in seg]
                if any(y is None for y in ys):
                    continue
                for i in _direction_breaks(ys):
                    bad(sub, 'ERRATA?', 'isobara %s MPa entre T=%s y T=%s: %s '
                        'rompe la monotonia (%.6g -> %.6g)'
                        % (b['P'], seg[i]['T'], seg[i + 1]['T'], key,
                           ys[i], ys[i + 1]))


# ------------------------------------------------------------------ informe
def main():
    subs = load()
    lines = []
    lines.append('INFORME DE VALIDACION DE data/master.json')
    lines.append('=' * 72)
    lines.append('')

    red = []
    for s in subs:
        check_units(s)
        check_completeness(s)
        check_phase_order(s)
        check_positive(s)
        check_monotonic(s)
        r = check_sat_redundancy(s)
        if r:
            red.append((s['name'], s['T_unit'], r))
        check_isobar_sat_continuity(s)
        check_outliers(s)

    lines.append('1) INVENTARIO')
    lines.append('-' * 72)
    tot = 0
    for s in subs:
        n = (len(s['sat_by_T']) + len(s['sat_by_P'])
             + sum(len(b['rows']) for b in s['isobars']))
        tot += n
        lines.append('%-26s T[%s] sat_T=%3d sat_P=%3d isobaras=%3d filas=%4d %s'
                     % (s['name'], s['T_unit'], len(s['sat_by_T']),
                        len(s['sat_by_P']), len(s['isobars']), n,
                        'MEZCLA' if s['blend'] else ''))
    lines.append('TOTAL filas: %d' % tot)
    lines.append('')

    lines.append('2) REDUNDANCIA sat(T) vs sat(P):  error de reconstruir T_sat(P)')
    lines.append('   interpolando LINEALMENTE la tabla por T')
    lines.append('-' * 72)
    for name, unit, (mean, wmax, wP, n) in red:
        lines.append('%-26s medio=%.3f %s   maximo=%.3f %s (a P=%s MPa)  n=%d'
                     % (name, mean, unit, wmax, unit, wP, n))
    lines.append('')

    lines.append('3) INCIDENCIAS')
    lines.append('-' * 72)
    if not issues:
        lines.append('ninguna')
    else:
        from collections import Counter
        c = Counter(k for _, k, _ in issues)
        lines.append('resumen: ' + ', '.join('%s=%d' % kv for kv in c.most_common()))
        lines.append('')
        for name, kind, msg in issues:
            lines.append('[%-12s] %-26s %s' % (kind, name, msg))

    txt = '\n'.join(lines)
    with io.open(REPORT, 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
