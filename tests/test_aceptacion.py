# -*- coding: utf-8 -*-
"""Prueba de aceptacion: problemas de la asignatura con su solucion oficial.

Es la prueba que de verdad decide. Los otros dos arneses comprueban que la app
es coherente con el PDF de tablas y con tablas de vapor publicadas; este
comprueba que **reproduce lo que da por bueno el profesor**, que no es lo
mismo.

Fuentes:

  - "Termodinamica. Tests i problemes" (ETSEIB-UPC, marzo 2025), Tema 1
    "Propietats de les substancies pures". Los enunciados marcados "Taules
    individualitzades" usan exactamente las tablas de este proyecto.
  - Dos ciclos completos con solucion oficial. Las soluciones estan
    resueltas con EES, que usa propiedades de fluido real: la desviacion que
    sale es el error de las tablas mas el de la interpolacion, que es lo que
    se quiere medir.

Encontro dos fallos reales del motor. Los dos hacian que la app diera ERROR
en vez de un numero; ninguno daba un resultado equivocado:

  1. Por encima de la presion critica no hay curva de saturacion, y la
     determinacion de region se caia. Afectaba a 30 isobaras de 6 sustancias,
     14 de ellas del agua (25 a 100 MPa).
  2. La isobara se partia en rama liquida y rama vapor por el salto de v, con
     umbral x5. Cerca del punto critico v_f y v_g convergen y el salto no
     llega: 10 isobaras quedaban sin rama vapor, entre ellas las del agua a
     17,5 y 20 MPa. Lo destapo el ciclo Rankine de aqui abajo, que se caia.

Y dejo documentada una limitacion que NO se ha corregido a proposito: donde el
PDF pega un salto grande de presion, interpolar v linealmente (que es lo que
se hace a mano) se separa del valor real. Ver p17_amoniac.
"""
from __future__ import unicode_literals
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))

import engine as E

PASS, FAIL = [], []


NOTAS = []


