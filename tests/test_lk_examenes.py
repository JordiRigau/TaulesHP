# -*- coding: utf-8 -*-
"""Prueba de aceptacion de los metodos generalizados.

Las preguntas de "correlacions de Pitzer" y "funcions de discrepancia" de los
examenes de los ultimos catorce anos, con la respuesta que el profesor da por
buena. Es la prueba que decide si tools/lk.py puede sustituir a los tres
graficos generalizados de la Seccion C del libro de tablas.

**De donde sale la respuesta correcta.** Son examenes tipo test y el PDF de
solucion marca la opcion buena en NEGRITA. La negrita sobrevive a la
extraccion (pdfplumber da el nombre de la fuente por caracter), asi que la
clave se lee del PDF y no se teclea a mano.

**Que se mide.** El criterio real de un test es *acertar la opcion*, no
clavar el decimal: la solucion oficial se obtuvo leyendo tres graficos a ojo,
asi que tiene su propio error de lectura. Se comprueban las dos cosas:

  - OPCION: cual de las cinco letras selecciona el valor calculado;
  - DESV.:  cuanto se separa del numero que da el profesor.

Una desviacion del 5 % con la opcion correcta es un ACIERTO, y ademas dice
que el grafico se leyo con esa precision.

Tres preguntas nombran una sustancia y NO dan sus constantes criticas: hay
que buscarlas. Las del etileno salen de master.json, que es la misma fuente
que alimenta el desplegable de la app; las de H2S, NO y n-butano, de tabla
publicada, porque esas tres no estan en el PDF de la asignatura.

    python tests/test_lk_examenes.py
"""
from __future__ import unicode_literals
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))

import lk

R = lk.R
PASS, FAIL, NOTAS = [], [], []

# Constantes criticas que el enunciado NO da. Las de H2S, NO y n-butano salen
# de tabla publicada (Poling, "The Properties of Gases and Liquids", 5a ed.)
# porque esas tres sustancias no estan en el PDF de la asignatura.
H2S = (373.5, 8.94e6, 0.081, 34.08)     # Tc[K], Pc[Pa], w, M[g/mol]
NO = (180.0, 6.48e6, 0.583, 30.006)
BUTA = (425.3, 3.792e6, 0.199, 58.122)  # los da el examen de 06/04/2022


def de_taula(clau):
    """Constantes criticas de una sustancia del PDF, como las lee la app.

    El etileno SI esta tabulado, y las dos preguntas que lo nombran no dan sus
    constantes: hay que buscarlas. Se leen de master.json -- la misma fuente
    que alimenta el desplegable de la pantalla -- en vez de teclearlas aqui,
    para que la prueba recorra el mismo camino que el estudiante.
    """
    import engine as E
    sub = E.get(clau)
    return (sub['Tc_K'], sub['Pc_MPa'] * 1e6, sub['omega'] or 0.0,
            sub['molar_mass'])


ETILE = de_taula('ETILE')


def _tupla(x):
    return x if isinstance(x, tuple) else (x,)


def anota(ref, magnitud, calc, oficial, unidad, opciones, letra):
    """Compara con la solucion oficial y con la lista de opciones.

    calc y oficial pueden ser un numero o una TUPLA. Hace falta porque varias
    preguntas ofrecen las cinco opciones como pares -"c) 9520 kJ, -2100 kJ"
    frente a "e) 9520 kJ, -2272 kJ"- y con un solo numero la letra queda
    indeterminada: hay que mirar los dos a la vez para saber cual se elige.
    """
    calc, oficial = _tupla(calc), _tupla(oficial)
    mejor, dmin = None, None
    for lt, v in opciones:
        v = _tupla(v)
        # distancia relativa sumada: los dos numeros de un par suelen ir en
        # unidades distintas y una diferencia absoluta compararia peras
        d = sum(abs(c - x) / max(abs(x), 1e-9) for c, x in zip(calc, v))
        if dmin is None or d < dmin:
            mejor, dmin = lt, d
    desv = max(100.0 * abs(c - o) / abs(o) if o else abs(c)
               for c, o in zip(calc, oficial))
    txt = ', '.join('%.4g' % c for c in calc)
    ofi = ', '.join('%.4g' % o for o in oficial)
    linea = ('%-16s %-34s %14s vs %13s %-8s  %s  %5.1f%%'
             % (ref, magnitud, txt, ofi, unidad, 'opcio %s' % mejor, desv))
    if mejor == letra:
        PASS.append(linea)
    else:
        FAIL.append(linea + '   (la bona es %s)' % letra)


