# -*- coding: utf-8 -*-
"""Motor termodinamico de referencia (Python).

Implementa la misma logica que despues se traduce a PPL para la HP Prime:
determinacion de region, enrutado por pares de entrada, interpolacion lineal
y busqueda inversa. Sirve como banco de pruebas rapido y como especificacion
ejecutable del comportamiento esperado en la calculadora.

Criterios de diseno (deliberados):

* La interpolacion es SIEMPRE lineal, en el mismo orden en que se hace a
  mano: primero en T dentro de cada isobara, despues en P entre isobaras.
  El objetivo es reproducir la solucion del profesor, no el valor mas exacto.
* Nunca se extrapola en silencio: fuera de rango se lanza FueraDeRango.
* La zona bifasica se resuelve SIEMPRE con las tablas de saturacion, no con
  las isobaras, porque son las que el alumno usa a mano.
* Cada estado devuelto lleva 'avisos' con lo que la app debe mostrar en
  pantalla (aproximaciones, fronteras, fases mezcladas).
"""
from __future__ import unicode_literals
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import load, PROPS

LIQUID, MIX, VAPOR = 'LIQUID', 'MIX', 'VAPOR'
REGION_ES = {LIQUID: 'Liq.comprimido', MIX: 'Bifasico', VAPOR: 'Vapor sobrecal.'}


class FueraDeRango(Exception):
    pass


class NoResoluble(Exception):
    pass


# --------------------------------------------------------------- utilidades
def _bracket(xs, x):
    """Indice i tal que xs[i] <= x <= xs[i+1]. Error si x sale del rango."""
    if x < xs[0] - 1e-12 or x > xs[-1] + 1e-12:
        raise FueraDeRango('valor %g fuera del rango tabulado [%g, %g]'
                           % (x, xs[0], xs[-1]))
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    return lo


def _lin(x, x0, x1, y0, y1):
    if x1 == x0:
        return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def _interp_rows(rows, key, x, keys):
    """Interpola linealmente todas las columnas 'keys' frente a rows[key]."""
    xs = [r[key] for r in rows]
    i = _bracket(xs, x)
    a, b = rows[i], rows[i + 1]
    out = {}
    for k in keys:
        out[k] = _lin(x, a[key], b[key], a[k], b[k])
    out[key] = x
    return out


SAT_KEYS = ['vl', 'vv', 'ul', 'uv', 'hl', 'hv', 'sl', 'sv']


# --------------------------------------------------------- curva de saturacion
def sat_at_T(sub, T):
    """Estado de saturacion a temperatura T (tabla indexada por T)."""
    rows = sub['sat_by_T']
    if not rows:
        raise NoResoluble('%s no tiene tabla de saturacion por T' % sub['name'])
    r = _interp_rows(rows, 'T', T, SAT_KEYS + ['Pl', 'Pv'])
    r['P'] = r['Pv']          # presion de rocio: la que fija el vapor saturado
    return r


def sat_at_P(sub, P):
    """Estado de saturacion a presion P (tabla indexada por P).

    Se usa esta tabla, y no la de T, siempre que el dato sea P: reconstruir
    T_sat(P) interpolando la tabla por T introduce un error de hasta 0,3 C
    en agua porque P_sat(T) es exponencial (ver informe de validacion).
    """
    rows = sub['sat_by_P']
    if not rows:
        raise NoResoluble('%s no tiene tabla de saturacion por P' % sub['name'])
    r = _interp_rows(rows, 'P', P, SAT_KEYS + ['Tl', 'Tv'])
    r['T'] = r['Tv']
    return r


# ------------------------------------------------------------------ isobaras
def branches(b):
    """Parte una isobara en (rama liquida, rama vapor).

    El corte se detecta por el SALTO de volumen especifico, no por una T
    repetida: en sustancias puras las dos filas de saturacion tienen la misma
    T, pero en mezclas zeotropicas hay deslizamiento (en R-404A a 0,14 MPa la
    burbuja esta a -39,24 C y el rocio a -38,53 C) y las T son distintas.
    """
    if '_br' in b:
        return b['_br']
    rows = b['rows']
    best, bi = 1.0, None
    for i in range(len(rows) - 1):
        v0, v1 = rows[i]['v'], rows[i + 1]['v']
        if v0 and v1 and v1 / v0 > best:
            best, bi = v1 / v0, i
    if bi is None or best < 5.0:
        b['_br'] = (rows, []) if rows[0]['v'] < 0.01 else ([], rows)
    else:
        b['_br'] = (rows[:bi + 1], rows[bi + 1:])
    return b['_br']


