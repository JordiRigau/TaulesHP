# -*- coding: utf-8 -*-
"""Utilidades compartidas para la extraccion del PDF de tablas termodinamicas.

El PDF es texto nativo (no escaneado), con tablas centradas por columna con
precision de 0.1 pt. Eso permite una extraccion 100% determinista por posicion,
sin LLM y sin heuristicas de conteo de tokens.
"""
from __future__ import unicode_literals
import re

# El PDF usa U+2010 (HYPHEN) para los signos negativos y en algunos exponentes,
# ademas del guion ASCII. Y coma decimal en todos los casos.
DASHES = ['\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2212']

NUM_RE = re.compile(
    '^[' + ''.join(DASHES) + r'\-]?\d+(?:,\d+)?(?:[eE][' + ''.join(DASHES) + r'\-\+]?\d+)?$'
)


def norm_dashes(s):
    for d in DASHES:
        s = s.replace(d, '-')
    return s


def is_num(tok):
    return bool(NUM_RE.match(tok))


def parse_num(tok):
    """'‐70,82' -> -70.82 ; '2,298E-12' -> 2.298e-12"""
    return float(norm_dashes(tok).replace(',', '.'))


def upright_words(page):
    """Palabras horizontales. Descarta el texto rotado del PDF, que es
    exactamente el de las etiquetas 'Vapor/Liquid' y 'sat.' de los margenes
    (verificado: son los unicos tokens con upright=False en todo el documento)."""
    ws = page.extract_words(use_text_flow=False, keep_blank_chars=False,
                            extra_attrs=['upright', 'size'])
    return [w for w in ws if w['upright']]


INT_TOK = re.compile(r'^[' + ''.join(DASHES) + r'\-]?\d+$')


def merge_fragments(row, max_gap_sign=4.0, max_gap_frac=1.0):
    """Recompone los numeros que el PDF parte en varias palabras.

    Dos averias reales del documento, ambas silenciosas si no se corrigen:

    a) Signo negativo suelto: '-' '50' en vez de '-50' (109 casos, 30 paginas).
       Sin arreglar, esos valores se leen como POSITIVOS.
    b) Parte decimal separada: '0' ',943324' en vez de '0,943324' (28 casos).
       Sin arreglar, el valor se lee como 0 y el resto se pierde.

    Ambas uniones exigen que los tokens se toquen (hueco <= 1 pt en el caso
    del decimal, <= 4 pt en el del signo) frente a los ~40 pt que separan
    columnas, asi que no pueden fusionar celdas distintas. La regla del signo
    exige ademas que el siguiente token sea numerico, para no tocar el guion
    de titulos como 'Saturacio liquid - vapor'.
    """
    out = []
    for w in row:
        if out:
            prev = out[-1]
            gap = w['x0'] - prev['x1']
            if (w['text'].startswith(',') and gap <= max_gap_frac
                    and INT_TOK.match(prev['text'])):
                prev['text'] += w['text']
                prev['x1'] = w['x1']
                continue
            if (prev['text'] in DASHES and gap <= max_gap_sign
                    and is_num(w['text'])):
                prev['text'] = '-' + w['text']
                prev['x1'] = w['x1']
                continue
        out.append(dict(w))
    return out


def group_rows(words, tol=2.5):
    """Agrupa palabras en filas por coordenada 'top'."""
    rows = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if rows and abs(w['top'] - rows[-1][0]['top']) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [merge_fragments(sorted(r, key=lambda w: w["x0"])) for r in rows]


def xc(w):
    return (w['x0'] + w['x1']) / 2.0


def learn_anchors(tokens, ncols, tol=3.0):
    """Deduce los centros de columna a partir de los propios datos.

    Las columnas del PDF estan centradas con desviacion < 0.2 pt, asi que un
    clustering 1D con tolerancia de 3 pt las separa sin ambiguedad.
    Devuelve los ncols centros con mas soporte, ordenados por x.
    """
    centers = sorted(xc(t) for t in tokens)
    clusters = []
    for c in centers:
        if clusters and c - clusters[-1][-1] <= tol:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    clusters.sort(key=len, reverse=True)
    best = clusters[:ncols]
    if len(best) < ncols:
        raise ValueError('solo %d columnas detectadas, se esperaban %d' % (len(best), ncols))
    return sorted(sum(c) / len(c) for c in best)


def assign_row(row, anchors, tol=8.0):
    """Coloca cada token numerico en su columna por cercania al centro.

    Devuelve (valores, descartados): una lista de longitud len(anchors) con
    None en las celdas vacias, y cuantos tokens quedaron sin colocar.
    'descartados' es lo que delata la fila del punto critico, donde el PDF
    centra cada valor sobre un par de columnas fusionadas.
    """
    out = [None] * len(anchors)
    dropped = 0
    for t in row:
        c = xc(t)
        d = [abs(c - a) for a in anchors]
        i = d.index(min(d))
        if d[i] > tol:
            dropped += 1
            continue
        if out[i] is not None:
            raise ValueError('colision en columna %d: %r vs %r' % (i, out[i], t['text']))
        out[i] = parse_num(t['text'])
    return out, dropped