# ------------------------------------------------------------------ 2012
def p_11042012_1():
    """H2S en recipiente rigido: 10 dm3, 0,9 kg, 7,5 MPa -> T."""
    tc, pc, w, m = H2S
    n = 900.0 / m                      # mol
    v = 0.010 / n                      # m3/mol
    vr = pc * v / (R * tc)
    # se busca la T que da 7,5 MPa con ese Vr
    lo, hi = 200.0, 900.0
    for _ in range(200):
        t = 0.5 * (lo + hi)
        g = lk.generalizado_tv(t / tc, vr, w)
        if g['z'] * R * t / v > 7.5e6:
            hi = t
        else:
            lo = t
    anota('11/04/2012 q1', 'T del H2S', 0.5 * (lo + hi), 432.0, 'K',
          [('a', 591), ('b', 612), ('c', 121), ('d', 432), ('e', 223)], 'd')


def p_11042012_2():
    """NO, 10 mol, 360 K, compresion isoterma reversible 6,48 -> 64,8 MPa."""
    tc, pc, w, _ = NO
    g1 = lk.estado_tp(tc, pc, w, 360.0, 6.48e6)
    g2 = lk.estado_tp(tc, pc, w, 360.0, 64.8e6)
    ds = -R * math.log(10.0) + (g2['ds_mol'] - g1['ds_mol'])
    q = 10 * 360.0 * ds / 1000.0
    anota('11/04/2012 q2', 'Q isoterma', q, -94.5, 'kJ',
          [('a', -17.4), ('b', -1437.7), ('c', -94.5), ('d', -268.9),
           ('e', -893.3)], 'c')


def p_30102012_2():
    """n-butano, 429,5 K, compresion isoterma reversible 1,517 -> 11,376 MPa."""
    tc, pc, w, _ = BUTA
    g1 = lk.estado_tp(tc, pc, w, 429.5, 1.517e6)
    g2 = lk.estado_tp(tc, pc, w, 429.5, 11.376e6)
    ds = -R * math.log(11.376 / 1.517) + (g2['ds_mol'] - g1['ds_mol'])
    q = 429.5 * ds                      # J/mol = kJ/kmol
    anota('30/10/2012 q2', 'Q molar isoterma', q, -17231.7, 'kJ/kmol',
          [('a', -23117.7), ('b', -7231.78), ('c', -6894.56),
           ('d', -12731.7), ('e', -17231.7)], 'e')


# ------------------------------------------------------------------ 2013
def p_17042013_6():
    """2 kmol, 6 MPa constante, 360 -> 450 K. Tc=300 K, Pc=5 MPa, w=0."""
    tc, pc, w, cp = 300.0, 5.0e6, 0.0, 40.0
    g1 = lk.estado_tp(tc, pc, w, 360.0, 6.0e6)
    g2 = lk.estado_tp(tc, pc, w, 450.0, 6.0e6)
    n = 2000.0
    q = n * (cp * 90.0 + g2['dh_mol'] - g1['dh_mol']) / 1000.0
    wk = -6.0e6 * n * (g2['v'] - g1['v']) / 1000.0
    anota('17/04/2013 q6', 'Q i W a P constant', (q, wk), (9520.0, -2272.0),
          'kJ', [('a', (7002, -3005)), ('b', (6951, -2272)),
                 ('c', (9520, -2100)), ('d', (8144, -3412)),
                 ('e', (9520, -2272))], 'e')