def iso_at_T(b, T, phase):
    """Interpola dentro de una isobara, en la rama de la fase pedida."""
    liq, vap = branches(b)
    rows = liq if phase == LIQUID else vap
    if len(rows) < 2:
        raise FueraDeRango('la isobara %g MPa no tiene rama %s tabulada'
                           % (b['P'], phase))
    return _interp_rows(rows, 'T', T, PROPS)


def bracket_isobars(sub, P):
    """Isobaras que encierran P. Si P coincide con una tabulada, devuelve una."""
    bs = sub['isobars']
    if not bs:
        raise NoResoluble('%s no tiene tablas de isobaras' % sub['name'])
    Ps = [b['P'] for b in bs]
    for i, p in enumerate(Ps):
        if abs(p - P) < 1e-12:
            return [bs[i]]
    i = _bracket(Ps, P)
    return [bs[i], bs[i + 1]]


def single_phase_at_PT(sub, P, T, phase, avisos):
    """Doble interpolacion: primero en T dentro de cada isobara, luego en P.

    Ese orden es el que se sigue a mano en clase, y se respeta para que el
    resultado coincida con la solucion oficial.

    Problema real de esta rejilla: a la temperatura T, una de las dos isobaras
    vecinas puede estar en la OTRA fase (a P1 < P la saturacion ocurre antes,
    asi que un liquido comprimido a P puede ser vapor a P1). Interpolar entre
    un liquido y un vapor daria un numero sin sentido. Cuando pasa, se
    sustituye esa isobara vecina por el propio estado de saturacion a T, que
    es la frontera fisica correcta, y se avisa en pantalla.
    """
    bs = bracket_isobars(sub, P)
    if len(bs) == 1:
        return iso_at_T(bs[0], T, phase)

    pts = []
    for b in bs:
        try:
            r = iso_at_T(b, T, phase)
            pts.append((b['P'], r))
        except FueraDeRango:
            pts.append((b['P'], None))

    if all(r is not None for _, r in pts):
        (p0, r0), (p1, r1) = pts
        return dict((k, _lin(P, p0, p1, r0[k], r1[k])) for k in PROPS)

    # Una vecina no tiene la fase pedida a esa T: se usa la frontera de
    # saturacion a esa misma T como punto de apoyo.
    sat = sat_at_T(sub, T)
    tag = 'l' if phase == LIQUID else 'v'
    bnd = (sat['P'], dict((k, sat[k + tag]) for k in PROPS))
    avisos.append('vecina en otra fase: se usa la saturacion a T')
    known = [(p, r) for p, r in pts if r is not None]
    if not known:
        raise FueraDeRango('ninguna isobara vecina tiene la fase pedida a T=%g' % T)
    (p0, r0) = known[0]
    (p1, r1) = bnd
    if abs(p1 - p0) < 1e-12:
        return r0
    return dict((k, _lin(P, p0, p1, r0[k], r1[k])) for k in PROPS)


# ------------------------------------------------------------------- estados
def _state(sub, **kw):
    st = {'sustancia': sub['name'], 'T_unit': sub['T_unit'],
          'T': None, 'P': None, 'v': None, 'u': None, 'h': None, 's': None,
          'x': None, 'region': None, 'avisos': []}
    st.update(kw)
    return st


def _fill_mix(st, sat, x, Tkey='T'):
    for k in PROPS:
        st[k] = sat[k + 'l'] + x * (sat[k + 'v'] - sat[k + 'l'])
    st['x'] = x
    st['region'] = MIX
    return st


