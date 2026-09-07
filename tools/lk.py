# -*- coding: utf-8 -*-
"""Metodos generalizados de Lee-Kesler: motor de referencia (Python).

Es el equivalente de engine.py para la OTRA mitad del libro de tablas. Donde
engine.py interpola la Seccion B (propiedades individualizadas), esto sustituye
la Seccion C: los diagramas generalizados de compresibilidad y las funciones
de discrepancia, que en el examen se leen a ojo sobre tres graficos.

La idea que lo hace barato: **esas tablas no son medidas, son calculadas**.
Lee y Kesler (1975) publicaron una ecuacion de estado tipo BWR con dos juegos
de constantes -fluido simple y fluido de referencia, el n-octano- y las tablas
de Z0/Z1 y de las discrepancias son su salida tabulada. Evaluando la ecuacion
se obtienen los mismos numeros sin llevar los graficos, y con mas cifras de
las que se pueden leer en papel.

Correlacion de Pitzer de tres parametros, para cualquier magnitud X:

    X = X0 + w * X1        X1 = (X_ref - X0) / w_ref      w_ref = 0.3978

Convenio de signos, que es donde se equivoca todo el mundo:

    dh = h - h*   (real menos gas ideal)  ->  NEGATIVO en la region util
    ds = s - s*   a la MISMA T y P

El apunte de clase suele tabular (h* - h)/(R*Tc), es decir el opuesto. Aqui se
devuelve h - h* porque es lo que se suma directamente: h = cp*(T-Tref) + dh.

Unidades: R en J/(mol*K), presiones en Pa, T en K, volumen molar en m3/mol.
"""
from __future__ import unicode_literals
import math

R = 8.314              # J/(mol*K)
W_REF = 0.3978         # factor acentrico del fluido de referencia (n-octano)

# Constantes de la ecuacion de Lee-Kesler. Orden: b1..b4, c1..c4, d1, d2,
# beta, gamma. El primer juego es el fluido simple (w=0), el segundo el de
# referencia.
SIMPLE = (0.1181193, 0.265728, 0.154790, 0.030323,
          0.0236744, 0.0186984, 0.0, 0.042724,
          0.155488e-4, 0.623689e-4, 0.65392, 0.060167)

REFER = (0.2026579, 0.331511, 0.027655, 0.203488,
         0.0313385, 0.0503618, 0.016901, 0.041577,
         0.48736e-4, 0.0740336e-4, 1.226, 0.03754)


class NoConverge(Exception):
    """No se encuentra raiz de volumen para ese (Tr, Pr)."""


# ------------------------------------------------------------------ nucleo
def z_de_vr(k, tr, vr):
    """Factor de compresibilidad de un juego de constantes en (Tr, Vr).

    Vr es el volumen reducido de Lee-Kesler, Vr = Pc*v/(R*Tc), que NO es
    v/vc: es adimensional por construccion y vale Tr/Pr en gas ideal.
    """
    b1, b2, b3, b4, c1, c2, c3, c4, d1, d2, be, ga = k
    bb = b1 - b2 / tr - b3 / tr ** 2 - b4 / tr ** 3
    cc = c1 - c2 / tr + c3 / tr ** 3
    dd = d1 + d2 / tr
    ex = math.exp(-ga / vr ** 2)
    return (1.0 + bb / vr + cc / vr ** 2 + dd / vr ** 5
            + c4 / (tr ** 3 * vr ** 2) * (be + ga / vr ** 2) * ex)