def p_29102013_6():
    """Compresor: 1,856 MPa/267,54 K -> 9,28 MPa/383 K, 0,55 kg/s."""
    tc, pc, w = 191.1, 4.64e6, 0.0
    mm, cp = 16.0, 2.2537               # g/mol, kJ/(kg*K)
    g1 = lk.estado_tp(tc, pc, w, 267.54, 1.856e6)
    g2 = lk.estado_tp(tc, pc, w, 383.0, 9.28e6)
    dh = cp * (383.0 - 267.54) + (g2['dh_mol'] - g1['dh_mol']) / mm
    anota('29/10/2013 q6', 'W del compressor', 0.55 * dh, 125.8, 'kW',
          [('a', 189.3), ('b', 143.1), ('c', 76.6), ('d', 267.7),
           ('e', 125.8)], 'e')


# ------------------------------------------------------------------ 2017
def p_30102017_7():
    """15 kg, M=58,1, 54,75 bar constante, 33 -> 155,5 C."""
    tc, pc, w = 408.2, 3.65e6, 0.0
    n = 15000.0 / 58.1
    g1 = lk.estado_tp(tc, pc, w, 306.15, 5.475e6)
    g2 = lk.estado_tp(tc, pc, w, 428.65, 5.475e6)
    dv = n * (g2['v'] - g1['v'])
    anota('30/10/2017 q7', "volum i treball d'expansio",
          (dv * 1000.0, -5.475e6 * dv / 1000.0), (23.04, -126.2), 'dm3, kJ',
          [('a', (1.78, -9.7)), ('b', (23.04, -126.2)),
           ('c', (1.78, -126.2)), ('d', (23.04, -328.0)),
           ('e', (15.7, -126.2))], 'b')


def p_30102017_8():
    """El mismo, con cp* = 19,252 + 0,261*T J/(mol*K) -> calor aportada."""
    tc, pc, w = 408.2, 3.65e6, 0.0
    n = 15000.0 / 58.1
    t1, t2 = 306.15, 428.65
    g1 = lk.estado_tp(tc, pc, w, t1, 5.475e6)
    g2 = lk.estado_tp(tc, pc, w, t2, 5.475e6)
    # integral de cp* dT con cp* lineal en T
    ideal = 19.252 * (t2 - t1) + 0.261 / 2.0 * (t2 ** 2 - t1 ** 2)
    q = n * (ideal + g2['dh_mol'] - g1['dh_mol']) / 1000.0
    anota('30/10/2017 q8', 'calor aportada', q, 5045.2, 'kJ',
          [('a', 14105.1), ('b', 11532.0), ('c', 3641.6), ('d', 5045.2),
           ('e', 22242.9)], 'd')


# ------------------------------------------------------------------ 2019
def p_30102019_9():
    """Etileno: 0,1 m3 a 290 K y 2 MPa -> 0,5 MPa, isoterma reversible."""
    tc, pc, w, _ = ETILE
    g1 = lk.estado_tp(tc, pc, w, 290.0, 2.0e6)
    g2 = lk.estado_tp(tc, pc, w, 290.0, 0.5e6)
    n = 0.1 / g1['v']
    ds = -R * math.log(0.25) + (g2['ds_mol'] - g1['ds_mol'])
    q = n * 290.0 * ds / 1000.0
    du = g2['dh_mol'] - g1['dh_mol'] - R * 290.0 * (g2['z'] - g1['z'])
    wk = q - n * du / 1000.0
    anota('30/10/2019 q9', 'Q i W isoterms etile', (q, -wk), (374.5, -322.1),
          'kJ', [('a', (374.5, -24.0)), ('b', (288.3, -243.1)),
                 ('c', (374.5, -322.1)), ('d', (76.5, -24.0)),
                 ('e', (243.1, -243.1))], 'c')


