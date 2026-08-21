# -*- coding: utf-8 -*-
"""Genera el icono de la app: la campana de saturacion T-s del agua.

Convencion de la HP Prime, deducida de la app Gallery (que la lleva y
funciona): un fichero llamado icon.png de 73x74 px dentro de la carpeta
.hpappdir.

La curva NO es un dibujo: sale de data/master.json, de la misma tabla de
saturacion que usa la app. Se dibuja a 4x y se reduce, que es la unica forma
de que una curva quede suave a 73 px.

Uso:
    python tools/gen_icon.py          # genera las variantes en icon/
"""
from __future__ import unicode_literals
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import engine as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'icon')

W, H = 73, 74          # tamano que usa Gallery
SS = 8                 # supermuestreo


def dome_points():
    """Campana T-s del agua: rama liquida subiendo, rama vapor bajando."""
    sub = E.get('AIGUA')
    rows = sub['sat_by_T']
    izq = [(r['sl'], r['T']) for r in rows]
    der = [(r['sv'], r['T']) for r in rows]
    return izq + der[::-1]


def escala(pts, w, h, mx, my):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    out = []
    for s, t in pts:
        X = mx + (s - x0) / (x1 - x0) * (w - 2 * mx)
        Y = h - my - (t - y0) / (y1 - y0) * (h - 2 * my)
        out.append((X, Y))
    return out


def make(nombre, fondo, curva, relleno, ejes, punto):
    w, h = W * SS, H * SS
    img = Image.new('RGBA', (w, h), fondo)
    m = 10 * SS
    pts = escala(dome_points(), w, h, m, m)

    # El relleno translucido va en su propia capa: dibujar con un color que
    # lleva alfa NO lo mezcla, lo escribe tal cual.
    if relleno:
        capa = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(capa).polygon(pts, fill=relleno)
        img = Image.alpha_composite(img, capa)

    if ejes:
        capa = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        de = ImageDraw.Draw(capa)
        de.line([(m - 4 * SS, m - 5 * SS), (m - 4 * SS, h - m + 4 * SS)],
                fill=ejes, width=SS)
        de.line([(m - 4 * SS, h - m + 4 * SS), (w - m + 4 * SS, h - m + 4 * SS)],
                fill=ejes, width=SS)
        img = Image.alpha_composite(img, capa)

    d = ImageDraw.Draw(img)
    d.line(pts, fill=curva, width=2 * SS, joint='curve')

    if punto:
        # linea de union bifasica + el punto: es lo que distingue una campana
        # termodinamica de una curva cualquiera
        i = int(len(pts) * 0.22)
        j = len(pts) - 1 - int(len(pts) * 0.22)
        d.line([pts[i], pts[j]], fill=punto, width=SS)
        cx, cy = (pts[i][0] + pts[j][0]) / 2, (pts[i][1] + pts[j][1]) / 2
        r = 3 * SS
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=punto)

    img = img.resize((W, H), Image.LANCZOS)
    p = os.path.join(OUT, nombre)
    img.save(p)
    # vista ampliada, para poder juzgarlo en pantalla
    img.resize((W * 4, H * 4), Image.NEAREST).save(
        p.replace('.png', '_x4.png'))
    print('  %-22s %d x %d' % (nombre, W, H))


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    print('iconos en icon/  (campana T-s del agua, datos reales)')
    make('icon_blau.png',   (26, 58, 105, 255), (255, 255, 255, 255),
         (255, 255, 255, 38), (255, 255, 255, 90), (255, 190, 60, 255))
    make('icon_blanc.png',  (250, 250, 250, 255), (20, 60, 120, 255),
         (20, 60, 120, 28), (150, 150, 150, 255), (200, 70, 30, 255))
    make('icon_vermell.png', (150, 32, 32, 255), (255, 255, 255, 255),
         (255, 255, 255, 40), (255, 255, 255, 90), (255, 225, 120, 255))
    make('icon_net.png',    (26, 58, 105, 255), (255, 255, 255, 255),
         (255, 255, 255, 45), None, None)
    return 0


if __name__ == '__main__':
    sys.exit(main())