def discrepancias(k, tr, vr, z):
    """(h - h*)/(R*Tc) y (s - s*)/R para un juego de constantes."""
    b1, b2, b3, b4, c1, c2, c3, c4, d1, d2, be, ga = k
    ex = math.exp(-ga / vr ** 2)
    ee = c4 / (2 * tr ** 3 * ga) * (be + 1.0 - (be + 1.0 + ga / vr ** 2) * ex)
    dh = tr * (z - 1.0
               - (b2 + 2 * b3 / tr + 3 * b4 / tr ** 2) / (tr * vr)
               - (c2 - 3 * c3 / tr ** 2) / (2 * tr * vr ** 2)
               + d2 / (5 * tr * vr ** 5)
               + 3 * ee)
    ds = (math.log(z)
          - (b1 + b3 / tr ** 2 + 2 * b4 / tr ** 3) / vr
          - (c1 - 2 * c3 / tr ** 3) / (2 * vr ** 2)
          - d1 / (5 * vr ** 5)
          + 2 * ee)
    return dh, ds


def _raices_vr(k, tr, pr):
    """Todas las raices Vr de P(Tr,Vr) = Pr, de menor a mayor.

    Se buscan por barrido y biseccion en vez de Newton. Motivo: por debajo de
    la temperatura critica la isoterma tiene TRES raices (liquido, rama
    inestable, vapor) y un Newton lanzado desde el gas ideal puede caer en
    cualquiera sin avisar. Un barrido dice cuantas hay y de que tipo.
    """
    def f(vr):
        return z_de_vr(k, tr, vr) * tr / vr - pr

    # Rejilla logaritmica: Vr va de ~0.03 (liquido comprimido) a 1e4 (gas a
    # presion muy baja). 400 puntos separan las tres raices con holgura.
    n = 400
    lo, hi = math.log(0.03), math.log(1.0e4)
    xs = [math.exp(lo + (hi - lo) * i / float(n)) for i in range(n + 1)]
    prev = xs[0]
    fprev = f(prev)
    out = []
    for x in xs[1:]:
        fx = f(x)
        if fprev == 0.0:
            out.append(prev)
        elif fprev * fx < 0:
            a, b = prev, x
            fa = fprev
            for _ in range(80):
                m = 0.5 * (a + b)
                fm = f(m)
                if fa * fm <= 0:
                    b = m
                else:
                    a, fa = m, fm
            out.append(0.5 * (a + b))
        prev, fprev = x, fx
    return out


def vr_de_trpr(k, tr, pr, fase='vapor'):
    """Vr en (Tr, Pr). fase: 'vapor' toma la raiz mayor, 'liquido' la menor."""
    rs = _raices_vr(k, tr, pr)
    if not rs:
        raise NoConverge('sense arrel Vr a Tr=%.4f Pr=%.4f' % (tr, pr))
    return rs[-1] if fase == 'vapor' else rs[0]


# ------------------------------------------------------- interfaz de Pitzer
def generalizado(tr, pr, w=0.0, fase='vapor'):
    """Z, dh y ds generalizados en (Tr, Pr).

    Devuelve un diccionario con los terminos separados -z0, z1, dh0, dh1,
    ds0, ds1- ademas de los combinados, porque es exactamente lo que el
    alumno leeria en los tres graficos y conviene poder ensenarlo.

    dh viene ya como (h - h*)/(R*Tc) y ds como (s - s*)/R.
    """
    vr0 = vr_de_trpr(SIMPLE, tr, pr, fase)
    z0 = z_de_vr(SIMPLE, tr, vr0)
    dh0, ds0 = discrepancias(SIMPLE, tr, vr0, z0)

    vrr = vr_de_trpr(REFER, tr, pr, fase)
    zr = z_de_vr(REFER, tr, vrr)
    dhr, dsr = discrepancias(REFER, tr, vrr, zr)

    z1 = (zr - z0) / W_REF
    dh1 = (dhr - dh0) / W_REF
    ds1 = (dsr - ds0) / W_REF
    return {'z0': z0, 'z1': z1, 'z': z0 + w * z1,
            'dh0': dh0, 'dh1': dh1, 'dh': dh0 + w * dh1,
            'ds0': ds0, 'ds1': ds1, 'ds': ds0 + w * ds1,
            'vr': vr0, 'tr': tr, 'pr': pr, 'w': w}