def p_30102019_10():
    """2 mol/s, 22,8 bar constante, 40,2 -> 270,3 C. Tc=319,7 K, Pc=3,8 MPa."""
    tc, pc, w, cp = 319.7, 3.8e6, 0.0, 35.7
    t1, t2 = 313.35, 543.45
    g1 = lk.estado_tp(tc, pc, w, t1, 2.28e6)
    g2 = lk.estado_tp(tc, pc, w, t2, 2.28e6)
    q = 2.0 * (cp * (t2 - t1) + g2['dh_mol'] - g1['dh_mol']) / 1000.0
    vol = 2.0 * g2['v'] * 3600.0
    anota('30/10/2019 q10', 'calor i cabal volumetric', (q, vol),
          (19.44, 13.79), 'kW, m3/h',
          [('a', (14.43, 14.27)), ('b', (19.44, 13.79)),
           ('c', (21.89, 8.22)), ('d', (19.44, 6.05)),
           ('e', (14.43, 13.79))], 'b')


# ------------------------------------------------------------------ 2021
def p_02112021_7():
    """10 mol, isoterma 308 K, 10 -> 5 MPa, resistencia electrica.

    Adiabatico: W_elec = dU + integral(P dv), y como la integral a T
    constante es T*ds - du, todo se reduce a W_elec = n*T*ds.
    """
    tc, pc, w = 280.0, 5.0e6, 0.09
    g1 = lk.estado_tp(tc, pc, w, 308.0, 10.0e6)
    g2 = lk.estado_tp(tc, pc, w, 308.0, 5.0e6)
    ds = -R * math.log(0.5) + (g2['ds_mol'] - g1['ds_mol'])
    anota('02/11/2021 q7', "W electric i dS univers",
          (10 * 308.0 * ds / 1000.0, 10 * ds), (53.57, 173.9), 'kJ, J/K',
          [('a', (177.5, 0)), ('b', (53.57, 173.9)), ('c', (177.5, 57.6)),
           ('d', (53.57, 0)), ('e', (456.8, 173.9))], 'b')


# ------------------------------------------------------------------ 2022
def p_06042022_7():
    """10 mol butano, 340,24 K, 379,2 -> 758,4 kPa isoterma reversible."""
    tc, pc, w, _ = BUTA
    g1 = lk.estado_tp(tc, pc, w, 340.24, 379.2e3)
    g2 = lk.estado_tp(tc, pc, w, 340.24, 758.4e3)
    anota('06/04/2022 q7', 'rv = Vini/Vfin', g1['v'] / g2['v'], 2.22, '-',
          [('a', 1.68), ('b', 2.22), ('c', 3.14), ('d', 4.45), ('e', 5.23)],
          'b')


def p_06042022_8():
    """Y su calor."""
    tc, pc, w, _ = BUTA
    g1 = lk.estado_tp(tc, pc, w, 340.24, 379.2e3)
    g2 = lk.estado_tp(tc, pc, w, 340.24, 758.4e3)
    ds = -R * math.log(2.0) + (g2['ds_mol'] - g1['ds_mol'])
    anota('06/04/2022 q8', 'Q bescanviada', 10 * 340.24 * ds / 1000.0, -26.0,
          'kJ', [('a', -11.8), ('b', -26.0), ('c', -37.1), ('d', 11.8),
                 ('e', 26.0)], 'b')


# ------------------------------------------------------------------ 2023
def p_14042023_8():
    """85 mol a 69 MPa y 209 K. Tc=190 K, Pc=46 MPa, w=0."""
    tc, pc, w = 190.0, 46.0e6, 0.0
    g = lk.estado_tp(tc, pc, w, 209.0, 69.0e6)
    vreal = 85 * g['v']
    videal = 85 * R * 209.0 / 69.0e6
    err = 100.0 * (vreal - videal) / vreal
    anota('14/04/2023 q8', 'volum i error del gas ideal',
          (vreal * 1000.0, abs(err)), (0.98, 118.3), 'dm3, %',
          [('a', (1.96, 9.21)), ('b', (0.98, 118.3)), ('c', (1.96, 118.3)),
           ('d', (0.98, 9.21)), ('e', (0.49, 236.6))], 'b')


