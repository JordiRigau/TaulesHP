# -*- coding: utf-8 -*-
"""Prueba de aceptacion: problemas de la asignatura con su solucion oficial.

Es la prueba que de verdad decide. Los otros dos arneses comprueban que la app
es coherente con el PDF de tablas y con tablas de vapor publicadas; este
comprueba que **reproduce lo que da por bueno el profesor**, que no es lo
mismo.

Fuente: "Termodinamica. Tests i problemes" (ETSEIB-UPC, marzo 2025),
Tema 1 "Propietats de les substancies pures". Los enunciados marcados
"Taules individualitzades" usan exactamente las tablas de este proyecto.

Encontro dos fallos reales del motor:

  1. Por encima de la presion critica no hay curva de saturacion, y la
     determinacion de region se caia. Afectaba a 30 isobaras de 6 sustancias,
     14 de ellas del agua (25 a 100 MPa).
  2. v se interpolaba linealmente en P. En un gas v ~ ZRT/P, casi
     hiperbolica: entre isobaras muy separadas la recta se aleja mucho.
     Con el amoniaco a 2,5 MPa (el PDF salta de 1,8 a 3,0) daba 8 % de error.
"""
from __future__ import unicode_literals
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))

import engine as E

PASS, FAIL = [], []


def check(ref, texto, calc, oficial, unidad, tol_rel):
    """tol_rel en %, sobre el valor oficial."""
    d = abs(calc - oficial)
    rel = 100.0 * d / abs(oficial) if oficial else d
    ok = rel <= tol_rel
    (PASS if ok else FAIL).append(
        '%-6s %-44s %12.5f vs %11.5f %-5s  %6.3f%%'
        % (ref, texto, calc, oficial, unidad, rel))
    return ok


# --------------------------------------------------------------------------
def p1_diposit_rigid():
    """P1. Recipiente de 1 m3 con agua a 5 bar.

    R/ 1) 151,8 C, liquido 616,1 kg (0,6734 m3) y vapor 0,872 kg (0,3267 m3)
       2) liquida, 81,9 C   3) vapor, 1,16 MPa   4) liquida, 827,8 kg
    """
    w = E.get('AIGUA')

    st = E.state_Py(w, 0.5, 'v', 1 / 617.0)
    sat = E.sat_at_P(w, 0.5)
    check('1.1', 'T del recipient amb 617 kg', st['T'], 151.8, 'C', 0.1)
    mv = st['x'] * 617
    check('1.1', 'massa de liquid', 617 - mv, 616.1, 'kg', 0.1)
    check('1.1', 'massa de vapor', mv, 0.872, 'kg', 1.0)
    check('1.1', 'volum de liquid', (617 - mv) * sat['vl'], 0.6734, 'm3', 0.5)
    check('1.1', 'volum de vapor', mv * sat['vv'], 0.3267, 'm3', 1.0)

    # 970 kg: liquido comprimido. La T es muy sensible al redondeo del PDF
    # (v con 6 decimales y dv/dT = 6,8e-7 -> +-0,7 C por medio digito), asi
    # que 82,25 y 81,9 son el mismo punto para estas tablas.
    st = E.state_Py(w, 0.5, 'v', 1 / 970.0)
    check('1.2', 'T del recipient amb 970 kg', st['T'], 81.9, 'C', 1.0)
    (PASS if st['region'] == E.LIQUID else FAIL).append(
        '%-6s %-44s regio=%s' % ('1.2', 'ha de sortir liquid comprimit',
                                 st['region']))

    st = E.state_Ty(w, 250.0, 'v', 1 / 5.0)
    check('1.3', 'P amb 5 kg a 250 C', st['P'], 1.16, 'MPa', 1.0)

    st = E.state_PT(w, 4.0, 230.0)
    check('1.4', 'massa a 230 C i 40 bar', 1 / st['v'], 827.8, 'kg', 0.2)


def p14_meta():
    """P14. Masa de metano en 20 L sin pasar de 50 bar a 50 C.
    R/ taules individualitzades: 636 g   -- ES SUPERCRITICO (Pc = 4,599 MPa)
    """
    m = E.get('META')
    st = E.state_PT(m, 5.0, 323.15)
    check('14', 'massa de meta en 20 L', 0.020 / st['v'] * 1000, 636, 'g', 1.0)
    (PASS if st['region'] == E.SUPER else FAIL).append(
        '%-6s %-44s regio=%s' % ('14', 'per sobre de Pc: supercritic',
                                 st['region']))


def p15_propa():
    """P15. Bombona de 15 L con 1 kg de propano.
    R/ taula de prop.: 33,2 bar a 380 K ; 480 K al arribar a 50 bar
       -- 380 K esta por encima de Tc = 369,89 K
    """
    p = E.get('PROPA')
    st = E.state_Ty(p, 380.0, 'v', 0.015)
    check('15a', 'P del propa a 380 K', st['P'] * 10, 33.2, 'bar', 1.5)
    st = E.state_Py(p, 5.0, 'v', 0.015)
    check('15b', 'T del propa en arribar a 50 bar', st['T'], 480, 'K', 1.0)


def p17_amoniac():
    """P17. Volumen de 1 mol de amoniaco a 25 bar y 340 K.
    R/ 3) les taules: 0,9202 dm3

    Este es el que destapo lo de interpolar v en 1/P: el PDF salta de 1,8 a
    3,0 MPa y la recta daba 0,9952 (8 % de error).
    """
    a = E.get('AMONIAC')
    st = E.state_PT(a, 2.5, 340.0 - 273.15)
    check('17', 'volum d1 mol damoniac',
          st['v'] * 17.03e-3 * 1000, 0.9202, 'dm3', 1.0)


def p22_eta():
    """P22. Volumen de 2,5 mol de etano a 3,0 MPa y 310 K.
    R/ 3) les taules de l'eta: 1,640 dm3
    """
    e = E.get('ETA')
    st = E.state_PT(e, 3.0, 310.0)
    check('22', 'volum de 2,5 mol d\'eta',
          st['v'] * 2.5 * 30.07e-3 * 1000, 1.640, 'dm3', 0.5)


def main():
    for fn in (p1_diposit_rigid, p14_meta, p15_propa, p17_amoniac, p22_eta):
        try:
            fn()
        except Exception as e:
            FAIL.append('%-6s EXCEPCION %s: %s' % (fn.__name__,
                                                   type(e).__name__, e))
    print('%-6s %-44s %12s vs %11s %-5s  %7s'
          % ('ref', 'magnitud', 'calculat', 'oficial', 'unit', 'desv.'))
    print('-' * 96)
    for l in PASS:
        print('  ' + l)
    for l in FAIL:
        print('  FALLA ' + l)
    print('-' * 96)
    print('PASS: %d    FAIL: %d' % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
