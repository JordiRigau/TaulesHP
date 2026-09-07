# -*- coding: utf-8 -*-
"""Comprueba que la guia del estudiante no ensena numeros que la app no da.

Las CAPTURAS de docs/GUIA_ESTUDIANT.pdf las dibuja tools/pantalla.py llamando
a los motores, asi que no pueden mentir. El texto de corregido es otra cosa:
frases como "el treball es w = 3116,06 - 2403,01 = 713,05 kJ/kg" llevan
numeros escritos a mano, y si algun dia cambia el motor se quedan viejos sin
que nada avise. Un estudiante haria el examen con ellos.

Asi que aqui se recorre el texto de la guia con un Guia de mentira que en vez
de dibujar apunta lo que se le manda, y se comprueba que cada cifra citada
sigue saliendo de engine.py o de lk.py.

    python tests/test_guia.py
"""
from __future__ import unicode_literals
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import engine as E
import lk

PASS, FAIL = [], []


def note(ok, msg):
    (PASS if ok else FAIL).append(msg)


class GuiaFalsa(object):
    """La misma API que tools/gen_guia.py:Guia, pero apuntando en vez de
    pintar. Cualquier metodo que no este aqui saldria como AttributeError, que
    es lo que se quiere: si la guia crece, esto se entera."""

    def __init__(self):
        self.text = []
        self.imatges = []
        self.y = 0.0

    def _add(self, *xs):
        for x in xs:
            if isinstance(x, (list, tuple)):
                self._add(*x)
            elif x is not None and not isinstance(x, (int, float)):
                self.text.append(x)

    def portada(self, titol, sub, linies):
        self._add(titol, sub, linies)

    def h1(self, t, trenca=True):
        self._add(t)

    def h2(self, t):
        self._add(t)

    h3 = h2

    def par(self, t, mida=10, color=None, sagnat=0.0):
        self._add(t)

    def punts(self, items, mida=10):
        self._add(items)

    def codi(self, linies, mida=9):
        self._add(linies)

    def avis(self, titol, txt, fons=None, vora=None, mida=9.5):
        self._add(titol, txt)

    def taula(self, capcalera, files, amples, mida=9):
        self._add(capcalera, files)

    def imatge(self, ruta, ample=3.5, peu=None, x=None):
        self.imatges.append(ruta)
        self._add(peu)

    def imatges2(self, r1, r2, ample=2.85, peu=None):
        self.imatges += [r1, r2]
        self._add(peu)

    def salt(self, h=0.12):
        pass

    def bloc(self, alt):
        pass


def recull():
    """Todo el texto de la guia, en una sola cadena normalizada.

    La prosa catalana usa coma decimal ("713,05") y las tablas y capturas
    usan punto ("h = 3116.06"). Se pasa todo a punto para poder comparar una
    sola vez con lo que dan los motores.
    """
    import guia_text as T
    g = GuiaFalsa()
    fals = _FitxersFalsos()
    for seccio in T.SECCIONS:
        seccio(g, fals)
    s = ' '.join(g.text)
    # coma decimal -> punto, y los signos menos tipograficos -> ASCII
    out = []
    for i, c in enumerate(s):
        if c == ',' and i and s[i - 1].isdigit() and i + 1 < len(s) \
                and s[i + 1].isdigit():
            out.append('.')
        elif c in u'−–—':
            out.append('-')
        else:
            out.append(c)
    return ''.join(out), g


class _FitxersFalsos(dict):
    """Cualquier nombre de captura devuelve su ruta, exista o no: aqui no se
    dibuja nada, solo se recorre el texto."""

    def __missing__(self, k):
        return os.path.join(ROOT, 'docs', 'guia', 'img', k + '.png')


def comprova(txt, etiqueta, valor, fmt='%.2f', cops=1):
    """Que `valor`, formateado, aparezca `cops` veces en el texto.

    Se cuenta, no se busca. Con "esta o no esta" la prueba no sirve: varias
    cifras salen dos veces -en la frase y en el pie de la captura- y tocar una
    sola dejaba la prueba en verde. Comprobado torciendo un numero a proposito.

    Que el numero de apariciones sea parte de la prueba tiene un efecto
    secundario que interesa: anadir una mencion nueva la rompe, y obliga a
    mirar si esa mencion tambien deberia venir del motor.
    """
    esperat = fmt % valor
    n = txt.count(esperat)
    note(n == cops,
         '%-42s %s hauria de sortir %d cop(s) i en surt %d'
         % (etiqueta, esperat, cops, n))