def p_14042023_9():
    """El mismo deposito rigido hasta 92 MPa y 228 K. cp*=34 J/(mol*K)."""
    tc, pc, w, cp = 190.0, 46.0e6, 0.0, 34.0
    g1 = lk.estado_tp(tc, pc, w, 209.0, 69.0e6)
    g2 = lk.estado_tp(tc, pc, w, 228.0, 92.0e6)
    du = ((cp - R) * (228.0 - 209.0)
          + (g2['dh_mol'] - g1['dh_mol'])
          - R * (228.0 * g2['z'] - 209.0 * g1['z']) + R * (228.0 - 209.0))
    anota('14/04/2023 q9', 'W electric', 85 * du / 1000.0, 49.0, 'kJ',
          [('a', 123), ('b', 49), ('c', 72), ('d', 3), ('e', 98)], 'b')


# ------------------------------------------------------------------ 2024
def p_31102024_3():
    """5 mol etileno, 197,7 K, 0,1 bar -> 6,05 MPa isoterma reversible."""
    tc, pc, w, _ = ETILE
    v1 = 5 * R * 197.7 / 1.0e4          # el enunciado dice: gas ideal
    g2 = lk.estado_tp(tc, pc, w, 197.7, 6.05e6, fase='liquido')
    dv = 5 * g2['v'] - v1
    anota('31/10/2024 q3', 'variacio de volum', dv, -0.82, 'm3',
          [('a', 0.45), ('b', -0.45), ('c', 0.82), ('d', -0.82), ('e', 0)],
          'd')


def p_31102024_4():
    """Y su calor."""
    tc, pc, w, _ = ETILE
    g2 = lk.estado_tp(tc, pc, w, 197.7, 6.05e6, fase='liquido')
    # estado 1: gas ideal, discrepancias nulas
    ds = -R * math.log(6.05e6 / 1.0e4) + g2['ds_mol']
    anota('31/10/2024 q4', 'Q isoterma', 5 * 197.7 * ds / 1000.0, -94.93,
          'kJ', [('a', 245.6), ('b', -245.6), ('c', 94.93), ('d', -94.93),
                 ('e', 0)], 'd')


# ------------------------------------------------------------------ 2025
def p_09042025_1():
    """Difusor: 50 bar/300 K, 300 m/s, seccion 0,002 m2. M=120 g/mol."""
    tc, pc, w, mm = 300.0, 5.0e6, 0.089, 120.0
    g = lk.estado_tp(tc, pc, w, 300.0, 50.0e5)
    vesp = g['v'] / (mm / 1000.0)       # m3/kg
    anota('09/04/2025 q1', 'flux massic', 0.002 * 300.0 / vesp, 511.0, 'kg/s',
          [('a', 765), ('b', 6), ('c', 234), ('d', 15), ('e', 511)], 'e')


def p_09042025_2():
    """Y la velocidad de salida a 250 bar y 390 K."""
    tc, pc, w, mm, cp = 300.0, 5.0e6, 0.089, 120.0, 43.0
    g1 = lk.estado_tp(tc, pc, w, 300.0, 50.0e5)
    g2 = lk.estado_tp(tc, pc, w, 390.0, 250.0e5)
    dh = (cp * 90.0 + g2['dh_mol'] - g1['dh_mol']) / (mm / 1000.0)  # J/kg
    v2 = math.sqrt(max(0.0, 300.0 ** 2 - 2 * dh))
    anota('09/04/2025 q2', 'velocitat de sortida', v2, 174.1, 'm/s',
          [('a', 102.3), ('b', 174.1), ('c', 8.4), ('d', 223.4),
           ('e', 44.5)], 'b')


