# -*- coding: utf-8 -*-
"""Genera docs/GUIA_ESTUDIANT.pdf: la guia de la app, en catalan.

Para quien cursa Termodinamica por primera vez y no ha visto nunca la
calculadora. Se genera en vez de escribirse porque **las capturas y los
numeros salen de los motores**: cada pantalla la dibuja tools/pantalla.py
llamando a engine.py y a lk.py, asi que la guia no puede ensenar un numero
que la app no de. Si cambia un motor, se regenera y sigue siendo cierta.

Sin dependencias nuevas: matplotlib (PDF vectorial, texto seleccionable) y
Pillow (las pantallas), que ya estaban.

    python tools/gen_guia.py
"""
from __future__ import unicode_literals
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pantalla as PA
import guia_text as T

IMG = os.path.join(ROOT, 'docs', 'guia', 'img')
OUT = os.path.join(ROOT, 'docs', 'GUIA_ESTUDIANT.pdf')

# Con --png deja ademas cada pagina suelta en docs/guia/img/, para poder
# mirarlas sin abrir el PDF. No se versionan.
PNG = '--png' in sys.argv

A4 = (8.27, 11.69)
MARGE_X = 0.85
MARGE_DALT = 0.80
MARGE_BAIX = 0.75
AMPLE = A4[0] - 2 * MARGE_X

TINTA = '#1a1a1a'
BLAU = '#0d2f8f'
GRIS = '#5a5a5a'
VERD = '#0a6b2e'
VERMELL = '#a11'
FONS_BOX = '#eef2fb'
FONS_AVIS = '#fff4e0'
FONS_CODI = '#f4f4f2'

MONO = 'DejaVu Sans Mono'
SANS = 'DejaVu Sans'

# Cache de anchos. matplotlib no ajusta lineas, asi que hay que hacerlo aqui,
# y estimar "tantos caracteres por linea" no vale: con una tipografia
# proporcional una linea de emes se sale y una de eles deja medio folio en
# blanco. Se mide el texto de verdad con el renderer, que es exacto y ademas
# permite comprobarlo despues sobre el PDF ya escrito.
_ANCHOS = {}


def ample_text(txt, mida, negreta=False):
    """Ancho de `txt` en pulgadas, medido con el renderer de matplotlib."""
    clau = (txt, mida, negreta)
    if clau not in _ANCHOS:
        fig = plt.figure(figsize=(1, 1))
        t = fig.text(0, 0, txt, fontsize=mida, family=SANS,
                     weight='bold' if negreta else 'normal')
        r = fig.canvas.get_renderer()
        _ANCHOS[clau] = t.get_window_extent(renderer=r).width / fig.dpi
        plt.close(fig)
    return _ANCHOS[clau]


def talla(txt, mida, ample, negreta=False):
    """Parte `txt` en lineas que caben en `ample` pulgadas."""
    out, linia = [], ''
    for mot in txt.split():
        prova = (linia + ' ' + mot).strip()
        if linia and ample_text(prova, mida, negreta) > ample:
            out.append(linia)
            linia = mot
        else:
            linia = prova
    if linia:
        out.append(linia)
    return out or ['']


