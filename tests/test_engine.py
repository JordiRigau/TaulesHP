# -*- coding: utf-8 -*-
"""Bateria de pruebas del motor.

Los valores esperados NO salen de reimplementar el algoritmo, porque eso solo
detectaria errores de transcripcion y no de concepto. Vienen de tres fuentes
independientes:

  A. Puntos EXACTAMENTE tabulados en el PDF. Interpolar sobre un nodo debe
     devolver el propio nodo; si no, el enrutado o el bracketing estan mal.
  B. Valores de tablas de vapor publicadas (Cengel / NIST), ajenos por
     completo a este proyecto.
  C. Comportamiento exigido en los limites: x=0, x=1, fuera de rango,
     vecina en otra fase.
"""
from __future__ import unicode_literals
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))

import engine as E
from engine import FueraDeRango

PASS, FAIL = [], []


def check(name, got, exp, tol):
    ok = got is not None and abs(got - exp) <= tol
    (PASS if ok else FAIL).append(
        '%-58s got=%s exp=%s tol=%g' % (name, got, exp, tol))
    return ok


def check_raises(name, fn):
    try:
        fn()
    except (FueraDeRango, E.NoResoluble):
        PASS.append('%-58s lanza error como debe' % name)
        return True
    FAIL.append('%-58s NO lanzo error estando fuera de rango' % name)
    return False


# =========================================================== A. nodos exactos
def test_exact_saturation():
    """En un punto tabulado de saturacion, x=0 y x=1 deben dar h_f y h_g."""
    for key in ('AIGUA', 'AMONIAC', 'R134A'):
        sub = E.get(key)
        for r in sub['sat_by_P'][5:40:11]:
            P = r['P']
            st0 = E.state_Px(sub, P, 0.0)
            st1 = E.state_Px(sub, P, 1.0)
            for p in ('v', 'u', 'h', 's'):
                check('%s P=%g x=0 %s' % (key, P, p), st0[p], r[p + 'l'],
                      abs(r[p + 'l']) * 1e-9 + 1e-9)
                check('%s P=%g x=1 %s' % (key, P, p), st1[p], r[p + 'v'],
                      abs(r[p + 'v']) * 1e-9 + 1e-9)


def test_exact_superheated():
    """(P,T) sobre un nodo tabulado de una isobara debe devolver la fila."""
    sub = E.get('AIGUA')
    for b in sub['isobars'][:12:3]:
        liq, vap = E.branches(b)
        for r in vap[2:20:6]:
            st = E.state_PT(sub, b['P'], r['T'])
            for p in ('v', 'u', 'h', 's'):
                check('AIGUA P=%g T=%g %s' % (b['P'], r['T'], p), st[p], r[p],
                      abs(r[p]) * 1e-9 + 1e-9)


def test_exact_compressed_liquid():
    """El PDF SI trae liquido subenfriado (las isobaras empiezan en liquido),
    asi que no hace falta aproximar por liquido saturado."""
    sub = E.get('AIGUA')
    for b in sub['isobars'][:16:5]:
        liq, vap = E.branches(b)
        if len(liq) < 3:
            continue
        r = liq[1]
        st = E.state_PT(sub, b['P'], r['T'])
        check('AIGUA liq P=%g T=%g h' % (b['P'], r['T']), st['h'], r['h'],
              abs(r['h']) * 1e-9 + 1e-9)
        ok = st['region'] == E.LIQUID
        (PASS if ok else FAIL).append(
            '%-58s region=%s' % ('AIGUA liq P=%g T=%g region' % (b['P'], r['T']),
                                 st['region']))


def test_inverse_returns_node():
    """Inversa: partiendo de un (P,h) tabulado hay que recuperar su T."""
    sub = E.get('AIGUA')
    for b in sub['isobars'][:12:3]:
        liq, vap = E.branches(b)
        for r in vap[3:18:6]:
            st = E.state_Py(sub, b['P'], 'h', r['h'])
            check('inv AIGUA P=%g h=%g -> T' % (b['P'], r['h']), st['T'],
                  r['T'], 1e-4)
            st = E.state_Py(sub, b['P'], 's', r['s'])
            check('inv AIGUA P=%g s=%g -> T' % (b['P'], r['s']), st['T'],
                  r['T'], 1e-3)


# ================================================== B. referencia externa
# Tablas de vapor publicadas (Cengel, "Termodinamica", tablas A-4/A-5/A-6).
# Independientes de este PDF: sirven para detectar un fallo de extraccion o
# de enrutado que fuera coherente consigo mismo pero equivocado.
EXTERNAL = [
    # (sustancia, par, a, b, propiedad, valor esperado, tolerancia)
    ('AIGUA', 'Px', 0.1, 0.0, 'T', 99.61, 0.05),      # T_sat a 100 kPa
    ('AIGUA', 'Px', 0.1, 0.0, 'h', 417.51, 0.30),     # h_f
    ('AIGUA', 'Px', 0.1, 1.0, 'h', 2675.0, 1.0),      # h_g
    ('AIGUA', 'Px', 0.1, 1.0, 's', 7.3589, 0.005),    # s_g
    ('AIGUA', 'Tx', 100.0, 1.0, 'P', 0.10142, 0.0015),  # P_sat a 100 C
    ('AIGUA', 'PT', 0.1, 200.0, 'v', 2.1723, 0.002),  # vapor sobrecalentado
    ('AIGUA', 'PT', 0.1, 200.0, 'h', 2875.5, 0.5),
    ('AIGUA', 'PT', 1.0, 300.0, 'h', 3051.6, 1.5),
    ('AIGUA', 'PT', 10.0, 500.0, 'h', 3375.1, 2.0),
    ('AMONIAC', 'Px', 0.2, 1.0, 'T', -18.86, 0.15),   # T_sat NH3 a 200 kPa
    ('R134A', 'Px', 0.2, 1.0, 'T', -10.09, 0.20),     # T_sat R-134a a 200 kPa
]