def generalizado_tv(tr, vr, w=0.0):
    """Lo mismo pero desde (Tr, Vr): sin iterar, porque Vr ya lo fija todo.

    Es el caso del deposito rigido, que en los examenes sale tanto como el
    otro: se conoce el volumen y se pregunta la presion.

    Ojo: el fluido de referencia se evalua al MISMO Vr, no al mismo Pr, que
    es como estan construidas las tablas de Lee-Kesler.

    Con (T, v) NO hay garantia de que la presion salga positiva: dentro de la
    campana la isoterma de Lee-Kesler baja por debajo de cero, y ahi Z <= 0.
    Eso no es un estado, es la rama mecanicamente inestable de la ecuacion, y
    la discrepancia de entropia lleva un ln(Z) que no admite ese numero. Se
    rechaza en vez de calcular: por (T, P) el caso no existe, porque
    Z = Pr*Vr/Tr es positivo por construccion.
    """
    z0 = z_de_vr(SIMPLE, tr, vr)
    zr = z_de_vr(REFER, tr, vr)
    if z0 <= 0 or zr <= 0:
        raise NoConverge('pressio negativa a Tr=%.4f Vr=%.4f: (T,v) cau dins'
                         ' la campana' % (tr, vr))
    dh0, ds0 = discrepancias(SIMPLE, tr, vr, z0)
    dhr, dsr = discrepancias(REFER, tr, vr, zr)
    z1 = (zr - z0) / W_REF
    dh1 = (dhr - dh0) / W_REF
    ds1 = (dsr - ds0) / W_REF
    return {'z0': z0, 'z1': z1, 'z': z0 + w * z1,
            'dh0': dh0, 'dh1': dh1, 'dh': dh0 + w * dh1,
            'ds0': ds0, 'ds1': ds1, 'ds': ds0 + w * ds1,
            'vr': vr, 'tr': tr, 'pr': (z0 + w * z1) * tr / vr, 'w': w}


# --------------------------------------------------------- capa con unidades
def estado_tp(tc, pc, w, t, p, fase='vapor'):
    """Estado real en (T, P). tc en K, pc en Pa, t en K, p en Pa.

    Devuelve v (m3/mol), Z, dh (J/mol) y ds (J/(mol*K)), con dh = h - h* y
    ds = s - s* a la misma T y P.
    """
    g = generalizado(t / tc, p / pc, w, fase)
    g['t'], g['p'] = t, p
    g['v'] = g['z'] * R * t / p
    g['dh_mol'] = g['dh'] * R * tc
    g['ds_mol'] = g['ds'] * R
    return g


def estado_tv(tc, pc, w, t, v):
    """Estado real en (T, v). v es volumen MOLAR en m3/mol."""
    g = generalizado_tv(t / tc, pc * v / (R * tc), w)
    g['t'], g['v'] = t, v
    g['p'] = g['z'] * R * t / v
    g['dh_mol'] = g['dh'] * R * tc
    g['ds_mol'] = g['ds'] * R
    return g


def ds_proceso(g1, g2, cp_ig, p1, p2, t1, t2):
    """s2 - s1 en J/(mol*K) para cp* constante.

    s2 - s1 = [cp* ln(T2/T1) - R ln(P2/P1)]  +  (ds2 - ds1)

    El corchete es el gas ideal; el parentesis, las dos discrepancias. Es la
    receta del apunte: se va al gas ideal, se hace el camino alli, y se
    vuelve.
    """
    ideal = cp_ig * math.log(t2 / t1) - R * math.log(p2 / p1)
    return ideal + (g2['ds_mol'] - g1['ds_mol'])


def dh_proceso(g1, g2, cp_ig, t1, t2):
    """h2 - h1 en J/mol para cp* constante."""
    return cp_ig * (t2 - t1) + (g2['dh_mol'] - g1['dh_mol'])