class Guia(object):
    """Flujo vertical de una columna, con salto de pagina automatico."""

    def __init__(self, pdf):
        self.pdf = pdf
        self.fig = None
        self.y = 0.0
        self.pagina = 0
        self.peu = True
        self._nova()

    # -- infraestructura ------------------------------------------------
    def _nova(self, peu=True):
        if self.fig is not None:
            self._peu()
            if PNG:
                self.fig.savefig(
                    os.path.join(IMG, 'pag%02d.png' % self.pagina), dpi=110)
            self.pdf.savefig(self.fig)
            plt.close(self.fig)
        self.fig = plt.figure(figsize=A4)
        self.pagina += 1
        self.peu = peu
        self.y = A4[1] - MARGE_DALT

    def _peu(self):
        if not self.peu or self.pagina == 1:
            return
        # fig.text va en FRACCION de figura, no en pulgadas: con las
        # pulgadas el numero de pagina se iba a 3800 pt del papel.
        y = (MARGE_BAIX - 0.30) / A4[1]
        self.fig.text(self._fx(MARGE_X), y,
                      'TAULES - guia per a Termodinamica', fontsize=7,
                      color=GRIS, family=SANS, va='top')
        self.fig.text(self._fx(A4[0] - MARGE_X), y, str(self.pagina),
                      fontsize=7, color=GRIS, ha='right', family=SANS, va='top')

    def _cap(self, alt):
        """Salta de pagina si lo que viene no cabe."""
        if self.y - alt < MARGE_BAIX:
            self._nova()
            return True
        return False

    def _fy(self, dy=0.0):
        return (self.y + dy) / A4[1]

    def _fx(self, x):
        return x / A4[0]

    # -- bloques --------------------------------------------------------
    def salt(self, h=0.12):
        self.y -= h

    def bloc(self, alt):
        """Reserva `alt` pulgadas: si no caben, salta de pagina ANTES.

        El flujo automatico rompe donde toca linea a linea, y eso parte un
        titulo de su imagen y deja la pagina siguiente con cuatro renglones.
        Donde un titulo, su parrafo y su captura son una sola cosa, se dice
        cuanto ocupan y se mueven juntos.
        """
        self._cap(alt)

    def portada(self, titol, sub, linies):
        self.y = A4[1] - 2.7
        self.fig.text(0.5, self._fy(), titol, fontsize=30, color=BLAU,
                      ha='center', family=SANS, weight='bold', va='top')
        self.y -= 0.55
        self.fig.text(0.5, self._fy(), sub, fontsize=14, color=TINTA,
                      ha='center', family=SANS, va='top')
        self.y -= 0.75
        for l in linies:
            self.fig.text(0.5, self._fy(), l, fontsize=10.5, color=GRIS,
                          ha='center', family=SANS, va='top')
            self.y -= 0.26

    def h1(self, txt, trenca=True):
        """Titol de seccio. Amb `trenca=False` NO obre pagina nova: segueix
        on sigui si hi cap, que es l'unica manera de posar dues seccions
        curtes al mateix full."""
        if trenca:
            self._nova()
        else:
            self._cap(2.6)
            self.y -= 0.22
        self.fig.text(self._fx(MARGE_X), self._fy(), txt, fontsize=21,
                      color=BLAU, family=SANS, weight='bold', va='top')
        # con va='top' el titulo ocupa hacia ABAJO: la regla va por debajo de
        # su alto, no a 0.10 del cursor, o le cruza el texto por la mitad
        self.y -= 0.36
        self.fig.add_artist(plt.Line2D(
            [self._fx(MARGE_X), self._fx(A4[0] - MARGE_X)],
            [self._fy(), self._fy()], color=BLAU, lw=1.2))
        self.y -= 0.28

    def _titol(self, txt, mida, color, davant, abans, despres):
        """Un titulo, ajustado a linea igual que un parrafo.

        Los titulos tambien se salen: uno largo se pintaba fuera del margen
        derecho sin dar ningun error, y lo caza la prueba del PDF, no la
        vista. Ajustarlos cuesta lo mismo que no hacerlo.
        """
        linies = talla(txt, mida, AMPLE, negreta=True)
        self._cap(davant + (len(linies) - 1) * mida * 0.020)
        self.y -= abans
        for l in linies:
            self.fig.text(self._fx(MARGE_X), self._fy(), l, fontsize=mida,
                          color=color, family=SANS, weight='bold', va='top')
            self.y -= mida * 0.020
        self.y -= despres

    def h2(self, txt):
        # se mira 2 pulgadas por delante: un titulo que cabe justo al pie
        # deja la seccion partida y la pagina siguiente con cuatro lineas
        self._titol(txt, 13.5, BLAU, 2.0, 0.12, 0.03)

    def h3(self, txt):
        self._titol(txt, 11, TINTA, 1.4, 0.06, 0.03)

    def par(self, txt, mida=10, color=None, sagnat=0.0):
        """Un parrafo. El ajuste de linea se hace aqui: matplotlib no lo hace."""
        color = color or TINTA
        for l in talla(txt, mida, AMPLE - sagnat):
            self._cap(0.22)
            self.fig.text(self._fx(MARGE_X + sagnat), self._fy(), l,
                          fontsize=mida, color=color, family=SANS, va='top')
            self.y -= mida * 0.0195
        self.y -= 0.09

    def punts(self, items, mida=10):
        for it in items:
            trossos = talla(it, mida, AMPLE - 0.28)
            for i, l in enumerate(trossos):
                self._cap(0.22)
                if i == 0:
                    self.fig.text(self._fx(MARGE_X + 0.06), self._fy(), '•',
                                  fontsize=mida, color=BLAU, family=SANS, va='top')
                self.fig.text(self._fx(MARGE_X + 0.28), self._fy(), l,
                              fontsize=mida, color=TINTA, family=SANS, va='top')
                self.y -= mida * 0.0195
            self.y -= 0.05
        self.y -= 0.06

    def codi(self, linies, mida=9):
        alt = len(linies) * mida * 0.0175 + 0.20
        self.y -= 0.06
        self._cap(alt)
        self.fig.patches.append(plt.Rectangle(
            (self._fx(MARGE_X), self._fy(-alt)),
            AMPLE / A4[0], alt / A4[1],
            facecolor=FONS_CODI, edgecolor='#dcdcd8', lw=0.8,
            transform=self.fig.transFigure, zorder=0))
        self.y -= 0.10
        for l in linies:
            self.fig.text(self._fx(MARGE_X + 0.12), self._fy(), l,
                          fontsize=mida, color=TINTA, family=MONO, va='top')
            self.y -= mida * 0.0175
        self.y -= 0.16

    def avis(self, titol, txt, fons=FONS_AVIS, vora='#e0b060', mida=9.5):
        linies = talla(txt, mida, AMPLE - 0.36)
        alt = len(linies) * mida * 0.0195 + 0.42
        self.y -= 0.08
        self._cap(alt)
        self.fig.patches.append(plt.Rectangle(
            (self._fx(MARGE_X), self._fy(-alt)),
            AMPLE / A4[0], alt / A4[1],
            facecolor=fons, edgecolor=vora, lw=1.0,
            transform=self.fig.transFigure, zorder=0))
        self.y -= 0.16
        self.fig.text(self._fx(MARGE_X + 0.16), self._fy(), titol,
                      fontsize=mida, color=TINTA, family=SANS, weight='bold', va='top')
        self.y -= 0.21
        for l in linies:
            self.fig.text(self._fx(MARGE_X + 0.16), self._fy(), l,
                          fontsize=mida, color=TINTA, family=SANS, va='top')
            self.y -= mida * 0.0195
        self.y -= 0.20

    def imatge(self, ruta, ample=3.5, peu=None, x=None):
        """Una pantalla. Alto = ancho * 240/320 mas el marco."""
        alt = ample * (240.0 + 4) / (320.0 + 4)
        self._cap(alt + (0.30 if peu else 0.12))
        x = MARGE_X + (AMPLE - ample) / 2.0 if x is None else x
        ax = self.fig.add_axes([self._fx(x), self._fy(-alt),
                                ample / A4[0], alt / A4[1]])
        ax.imshow(mpimg.imread(ruta))
        ax.axis('off')
        self.y -= alt + 0.06
        if peu:
            self.fig.text(0.5, self._fy(), peu, fontsize=8.5, color=GRIS,
                          ha='center', family=SANS, style='italic', va='top')
            self.y -= 0.22
        self.y -= 0.08

    def imatges2(self, r1, r2, ample=2.60, peu=None):
        """Dos pantallas lado a lado: formulario y resultado."""
        alt = ample * 244.0 / 324.0
        self._cap(alt + (0.32 if peu else 0.14))
        hueco = 0.22
        x0 = MARGE_X + (AMPLE - 2 * ample - hueco) / 2.0
        for i, r in enumerate((r1, r2)):
            ax = self.fig.add_axes([self._fx(x0 + i * (ample + hueco)),
                                    self._fy(-alt), ample / A4[0],
                                    alt / A4[1]])
            ax.imshow(mpimg.imread(r))
            ax.axis('off')
        self.y -= alt + 0.06
        if peu:
            self.fig.text(0.5, self._fy(), peu, fontsize=8.5, color=GRIS,
                          ha='center', family=SANS, style='italic', va='top')
            self.y -= 0.22
        self.y -= 0.08

    def taula(self, capcalera, files, amples, mida=9):
        alt = (len(files) + 1) * mida * 0.0215 + 0.14
        self._cap(alt)
        xs = [MARGE_X]
        for a in amples[:-1]:
            xs.append(xs[-1] + a * AMPLE)
        self.fig.patches.append(plt.Rectangle(
            (self._fx(MARGE_X), self._fy(-0.04)), AMPLE / A4[0],
            (mida * 0.0215 + 0.02) / A4[1], facecolor=FONS_BOX,
            edgecolor='none', transform=self.fig.transFigure, zorder=0))
        for x, c in zip(xs, capcalera):
            self.fig.text(self._fx(x + 0.06), self._fy(), c, fontsize=mida,
                          color=BLAU, family=SANS, weight='bold', va='top')
        self.y -= mida * 0.0215 + 0.04
        for fila in files:
            self._cap(0.2)
            for x, c in zip(xs, fila):
                self.fig.text(self._fx(x + 0.06), self._fy(), c,
                              fontsize=mida, color=TINTA, family=SANS, va='top')
            self.y -= mida * 0.0215
        self.y -= 0.16

    def tanca(self):
        self._peu()
        if PNG:
            self.fig.savefig(os.path.join(IMG, 'pag%02d.png' % self.pagina),
                             dpi=110)
        self.pdf.savefig(self.fig)
        plt.close(self.fig)