def test_external_reference():
    for key, pair, a, b, prop, exp, tol in EXTERNAL:
        sub = E.get(key)
        st = E.solve(sub, pair, a, b)
        check('EXT %s %s(%g,%g) %s' % (key, pair, a, b, prop), st[prop], exp, tol)


# ==================================================== C. limites y errores
def test_two_phase_lever_rule():
    """Zona bifasica: y = y_f + x (y_g - y_f), y la inversa devuelve la x."""
    sub = E.get('AIGUA')
    P = 1.0
    for x in (0.0, 0.25, 0.5, 0.85, 1.0):
        st = E.state_Px(sub, P, x)
        back = E.state_Py(sub, P, 'h', st['h'])
        check('AIGUA P=1 x=%.2f -> h -> x' % x, back['x'], x, 1e-6)
        ok = back['region'] == E.MIX
        (PASS if ok else FAIL).append(
            '%-58s region=%s' % ('AIGUA P=1 x=%.2f region' % x, back['region']))


def test_region_routing():
    """Cada par debe caer en la region correcta."""
    sub = E.get('AIGUA')
    cases = [
        (('Ph', 1.0, 500.0), E.LIQUID),    # h < h_f(1 MPa)=762.5
        (('Ph', 1.0, 2000.0), E.MIX),      # entre h_f y h_g
        (('Ph', 1.0, 3000.0), E.VAPOR),    # h > h_g=2777.1
        (('PT', 1.0, 100.0), E.LIQUID),    # T < T_sat=179.9
        (('PT', 1.0, 400.0), E.VAPOR),
    ]
    for (pair, a, b), exp in cases:
        st = E.solve(sub, pair, a, b)
        ok = st['region'] == exp
        (PASS if ok else FAIL).append(
            '%-58s region=%s esperada=%s'
            % ('routing %s(%g,%g)' % (pair, a, b), st['region'], exp))


def test_out_of_range():
    sub = E.get('AIGUA')
    check_raises('T=2000 C fuera de rango',
                 lambda: E.state_PT(sub, 1.0, 2000.0))
    check_raises('P=500 MPa fuera de rango',
                 lambda: E.state_PT(sub, 500.0, 300.0))
    check_raises('h=99999 fuera de rango',
                 lambda: E.state_Py(sub, 1.0, 'h', 99999.0))
    check_raises('x=1.4 invalido',
                 lambda: E.state_Px(sub, 1.0, 1.4))


def test_neighbour_other_phase():
    """P entre dos isobaras y T tal que una vecina esta en la otra fase.

    A 0,15 MPa la saturacion esta en 111,35 C, asi que 115 C es vapor
    sobrecalentado. Pero la isobara vecina de arriba (0,20 MPa) satura a
    120,21 C: a esa misma T su tabla da LIQUIDO. Interpolar entre ambas
    mezclaria fases. La app debe apoyarse en la saturacion y avisar.
    """
    sub = E.get('AIGUA')
    st = E.state_PT(sub, 0.15, 115.0)
    ok = st['region'] == E.VAPOR and st['avisos']
    (PASS if ok else FAIL).append(
        '%-58s region=%s avisos=%s'
        % ('vecina en otra fase (0,15 MPa 115 C)', st['region'], st['avisos']))
    # el resultado debe quedar entre el vapor saturado y la isobara de 0,1 MPa
    sat = E.sat_at_T(sub, 115.0)
    ok2 = st['v'] is not None and 0.5 * sat['vv'] < st['v'] < 2.0 * sat['vv']
    (PASS if ok2 else FAIL).append(
        '%-58s v=%s vg=%s' % ('vecina en otra fase: v razonable',
                              st['v'], sat['vv']))


def main():
    for fn in (test_exact_saturation, test_exact_superheated,
               test_exact_compressed_liquid, test_inverse_returns_node,
               test_external_reference, test_two_phase_lever_rule,
               test_region_routing, test_out_of_range,
               test_neighbour_other_phase):
        try:
            fn()
        except Exception as e:
            FAIL.append('%-58s EXCEPCION %s: %s' % (fn.__name__,
                                                    type(e).__name__, e))
    print('PASS: %d' % len(PASS))
    print('FAIL: %d' % len(FAIL))
    for f in FAIL:
        print('  FAIL ' + f)
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