def main():
    txt, g = recull()

    # ---- pantalla 1: les taules -------------------------------------
    # La seccio del boto 1 explica com es fa servir la pantalla i no resol
    # cap problema, aixi que no escriu cap xifra a la prosa: les uniques que
    # hi surten son dins de les captures, i aquelles les calcula el motor a
    # tools/pantalla.py. Nomes queden els dos numeros del full de ruta, que
    # son els que serveixen per comprovar la instal.lacio.
    w = E.get('AIGUA')
    inst = E.state_PT(w, 3.0, 350.0)
    comprova(txt, 'full de ruta: h', inst['h'])
    comprova(txt, 'full de ruta: s', inst['s'], '%.4f')

    # ---- pantalla 2: generalitzats ----------------------------------
    gg = lk.generalizado(793.78 / 305.3, 14.61 / 4.87, 0.099)
    comprova(txt, 'turbina de gas: Z', gg['z'], '%.4f')
    vv = 0.012 / 144.3
    r1 = lk.estado_tv(300.0, 7.5e6, 0.0, 345.0, vv)
    r2 = lk.estado_tv(300.0, 7.5e6, 0.0, 315.0, vv)
    comprova(txt, 'diposit rigid: P a 345 K', r1['p'] / 1e6, '%.4f')
    comprova(txt, 'diposit rigid: P a 315 K', r2['p'] / 1e6, '%.4f')
    comprova(txt, 'diposit rigid: caiguda de pressio',
             (r2['p'] - r1['p']) / 1e6, '%.2f')

    # ---- pantalla 3: discrepancia -----------------------------------
    d1 = lk.estado_tp(300.0, 5e6, 0.089, 300.0, 5e6)
    d2 = lk.estado_tp(300.0, 5e6, 0.089, 390.0, 25e6)
    dh = 43.0 * 90 + d2['dh_mol'] - d1['dh_mol']
    comprova(txt, 'difusor: dh per kg', dh / 120.0, '%.3f')
    comprova(txt, 'difusor: velocitat de sortida',
             math.sqrt(300.0 ** 2 - 2 * dh / 0.120), '%.1f')
    e1 = lk.estado_tp(280.0, 5e6, 0.09, 308.0, 10e6)
    e2 = lk.estado_tp(280.0, 5e6, 0.09, 308.0, 5e6)
    ds = -lk.R * math.log(0.5) + e2['ds_mol'] - e1['ds_mol']
    comprova(txt, 'isoterm: ds molar', ds, '%.4f', cops=2)
    comprova(txt, 'isoterm: q = T*ds', 308.0 * ds, '%.1f', cops=2)
    comprova(txt, 'isoterm: dS univers de 10 mol', 10 * ds, '%.1f')
    comprova(txt, 'isoterm: W electric de 10 mol',
             10 * 308.0 * ds / 1000.0, '%.2f')

    # ---- que cap captura citada falti -------------------------------
    falten = [r for r in g.imatges if not os.path.isfile(r)]
    note(not falten,
         'captures que la guia cita i no existeixen: %s'
         % ', '.join(os.path.basename(r) for r in falten[:5]))

    # ---- i que el PDF estigui fet i sense text fora del marge -------
    pdf = os.path.join(ROOT, 'docs', 'GUIA_ESTUDIANT.pdf')
    if not os.path.isfile(pdf):
        note(False, 'falta docs/GUIA_ESTUDIANT.pdf: python tools/gen_guia.py')
    else:
        note(True, 'docs/GUIA_ESTUDIANT.pdf existeix')
        try:
            import pdfplumber
        except ImportError:
            print('  (sense pdfplumber: no es mira el marge dret)')
        else:
            lim = (8.27 - 0.85) * 72 + 1.5
            fora = []
            with pdfplumber.open(pdf) as doc:
                for i, pg in enumerate(doc.pages):
                    fora += [(i + 1, x['text']) for x in pg.extract_words()
                             if x['x1'] > lim]
            note(not fora,
                 'text que se surt del marge dret: %s'
                 % '; '.join('p%d %s' % f for f in fora[:5]))

    for l in FAIL:
        print('  FALLA ' + l)
    print('-' * 70)
    print('PASS: %d    FAIL: %d' % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