# ---- (P, T) ---------------------------------------------------------------
def state_PT(sub, P, T):
    """Par (P,T). Ambiguo justo en saturacion: ahi hace falta ademas x."""
    st = _state(sub, P=P, T=T)
    sat = sat_at_P(sub, P)
    Tb, Td = sat['Tl'], sat['Tv']          # burbuja y rocio (iguales si es pura)
    if T < Tb - 1e-9:
        st['region'] = LIQUID
        st['x'] = 0.0 if False else None
    elif T > Td + 1e-9:
        st['region'] = VAPOR
    else:
        st['region'] = MIX
        st['avisos'].append('(P,T) en saturacion: x indeterminado, se supone x=0')
        return _fill_mix(st, sat, 0.0)
    r = single_phase_at_PT(sub, P, T, st['region'], st['avisos'])
    for k in PROPS:
        st[k] = r[k]
    return st


# ---- (P, x) y (T, x) -------------------------------------------------------
def state_Px(sub, P, x):
    if not (0.0 <= x <= 1.0):
        raise FueraDeRango('el titulo debe estar entre 0 y 1 (x=%g)' % x)
    sat = sat_at_P(sub, P)
    st = _state(sub, P=P, T=sat['Tl'] + x * (sat['Tv'] - sat['Tl']))
    if sub['blend']:
        st['avisos'].append('mezcla: T de burbuja %.2f, de rocio %.2f'
                            % (sat['Tl'], sat['Tv']))
    return _fill_mix(st, sat, x)


def state_Tx(sub, T, x):
    if not (0.0 <= x <= 1.0):
        raise FueraDeRango('el titulo debe estar entre 0 y 1 (x=%g)' % x)
    sat = sat_at_T(sub, T)
    st = _state(sub, T=T, P=sat['Pl'] + x * (sat['Pv'] - sat['Pl']))
    return _fill_mix(st, sat, x)


# ---- (P, y) con y en {v,u,h,s} --------------------------------------------
def state_Py(sub, P, prop, y):
    """Par (P, propiedad). Es el caso mas frecuente en examen.

    Enrutado: se compara y con y_f(P) e y_g(P) de la tabla de saturacion.
      y < y_f            -> liquido comprimido -> inversa dentro de la isobara
      y_f <= y <= y_g    -> bifasico -> x = (y - y_f)/(y_g - y_f), directo
      y > y_g            -> vapor sobrecalentado -> inversa dentro de la isobara
    """
    sat = sat_at_P(sub, P)
    yf, yg = sat[prop + 'l'], sat[prop + 'v']
    st = _state(sub, P=P)
    if yf <= y <= yg:
        x = (y - yf) / (yg - yf) if yg != yf else 0.0
        st['T'] = sat['Tl'] + x * (sat['Tv'] - sat['Tl'])
        return _fill_mix(st, sat, x)
    st['region'] = LIQUID if y < yf else VAPOR
    T = invert_in_P(sub, P, prop, y, st['region'], st['avisos'])
    st['T'] = T
    r = single_phase_at_PT(sub, P, T, st['region'], st['avisos'])
    for k in PROPS:
        st[k] = r[k]
    st[prop] = y                        # se respeta el dato de entrada
    return st


def invert_in_P(sub, P, prop, y, phase, avisos):
    """Busqueda inversa: dado (P, y) halla T en la region monofasica.

    Se resuelve sobre la MISMA funcion que usa el calculo directo, para que
    ida y vuelta sean consistentes: se construye y(T) por doble interpolacion
    y se invierte por biseccion sobre el intervalo tabulado. La monotonia de
    h y s con T a P constante (verificada en validate.py) garantiza que la
    solucion es unica.
    """
    bs = bracket_isobars(sub, P)
    lo_c, hi_c = [], []
    for b in bs:
        liq, vap = branches(b)
        rows = liq if phase == LIQUID else vap
        if len(rows) >= 2:
            lo_c.append(rows[0]['T'])
            hi_c.append(rows[-1]['T'])
    if not lo_c:
        raise FueraDeRango('sin datos de la fase %s a P=%g' % (phase, P))
    lo, hi = max(lo_c), min(hi_c)

    def f(T):
        return single_phase_at_PT(sub, P, T, phase, [])[prop] - y

    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        raise FueraDeRango('%s=%g fuera del rango tabulado a P=%g MPa '
                           '(de %g a %g)' % (prop, y, P, y + flo, y + fhi))
    for _ in range(80):
        mid = (lo + hi) / 2.0
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
        if hi - lo < 1e-9:
            break
    return (lo + hi) / 2.0