def nota(ref, texto):
    NOTAS.append('%-6s %s' % (ref, texto))


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

    LIMITACION CONOCIDA, y es deliberada.

    La tabla del amoniaco salta de 1,8 a 3,0 MPa. A 66,85 C da v = 1,3742 y
    0,7244 dm3/mol, y la recta entre las dos, evaluada en 2,5 MPa, vale
    0,9952. Eso es lo que sale a mano y es lo que da la app.

    La solucion oficial es 0,9202, un 8 % menos, y NO se puede obtener
    interpolando linealmente: v ~ ZRT/P es casi hiperbolica, y con un salto
    de 1,8 a 3,0 la recta se queda lejos. En 1/P saldria 0,9193.

    Se ha elegido reproducir el metodo del examen y no corregirlo, porque el
    numero que da la app tiene que ser el que el alumno puede justificar en el
    papel. Asi que aqui se comprueba justo eso: que la app da EXACTAMENTE la
    interpolacion a mano, y la desviacion contra el oficial queda anotada.

    Solo pasa donde el PDF tiene huecos grandes: 35 de 214 pares de isobaras.
    """
    a = E.get('AMONIAC')
    T = 340.0 - 273.15

    # interpolacion a mano, calculada aparte a proposito
    b18 = [b for b in a['isobars'] if abs(b['P'] - 1.8) < 1e-9][0]
    b30 = [b for b in a['isobars'] if abs(b['P'] - 3.0) < 1e-9][0]
    v18 = E._interp_rows(E.branches(b18)[1], 'T', T, ['v'])['v']
    v30 = E._interp_rows(E.branches(b30)[1], 'T', T, ['v'])['v']
    a_ma = E._lin(2.5, 1.8, 3.0, v18, v30) * 17.03e-3 * 1000

    st = E.state_PT(a, 2.5, T)
    app = st['v'] * 17.03e-3 * 1000
    check('17', 'la app ha de donar el que surt a ma', app, a_ma, 'dm3', 0.001)
    nota('17', 'volum d1 mol damoniac a 2,5 MPa: la app i el llapis donen '
               '%.4f dm3' % app)
    nota('17', '  la solucio oficial es 0,9202 (%.1f %% menys). El PDF salta '
               'd1,8 a 3,0 MPa' % (100 * (app - 0.9202) / 0.9202))
    nota('17', '  i entre isobares tan separades la recta no hi arriba. '
               'Es la limitacio del metode,')
    nota('17', '  no de la app: a ma surt exactament el mateix.')


def p22_eta():
    """P22. Volumen de 2,5 mol de etano a 3,0 MPa y 310 K.
    R/ 3) les taules de l'eta: 1,640 dm3
    """
    e = E.get('ETA')
    st = E.state_PT(e, 3.0, 310.0)
    check('22', 'volum de 2,5 mol d\'eta',
          st['v'] * 2.5 * 30.07e-3 * 1000, 1.640, 'dm3', 0.5)


# --------------------------------------------------------------------------
def rankine_reescalfament():
    """Cicle de vapor amb dues turbines, reescalfament, regeneracio i calor
    de proces.

    20 kg/s d'aigua, 17,5 MPa i 600 C a l'entrada de cada turbina, extraccions
    a 4 i 1 MPa, condensador a 0,1 MPa.

    Es la prueba mas exigente del proyecto: encadena 11 consultas a las tablas
    (liquido comprimido, vapor sobrecalentado, dos expansiones isentropicas,
    tres liquidos saturados y un titulo por entalpia) y los errores se
    arrastran de una a otra. Ademas h[1] es a 17,5 MPa, la isobara que estaba
    mal partida: sin el arreglo de branches() esto ni siquiera corria.
    """
    w = E.get('AIGUA')
    mF = 20.0
    hPT = lambda P, T: E.state_PT(w, P, T)['h']
    hPs = lambda P, sv: E.state_Py(w, P, 's', sv)['h']
    hf = lambda P: E.sat_at_P(w, P)['hl']

    h1 = hPT(17.5, 150.0)
    h2 = hPT(17.5, 600.0)
    s2 = E.state_PT(w, 17.5, 600.0)['s']
    h3, h7 = hPs(4.0, s2), hPs(2.0, s2)
    h8 = hPT(2.0, 600.0)
    s8 = E.state_PT(w, 2.0, 600.0)['s']
    h9, h10 = hPs(1.0, s8), hPs(0.1, s8)
    h11 = hf(0.1)
    h4, h13, h12 = hf(4.0), hf(1.0), h11

    Q_h1 = mF * (h2 - h1) / 1000.0
    W_t1 = 0.21 * Q_h1
    y1 = 1.0 - (W_t1 * 1000.0 - mF * (h2 - h3)) / (mF * (h3 - h7))
    y2 = (h1 - y1 * h4 - (1 - y1) * h12) / ((1 - y1) * (h9 - h12))
    h6 = (h13 - (1 - y1) * y2 * h9 - (1 - y1) * (1 - y2) * h12) / y1
    Q_p = mF * y1 * (h3 - h4) / 1000.0
    Q_h2 = mF * (1 - y1) * (h8 - h7) / 1000.0
    W_t2 = (mF * (1 - y1) * (h8 - h9)
            + mF * (1 - y1) * (1 - y2) * (h9 - h10)) / 1000.0

    check('R2.1', 'fraccio extreta a la turbina alta', y1, 0.1359, '', 2.0)
    check('R2.2', 'fraccio extreta a la turbina baixa', y2, 0.05153, '', 2.0)
    check('R2.3', 'titol a l estat 6',
          E.state_Py(w, 1.0, 'h', h6)['x'], 0.5983, '', 2.0)
    check('R2.4', 'T de sortida de l oli termic',
          20.0 + Q_p * 1e6 / (30.0 * 2000.0), 111.0, 'C', 2.0)
    check('R2.5', 'calor de la caldera, 1a etapa', Q_h1, 58.37, 'MW', 0.5)
    check('R2.5', 'calor del reescalfament', Q_h2, 13.23, 'MW', 0.5)
    check('R2.5', 'potencia de la turbina alta', W_t1, 12.26, 'MW', 0.5)
    check('R2.5', 'potencia de la turbina baixa', W_t2, 14.58, 'MW', 0.5)
    check('R2.5', 'calor de proces', Q_p, 5.461, 'MW', 2.0)
    check('R2.5', 'rendiment termic',
          (W_t1 + W_t2) / (Q_h1 + Q_h2), 0.3748, '', 0.5)
    check('R2.5', 'rendiment global',
          (W_t1 + W_t2 + Q_p) / (Q_h1 + Q_h2), 0.4511, '', 0.5)
    check('R2.6', 'cabal de gas natural',
          (Q_h1 + Q_h2) * 1000.0 / 44000.0, 1.627, 'kg/s', 0.5)


# --------------------------------------------------------------------------
def branques_prop_del_critic():
    """Toda isobara subcritica de agua debe tener las dos ramas.

    Guarda directa del fallo de branches(): a 17,5 MPa el salto de v es solo
    x4,40 y a 20 MPa x2,88, por debajo del umbral x5 que habia.
    """
    w = E.get('AIGUA')
    sub = [b for b in w['isobars'] if b['P'] <= w['Pc_MPa']]
    sup = [b for b in w['isobars'] if b['P'] > w['Pc_MPa']]
    mal = [b['P'] for b in sub if not all(E.branches(b))]
    (PASS if not mal else FAIL).append(
        '%-6s %-44s %s' % ('br', 'les %d isobares subcritiques, dues rames'
                           % len(sub), 'falten a %s' % mal if mal else 'ok'))
    mal = [b['P'] for b in sup if E.branches(b)[1]]
    (PASS if not mal else FAIL).append(
        '%-6s %-44s %s' % ('br', 'les %d supercritiques, una sola rama'
                           % len(sup), 'partides %s' % mal if mal else 'ok'))

# --------------------------------------------------------------------------
def frigorific_doble_etapa():
    """Cicle frigorific de R-134a de dues etapes amb cambra de separacio,
    per a una fabrica de gel.

    Evaporador a 0,1 MPa, condensador a 1,4 MPa, 0,45 kg/s, compressor de
    baixa de 16 kW.

    Cubre rutas que el Rankine no toca: la inversa P(T,h) para encontrar la
    presion intermedia, un rendimiento isentropico (diferencia de dos
    entalpias parecidas, donde el error relativo se amplifica) y una mezcla
    por titulo. El PDF de tablas usa la referencia IIR, la misma que la
    solucion oficial, asi que las entalpias son directamente comparables.
    """
    r = E.get('R134A')
    mF, Wc1 = 0.45, 16.0
    T1sat = E.sat_at_P(r, 0.1)['T']
    T5sat = E.sat_at_P(r, 1.4)['T']
    st1 = E.state_PT(r, 0.1, T1sat + 6.36)
    h1, s1 = st1['h'], st1['s']
    h2 = h1 + Wc1 / mF
    P2 = E.state_Ty(r, 30.0, 'h', h2)['P']
    sat6 = E.sat_at_P(r, P2)
    h6l, h6v = sat6['hl'], sat6['hv']
    h5 = E.state_PT(r, 1.4, T5sat - 2.42)['h']
    x6 = (h5 - h6l) / (h6v - h6l)
    mc2 = x6 * mF / (1 - x6) + mF
    h2s = E.state_Py(r, P2, 's', s1)['h']
    h3 = x6 * h6v + (1 - x6) * h2
    h4 = E.state_Py(r, 1.4, 's', E.state_Py(r, P2, 'h', h3)['s'])['h']
    Wc2 = mc2 * (h4 - h3)
    QL = mF * (h1 - h6l)

    check('F1.1', 'T de saturacio a 0,1 MPa', T1sat, -26.37, 'C', 1.0)
    check('F1.1', 'T de saturacio a 1,4 MPa', T5sat, 52.4, 'C', 1.0)
    check('F1.1', 'P de la cambra de separacio', P2, 0.400, 'MPa', 1.0)
    check('F1.1', 'h de liquid saturat a P6', h6l, 212.2, 'kJ/kg', 0.5)
    check('F1.1', 'h de vapor saturat a P6', h6v, 403.8, 'kJ/kg', 0.5)
    check('F1.2', 'cabal pel compressor 2', mc2, 0.652, 'kg/s', 1.0)
    check('F1.3', 'h2s de la compressio isentropica', h2s, 416.8, 'kJ/kg', 0.5)
    check('F1.3', 'rendiment isentropic del compressor 1',
          (h2s - h1) / (h2 - h1) * 100, 82.07, '%', 1.5)
    check('F1.4', 'potencia frigorifica', QL, 78.94, 'kW', 0.5)
    check('F1.4', 'potencia del compressor 2', Wc2, 18.29, 'kW', 1.5)
    check('F1.4', 'COP de la installacio', QL / (Wc1 + Wc2), 2.302, '', 1.0)
    check('F1.4', 'calor cedit al condensador',
          mc2 * (h5 - h4), -113.2, 'kW', 0.5)
    check('F1.5', 'gel produit',
          -QL / (4.18 * -25 - 334 + 2 * -12) * 86.4, 14.75, 't/dia', 1.0)


def main():
    for fn in (p1_diposit_rigid, p14_meta, p15_propa, p17_amoniac,
               p22_eta, rankine_reescalfament, frigorific_doble_etapa,
               branques_prop_del_critic):
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
    if NOTAS:
        print('-' * 96)
        print('  LIMITACIONES ANOTADAS (no son fallos):')
        for l in NOTAS:
            print('  ' + l)
    print('-' * 96)
    print('PASS: %d    FAIL: %d' % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