def p_28102025_1():
    """12 dm3, 144,3 mol, 345 -> 315 K. Tc=300 K, Pc=7,5 MPa, w=0."""
    tc, pc, w = 300.0, 7.5e6, 0.0
    v = 0.012 / 144.3
    g1 = lk.estado_tv(tc, pc, w, 345.0, v)
    g2 = lk.estado_tv(tc, pc, w, 315.0, v)
    anota('28/10/2025 q1', 'disminucio de pressio',
          (g2['p'] - g1['p']) / 1e6, -6.0, 'MPa',
          [('a', -6), ('b', -4), ('c', -0.6), ('d', -0.4), ('e', -8)], 'a')


def p_28102025_2():
    """Y la calor cedida. cp*=37,4 J/(mol*K)."""
    tc, pc, w, cp = 300.0, 7.5e6, 0.0, 37.4
    v = 0.012 / 144.3
    g1 = lk.estado_tv(tc, pc, w, 345.0, v)
    g2 = lk.estado_tv(tc, pc, w, 315.0, v)
    # u - u* = (h - h*) - (Pv - RT)
    u1 = g1['dh_mol'] - (g1['p'] * v - R * 345.0)
    u2 = g2['dh_mol'] - (g2['p'] * v - R * 315.0)
    du = (cp - R) * (315.0 - 345.0) + (u2 - u1)
    anota('28/10/2025 q2', 'calor cedida', 144.3 * du / 1000.0, -155.0, 'kJ',
          [('a', -1099), ('b', -891), ('c', -155), ('d', -25), ('e', -382)],
          'c')


# ------------------------------------------------------------------ 2026
def p_08042026_4():
    """Turbina: entra a Tr=2,6 y Pr=3; sale a 100 kPa y 400 K (gas ideal)."""
    tc, pc, w = 305.3, 4.87e6, 0.099
    rm, cp = 0.2765, 1.75               # kJ/(kg*K), del enunciado
    g1 = lk.generalizado(2.6, 3.0, w)
    dh1 = g1['dh'] * rm * tc            # (h1 - h1*), negativo, kJ/kg
    t1 = 2.6 * tc
    # el estado 2 es gas ideal, asi que su discrepancia es nula
    dh = cp * (t1 - 400.0) + dh1        # h1 - h2
    pot = 1.5 * dh - 450.0              # potencia PRODUCIDA
    anota('08/04/2026 q4', 'potencia de la turbina', -pot, -535.0, 'kW',
          [('a', -122), ('b', -350), ('c', -535), ('d', -648), ('e', -972)],
          'c')


def main():
    pruebas = [p_11042012_1, p_11042012_2, p_30102012_2, p_17042013_6,
               p_29102013_6, p_30102017_7, p_30102017_8, p_30102019_9,
               p_30102019_10, p_02112021_7, p_06042022_7, p_06042022_8,
               p_14042023_8, p_14042023_9, p_31102024_3, p_31102024_4,
               p_09042025_1, p_09042025_2, p_28102025_1, p_28102025_2,
               p_08042026_4]
    for fn in pruebas:
        try:
            fn()
        except Exception as e:
            FAIL.append('%-16s EXCEPCION %s: %s'
                        % (fn.__name__, type(e).__name__, e))
    print('%-16s %-34s %11s    %10s %-8s  %-8s %6s'
          % ('examen', 'magnitud', 'calculat', 'oficial', 'unitat',
             'tria', 'desv.'))
    print('-' * 104)
    for l in PASS:
        print('  ' + l)
    for l in FAIL:
        print('  FALLA ' + l)
    if NOTAS:
        print('-' * 104)
        for l in NOTAS:
            print('  ' + l)
    print('-' * 104)
    print('PASS: %d    FAIL: %d' % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