# ---- (T, y) ---------------------------------------------------------------
def state_Ty(sub, T, prop, y):
    """Par (T, propiedad). Enrutado analogo, con la tabla indexada por T."""
    sat = sat_at_T(sub, T)
    yf, yg = sat[prop + 'l'], sat[prop + 'v']
    st = _state(sub, T=T)
    if yf <= y <= yg:
        x = (y - yf) / (yg - yf) if yg != yf else 0.0
        st['P'] = sat['Pl'] + x * (sat['Pv'] - sat['Pl'])
        return _fill_mix(st, sat, x)
    st['region'] = LIQUID if y < yf else VAPOR
    P = invert_in_T(sub, T, prop, y, st['region'], st['avisos'])
    st['P'] = P
    r = single_phase_at_PT(sub, P, T, st['region'], st['avisos'])
    for k in PROPS:
        st[k] = r[k]
    st[prop] = y
    return st


def invert_in_T(sub, T, prop, y, phase, avisos):
    """Dado (T, y) halla P. Se recorre la lista de isobaras que tienen esa
    fase a esa T y se busca el intervalo de P donde y cambia de lado."""
    cand = []
    for b in sub['isobars']:
        try:
            cand.append((b['P'], iso_at_T(b, T, phase)[prop]))
        except FueraDeRango:
            continue
    if len(cand) < 2:
        raise FueraDeRango('no hay isobaras con fase %s a T=%g' % (phase, T))
    for i in range(len(cand) - 1):
        (p0, y0), (p1, y1) = cand[i], cand[i + 1]
        if (y0 - y) * (y1 - y) <= 0:
            return _lin(y, y0, y1, p0, p1)
    raise FueraDeRango('%s=%g fuera del rango tabulado a T=%g' % (prop, y, T))


# ------------------------------------------------------------------ fachada
PAIRS = {
    'PT': lambda s, a, b: state_PT(s, a, b),
    'Px': lambda s, a, b: state_Px(s, a, b),
    'Tx': lambda s, a, b: state_Tx(s, a, b),
    'Pv': lambda s, a, b: state_Py(s, a, 'v', b),
    'Pu': lambda s, a, b: state_Py(s, a, 'u', b),
    'Ph': lambda s, a, b: state_Py(s, a, 'h', b),
    'Ps': lambda s, a, b: state_Py(s, a, 's', b),
    'Tv': lambda s, a, b: state_Ty(s, a, 'v', b),
    'Tu': lambda s, a, b: state_Ty(s, a, 'u', b),
    'Th': lambda s, a, b: state_Ty(s, a, 'h', b),
    'Ts': lambda s, a, b: state_Ty(s, a, 's', b),
}


def solve(sub, pair, a, b):
    if pair not in PAIRS:
        raise NoResoluble('par no soportado: %s' % pair)
    return PAIRS[pair](sub, a, b)


def fmt(st):
    u = st['T_unit']
    p = lambda k, n: ('%.*f' % (n, st[k])) if st[k] is not None else '-'
    return ('%-14s T=%s %s  P=%s MPa  v=%s  u=%s  h=%s  s=%s  x=%s  [%s]%s'
            % (st['sustancia'], p('T', 2), u, p('P', 5), p('v', 6), p('u', 2),
               p('h', 2), p('s', 4),
               ('%.4f' % st['x']) if st['x'] is not None else '-',
               REGION_ES.get(st['region'], '?'),
               ('  !' + '; '.join(st['avisos'])) if st['avisos'] else ''))


_CACHE = {}


def substances():
    if not _CACHE:
        for s in load():
            _CACHE[s['key']] = s
    return _CACHE


def get(key):
    subs = substances()
    if key in subs:
        return subs[key]
    raise NoResoluble('sustancia desconocida: %s (hay %s)'
                      % (key, ', '.join(sorted(subs))))
