# -*- coding: utf-8 -*-
"""Dibuja las pantallas de la app tal como se ven en la calculadora.

Para la guia del estudiante hacen falta imagenes, y una foto de la pantalla
sale torcida, con reflejos y desactualizada en cuanto se toca una linea. Esto
las genera.

**Los numeros no se teclean aqui.** Cada pantalla llama a engine.py o a lk.py
y formatea con las mismas funciones que el PPL (TSIG = n cifras
significativas, TDEC = n decimales), asi que lo que se ve en la guia es lo que
va a salir en la calculadora. Si cambia un motor, la guia cambia con el.

Lo que SI esta transcrito a mano son las coordenadas: cada TEXTOUT_P de
ppl/TERMO.txt y ppl/GENER.txt con su x, su y y su fuente. Es la unica parte
que puede separarse del original con el tiempo, y por eso la guia dice que las
pantallas son una reproduccion, no una foto.

Geometria de la Prime: 320x240; el area de app va de y=0 a y=212 y por debajo
esta la fila de teclas de pantalla.
"""
from __future__ import unicode_literals
import os

from PIL import Image, ImageDraw, ImageFont

ANCHO, ALTO = 320, 240
ESCALA = 3                      # se dibuja x3 y se reduce: bordes limpios

FUENTES = ('C:/Windows/Fonts/DejaVuSans.ttf',
           '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
FUENTES_B = ('C:/Windows/Fonts/DejaVuSans-Bold.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')

# Altura de cada fuente de TEXTOUT_P, deducida de los interlineados que usa el
# PPL y que en una G2 real no se solapan: font 2 va a 17-19 px de separacion y
# font 3 a 21-25. No es una medida de la calculadora, es un tamano que
# reproduce el mismo encaje.
TAM = {1: 9, 2: 12, 3: 16, 4: 20}

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
AZUL = (0, 0, 180)
AZUL_F = (0, 0, 140)
VERDE = (0, 120, 0)
ROJO = (200, 0, 0)
NARANJA = (200, 80, 0)
GRIS = (90, 90, 90)
GRIS_C = (70, 70, 70)
BOTON = (228, 236, 252)
BARRA = (208, 216, 232)


def _fuente(tam, negrita=False):
    for ruta in (FUENTES_B if negrita else FUENTES):
        if os.path.isfile(ruta):
            return ImageFont.truetype(ruta, tam * ESCALA)
    return ImageFont.load_default()


class Pantalla(object):
    """Un lienzo de 320x240 con las primitivas que usa el PPL."""

    def __init__(self, fondo=BLANCO):
        self.img = Image.new('RGB', (ANCHO * ESCALA, ALTO * ESCALA), fondo)
        self.d = ImageDraw.Draw(self.img)

    # -- primitivas ----------------------------------------------------
    def texto(self, txt, x, y, font=2, color=NEGRO, ancho=None,
              negrita=False, dreta=False):
        """TEXTOUT_P. `ancho` recorta, como el septimo argumento del original.

        `dreta` alinea por la derecha. INPUT pone la etiqueta pegada a su
        campo, no al principio del hueco: alineandola a la izquierda, el "="
        del segundo campo de una fila caia encima del texto del primero.
        """
        f = _fuente(TAM[font], negrita)
        if ancho is not None:
            while txt and self.d.textsize(txt, font=f)[0] > ancho * ESCALA:
                txt = txt[:-1]
        px = x * ESCALA
        if dreta:
            px -= self.d.textsize(txt, font=f)[0]
        self.d.text((px, y * ESCALA), txt, font=f, fill=color)
        return self

    def rect(self, x1, y1, x2, y2, borde=None, relleno=None):
        """RECT_P."""
        self.d.rectangle([x1 * ESCALA, y1 * ESCALA,
                          x2 * ESCALA - 1, y2 * ESCALA - 1],
                         fill=relleno, outline=borde,
                         width=max(1, ESCALA - 1))
        return self

    def guarda(self, ruta):
        img = self.img.resize((ANCHO * 2, ALTO * 2), Image.LANCZOS)
        # marco fino, para que la pantalla se distinga del papel
        m = Image.new('RGB', (ANCHO * 2 + 4, ALTO * 2 + 4), (120, 120, 120))
        m.paste(img, (2, 2))
        m.save(ruta)
        return ruta


# ---------------------------------------------------------------- formatos
# Las mismas dos funciones del PPL, para que la guia redondee igual.
def tsig(x, n):
    """TSIG: n cifras significativas."""
    import math
    if x == 0:
        return '0'
    d = n - 1 - int(math.floor(math.log10(abs(x))))
    d = max(0, min(9, d))
    return _limpia(round(x, d))


def tdec(x, n):
    """TDEC: n decimales."""
    return _limpia(round(x, n))


def _limpia(v):
    """STRING() de la Prime: sin ceros de relleno a la derecha."""
    s = '%.10f' % v
    s = s.rstrip('0').rstrip('.')
    return s if s not in ('', '-') else '0'


# ------------------------------------------------------------ formularios
def formulario(titulo, filas, ayuda):
    """Aproximacion del dialogo INPUT.

    `filas` es una lista de listas de (etiqueta, valor, x%, ancho%), una por
    fila; con `ancho%` NEGATIVO el campo se dibuja como desplegable. INPUT
    coloca cada campo en {x%, ancho%, fila} y pone la etiqueta pegada a su
    izquierda; eso es lo que se reproduce.
    """
    p = Pantalla()
    p.rect(0, 0, ANCHO, 22, relleno=BARRA)
    p.texto(titulo, 5, 4, 2, AZUL_F, 310, negrita=True)
    y = 32
    for fila in filas:
        for (etq, val, x, anc) in fila:
            desple = anc < 0
            anc = abs(anc)
            px = int(ANCHO * x / 100.0)
            pw = int(ANCHO * anc / 100.0)
            p.texto(etq, px - 6, y + 4, 2, NEGRO, 70, dreta=True)
            p.rect(px, y, px + pw, y + 22, borde=(70, 70, 70), relleno=BLANCO)
            p.texto(val, px + 5, y + 4, 2, NEGRO, pw - (22 if desple else 8))
            if desple:
                # la marca del desplegable: de un vistazo se distingue de un
                # campo numerico, que es lo que decide si hay que teclear
                p.d.polygon([((px + pw - 14) * ESCALA, (y + 9) * ESCALA),
                             ((px + pw - 6) * ESCALA, (y + 9) * ESCALA),
                             ((px + pw - 10) * ESCALA, (y + 15) * ESCALA)],
                            fill=(60, 60, 60))
        y += 30
    p.texto(ayuda, 5, 196, 1, GRIS_C, 310)
    p.rect(0, 213, ANCHO, ALTO, relleno=BARRA)
    for i, etq in enumerate(('', '', '', '', 'Cancel', 'OK')):
        x = i * 53
        p.rect(x, 213, x + 53, ALTO, borde=(150, 150, 150))
        if etq:
            p.texto(etq, x + 6, 219, 1, NEGRO, 46)
    return p


# =========================================================== las pantallas
# Cada una transcribe las coordenadas de su TEXTOUT_P en el PPL. Los numeros
# salen de los motores.
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E
import lk

PEU = "tecla=tornar  View=menu  Help=ajuda  Esc=surt"

TITOLS = ('TAULES', 'GAS REAL', 'PROCES REAL')
SUBTITOLS = ("propietats d'una substancia",
             'un estat: Z, v i discrepancies',
             'dos estats: dh, ds i du')


def menu(resaltat=0):
    """ppl/MENU.txt: TMDRAW. Con `resaltat` se marca un boton, para senalarlo
    en la guia sin dibujar una flecha encima."""
    p = Pantalla()
    p.texto('TERMODINAMICA', 6, 4, 3, AZUL_F, 308, negrita=True)
    for i in range(1, 4):
        y = 32 + (i - 1) * 60
        relleno = (255, 236, 190) if i == resaltat else BOTON
        p.rect(6, y, 314, y + 52, borde=AZUL_F, relleno=relleno)
        p.texto('%d.  %s' % (i, TITOLS[i - 1]), 18, y + 7, 3, AZUL_F, 284)
        p.texto(SUBTITOLS[i - 1], 18, y + 31, 2, GRIS_C, 284)
    p.texto('toca el boto o prem 1/2/3    Help=ajuda   Esc=surt',
            6, 216, 2, GRIS_C, 308)
    return p


# ------------------------------------------------------------- 1. TAULES
def taules_form(sust, d1, v1, d2, v2):
    return formulario(
        'TERMO - quines dues coneixes?',
        [[('Sust', sust, 22, -72)],
         [('Dada 1', d1, 22, -30), ('=', v1, 58, 37)],
         [('Dada 2', d2, 22, -30), ('=', v2, 58, 37)]],
        'valor, en la unitat del desplegable')


def _regio(st):
    """El mismo texto que arma TSHOW: la campana se parte en sus fronteras."""
    if st['region'] == E.LIQUID:
        return 'LIQUID COMPRIMIT'
    if st['region'] == E.SUPER:
        return 'SUPERCRITIC'
    if st['region'] == E.VAPOR:
        return 'VAPOR SOBREESCALFAT'
    x = st['x']
    if x is not None and x <= 1e-9:
        return 'LIQUID SATURAT  x=0'
    if x is not None and x >= 1 - 1e-9:
        return 'VAPOR SATURAT  x=1'
    return 'BIFASIC'


def taules_res(clau, parell, a, b):
    """ppl/TERMO.txt: TSHOW."""
    sub = E.get(clau)
    st = E.solve(sub, parell, a, b)
    p = Pantalla()
    p.texto(sub['name'], 4, 2, 3, NEGRO, 316)
    p.texto(_regio(st), 4, 24, 3, AZUL, 316)
    ut = ' K' if sub['T_unit'] == 'K' else ' C'
    y = 45
    if sub['T_unit'] == 'K':
        p.texto('T = %s K = %s C' % (tdec(st['T'], 2), tdec(st['T'] - 273.15, 2)),
                4, y, 3, NEGRO, 316)
    else:
        p.texto('T = %s C = %s K' % (tdec(st['T'], 2), tdec(st['T'] + 273.15, 2)),
                4, y, 3, NEGRO, 316)
    for etq, val in (('P = %s MPa' % tsig(st['P'], 5), None),
                     ('v = %s m3/kg' % tsig(st['v'], 6), None),
                     ('u = %s kJ/kg' % tdec(st['u'], 2), None),
                     ('h = %s kJ/kg' % tdec(st['h'], 2), None),
                     ('s = %s kJ/kgK' % tdec(st['s'], 4), None)):
        y += 21
        p.texto(etq, 4, y, 3, NEGRO, 316)
    y += 21
    if st['x'] is not None:
        p.texto('x = %s' % tdec(st['x'], 4), 4, y, 3, VERDE, 316)
    else:
        p.texto('x = --', 4, y, 3, NEGRO, 316)
    # contexto de saturacion
    if st['region'] not in (E.MIX, E.SUPER):
        try:
            sa = E.sat_at_P(sub, st['P'])
            if st['region'] == E.VAPOR:
                p.texto('Tsat = %s%s   sobreescalfament +%s'
                        % (tdec(sa['T'], 2), ut, tdec(st['T'] - sa['T'], 1)),
                        4, 191, 2, (0, 110, 0), 316)
            else:
                p.texto('Tsat = %s%s   subrefredament -%s'
                        % (tdec(sa['T'], 2), ut, tdec(sa['T'] - st['T'], 1)),
                        4, 191, 2, (0, 110, 0), 316)
        except Exception:
            pass
    if st['avisos']:
        p.texto('! ' + st['avisos'][0], 4, 207, 2, NARANJA, 316)
    p.texto(PEU, 4, 224, 2, NEGRO, 316)
    return p


def taules_error(msg):
    p = Pantalla()
    p.texto('ERROR', 4, 4, 4, ROJO, 316, negrita=True)
    p.texto(msg, 4, 34, 3, NEGRO, 316)
    p.texto('Cap valor: revisa dades o rang.', 4, 64, 2, NEGRO, 316)
    p.texto('Prem una tecla per continuar', 4, 210, 2, NEGRO, 316)
    return p



# ----------------------------------------------------- 2 i 3. GENERALITZATS
def _cap(tc, pc, w, sust=None):
    """TGCAP: las constantes activas, siempre a la vista."""
    s = 'Tc=%sK  Pc=%sMPa  w=%s' % (tsig(tc, 5), tsig(pc, 5), tsig(w, 4))
    return ('%s -- %s' % (sust, s)) if sust else s


def _titol(tc, pc, w):
    """El titulo del INPUT, que INPUT si puede construir en cada llamada."""
    return 'Tc=%s Pc=%s w=%s' % (tsig(tc, 5), tsig(pc, 5), tsig(w, 4))


def gener_const(tc, pc, w, mm=0):
    """ppl/GENER.txt: TGDCON, les constants. Nomes surt amb (manual)."""
    return formulario(
        'Constants del fluid',
        [[('Tc[K]', tsig(tc, 6), 24, 26), ('Pc[MPa]', tsig(pc, 6), 70, 26)],
         [('w', tsig(w, 4), 24, 26), ('M', tsig(mm, 6), 70, 26)]],
        'factor acentric (0 si no el donen)')


def gener_cp(cpa=0, cpb=0):
    """ppl/GENER.txt: TGDCP. Nomes a PROCES REAL."""
    return formulario(
        'cp* del gas ideal',
        [[('cp* =', tsig(cpa, 6), 24, 26), ('+ T*', tsig(cpb, 6), 70, 26)]],
        'pendent; 0 si cp* es constant')


def gener_form(tc, pc, w, t, p, v=0, sust='(manual)'):
    """ppl/GENER.txt: el PRIMER formulari de TGTAB: el problema."""
    return formulario(
        'GAS REAL - un estat',
        [[('Sust', sust, 18, -78)],
         [('T [K]', tsig(t, 6), 24, 26), ('P[MPa]', tsig(p, 6), 70, 26)],
         [('v m3/mol', tsig(v, 6), 30, 26)]],
        'si el diposit es RIGID; 0 = usa la P')


def gener_res(tc, pc, w, t, p, v=0, mm=0, sust=None):
    """ppl/GENER.txt: la salida de TGTAB."""
    pa = Pantalla()
    pa.texto('GAS REAL - UN ESTAT', 4, 2, 3, AZUL, 316)
    pa.texto(_cap(tc, pc, w, sust), 4, 24, 2, GRIS, 316)
    tr = t / float(tc)
    try:
        if v > 0:
            g = lk.generalizado_tv(tr, pc * 1e6 * v / (lk.R * tc), w)
            pres = g['z'] * lk.R * t / v / 1e6
            vol = v
        else:
            g = lk.generalizado(tr, p / float(pc), w)
            pres = p
            vol = g['z'] * lk.R * t / (p * 1e6)
    except lk.NoConverge:
        pa.texto('Sense solucio a Tr=%s' % tsig(tr, 4), 4, 60, 3, ROJO, 316)
        pa.texto('Amb aquest volum el punt cau dins la campana:',
                 4, 90, 2, NEGRO, 316)
        pa.texto("alli l'equacio dona pressio negativa i no hi ha estat.",
                 4, 108, 2, NEGRO, 316)
        pa.texto(PEU, 4, 224, 2, NEGRO, 316)
        return pa
    pa.texto('Tr = %s     Pr = %s' % (tdec(tr, 4), tdec(pres / float(pc), 4)),
             4, 44, 3, NEGRO, 316)
    y = 70
    pa.texto('Z0 = %s   Z1 = %s' % (tdec(g['z0'], 4), tdec(g['z1'], 4)),
             4, y, 2, NEGRO, 316); y += 19
    pa.texto('Z  = %s' % tdec(g['z'], 4), 4, y, 3, VERDE, 316); y += 25
    pa.texto('(h-h*)/RTc:  0=%s  1=%s' % (tdec(g['dh0'], 4), tdec(g['dh1'], 4)),
             4, y, 2, NEGRO, 316); y += 19
    pa.texto('             = %s' % tdec(g['dh'], 4), 4, y, 2, AZUL, 316); y += 22
    pa.texto('(s-s*)/R:    0=%s  1=%s' % (tdec(g['ds0'], 4), tdec(g['ds1'], 4)),
             4, y, 2, NEGRO, 316); y += 19
    pa.texto('             = %s' % tdec(g['ds'], 4), 4, y, 2, AZUL, 316); y += 22
    if v > 0:
        pa.texto('P = %s MPa' % tsig(pres, 6), 4, y, 3, VERDE, 316)
    else:
        pa.texto('v = %s m3/mol' % tsig(vol, 5), 4, y, 2, NEGRO, 160)
        if mm > 0:
            pa.texto('= %s m3/kg' % tsig(vol * 1000 / mm, 5), 170, y, 2,
                     NEGRO, 146)
    pa.texto(PEU, 4, 224, 2, NEGRO, 316)
    return pa


def proc_form(tc, pc, w, t1, p1, t2, p2, v1=0, sust='(manual)'):
    """ppl/GENER.txt: el PRIMER formulari de TGPROC: el problema."""
    return formulario(
        'PROCES REAL - dos estats',
        [[('Sust', sust, 18, -54), ('v', tsig(v1, 6), 78, 21)],
         [('T1 [K]', tsig(t1, 6), 24, 26), ('P1[MPa]', tsig(p1, 6), 70, 26)],
         [('T2 [K]', tsig(t2, 6), 24, 26), ('P2[MPa]', tsig(p2, 6), 70, 26)]],
        'm3/mol si el diposit es RIGID; 0 = usa les P')


def _estat(tc, pc, w, t, p, v):
    """Lo que hace TGANY: por presion o por volumen, segun cual le des."""
    if v > 0:
        g = lk.generalizado_tv(t / float(tc), pc * 1e6 * v / (lk.R * tc), w)
        return g, g['z'] * lk.R * t / v / 1e6, v
    g = lk.generalizado(t / float(tc), p / float(pc), w)
    return g, p, g['z'] * lk.R * t / (p * 1e6)


def proc_res(tc, pc, w, cpa, t1, p1, t2, p2, v1=0, v2=0, cpb=0, mm=0,
             sust=None):
    """ppl/GENER.txt: la salida de TGPROC."""
    import math
    pa = Pantalla()
    pa.texto('PROCES REAL - 1 A 2', 4, 2, 3, AZUL, 316)
    pa.texto(_cap(tc, pc, w, sust), 4, 24, 2, GRIS, 316)
    try:
        ga, pr1, va = _estat(tc, pc, w, t1, p1, v1)
        gb, pr2, vb = _estat(tc, pc, w, t2, p2, v2)
    except lk.NoConverge:
        pa.texto('Sense solucio en un dels dos estats.', 4, 60, 3, ROJO, 316)
        pa.texto('Amb v donat, el punt pot caure dins la campana;',
                 4, 90, 2, NEGRO, 316)
        pa.texto('si no, revisa Tc, Pc i les unitats.', 4, 108, 2, NEGRO, 316)
        pa.texto(PEU, 4, 224, 2, NEGRO, 316)
        return pa
    idh = cpa * (t2 - t1) + cpb / 2.0 * (t2 ** 2 - t1 ** 2)
    ids = cpa * math.log(t2 / float(t1)) + cpb * (t2 - t1)
    dh = idh + (gb['dh'] - ga['dh']) * lk.R * tc
    ds = ids - lk.R * math.log(pr2 / pr1) + (gb['ds'] - ga['ds']) * lk.R
    du = dh - lk.R * (gb['z'] * t2 - ga['z'] * t1)
    y = 44
    pa.texto('1: Tr=%s Pr=%s  Z=%s'
             % (tdec(t1 / float(tc), 3), tdec(pr1 / float(pc), 3),
                tdec(ga['z'], 4)), 4, y, 2, NEGRO, 316); y += 18
    pa.texto('2: Tr=%s Pr=%s  Z=%s'
             % (tdec(t2 / float(tc), 3), tdec(pr2 / float(pc), 3),
                tdec(gb['z'], 4)), 4, y, 2, NEGRO, 316); y += 18
    if v1 > 0 or v2 > 0:
        pa.texto('P1 = %s   P2 = %s MPa' % (tsig(pr1, 6), tsig(pr2, 6)),
                 4, y, 2, VERDE, 316); y += 18
    else:
        y += 6
    pa.texto('dh = %s J/mol' % tdec(dh, 1), 4, y, 3, NEGRO, 316); y += 23
    pa.texto('ds = %s J/molK' % tdec(ds, 4), 4, y, 3, NEGRO, 316); y += 23
    pa.texto('du = %s J/mol' % tdec(du, 1), 4, y, 3, NEGRO, 316); y += 23
    if mm > 0:
        pa.texto('per kg:  dh=%s  du=%s kJ/kg'
                 % (tdec(dh / mm, 3), tdec(du / mm, 3)), 4, y, 2, NEGRO, 316)
        y += 18
    if t1 == t2:
        pa.texto('isoterm: q=T*ds= %s J/mol' % tdec(t1 * ds, 1),
                 4, y, 2, VERDE, 316); y += 18
    if pr1 == pr2:
        pa.texto('isobar: w=-P*dv= %s J/mol'
                 % tdec(-pr1 * 1e6 * (vb - va), 1), 4, y, 2, VERDE, 316)
    pa.texto(PEU, 4, 224, 2, NEGRO, 316)
    return pa