# ===================================================================
# Las pantallas que ilustran la guia. Cada una se dibuja con los motores.
# ===================================================================
def fes_imatges():
    # Es buida primer: si no, les pantalles d'una versio anterior es queden al
    # directori i costa de veure quines son les d'ara. Ja va passar amb un
    # formulari que havia canviat i seguia alli, amb data de dos dies abans.
    if os.path.isdir(IMG):
        for n in os.listdir(IMG):
            if n.endswith('.png'):
                os.remove(os.path.join(IMG, n))
    else:
        os.makedirs(IMG)
    f = {}

    def g(nom, p):
        r = os.path.join(IMG, nom + '.png')
        p.guarda(r)
        f[nom] = r

    g('menu', PA.menu())

    # --- exemple 1: caldera, 08/04/2026 q2. Les dues puntes de la mateixa
    #     isobara: liquid comprimit i vapor sobreescalfat.
    g('e1_form', PA.taules_form('R-718 (Aigua)', 'P [MPa]', '1.6',
                                'T [C]', '50'))
    # --- avis taronja i error
    g('t4_res', PA.taules_res('AIGUA', 'PT', 0.15, 115.0))
    g('t5_err', PA.taules_error('fora de rang'))

    # --- generalitzats
    g('g_const', PA.gener_const(305.3, 4.87, 0.099))
    g('g_cp', PA.gener_cp(43, 0))
    et2 = PA.E.get('ETILE')
    g('g5_form', PA.gener_form(et2['Tc_K'], et2['Pc_MPa'], et2['omega'],
                               197.7, 6.05, sust=et2['name']))
    g('g1_form', PA.gener_form(305.3, 4.87, 0.099, 793.78, 14.61))
    # el desplegable: etile es a taules i l'examen no dona constants
    et = PA.E.get('ETILE')
    g('g5_res', PA.gener_res(et['Tc_K'], et['Pc_MPa'], et['omega'],
                             197.7, 6.05, mm=et['molar_mass'],
                             sust=et['name']))
    g('g1_res', PA.gener_res(305.3, 4.87, 0.099, 793.78, 14.61))
    g('g2_const', PA.gener_const(1, 1, 0.099))
    g('g2_form', PA.gener_form(1, 1, 0.099, 2.6, 3))
    # diposit rigid: 28/10/2025
    vv = 0.012 / 144.3
    g('g3_form', PA.gener_form(300, 7.5, 0, 345, 0, v=vv))
    g('g3_res', PA.gener_res(300, 7.5, 0, 345, 0, vv))
    g('g4_res', PA.gener_res(300, 5, 0, 270, 0, 7.4826e-05))

    # --- discrepancia
    g('p1_form', PA.proc_form(300, 5, 0.089, 300, 5, 390, 25))
    g('p1_res', PA.proc_res(300., 5., 0.089, 43., 300., 5., 390., 25.,
                            mm=120.))
    g('p2_res', PA.proc_res(280., 5., 0.09, 0., 308., 10., 308., 5.))
    return f


# ===================================================================
def main():
    """El text viu a tools/guia_text.py; aqui nomes la maquetacio."""
    f = fes_imatges()
    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    pdf = PdfPages(OUT)
    g = Guia(pdf)
    for seccio in T.SECCIONS:
        seccio(g, f)
    g.tanca()
    d = pdf.infodict()
    d['Title'] = 'TAULES - guia per a Termodinamica'
    d['Subject'] = "Us de l'app de taules termodinamiques per a HP Prime G2"
    pdf.close()
    print('escrito %s (%d paginas)' % (os.path.relpath(OUT, ROOT), g.pagina))
    return 0


if __name__ == '__main__':
    sys.exit(main())
