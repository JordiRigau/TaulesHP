# -*- coding: utf-8 -*-
"""PDF -> data/master.json  (extraccion determinista, sin LLM).

El PDF 'Tablas_propiedades_individualizadas.pdf' es texto nativo con tablas
centradas por columna, asi que se extrae por geometria con fidelidad exacta.
Este script es la UNICA via de entrada de datos: master.json no se edita a mano.
"""
from __future__ import unicode_literals
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfplumber
from pdfcommon import (upright_words, group_rows, learn_anchors, assign_row,
                       is_num, parse_num, norm_dashes, xc)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, 'Tablas_propiedades_individualizadas.pdf')
OUT = os.path.join(ROOT, 'data', 'master.json')

SUBST_RE = re.compile(r'^B(\d+)\.\s*(.+?)\s*$')
MOLAR_RE = re.compile(r'Massa molar\s*=\s*([\d,]+)\s*g/mol')
# Los dos puntos son opcionales: en p65/p66 el PDF los omite ("R-507A Propietats...").
SAT_TITLE = re.compile(':?\\s*[Ss]aturació líquid\\s*[‐-]\\s*vapor')
SUP_TITLE = re.compile(':?\\s*Propietats de líquids subrefredats i vapors rescalfats')
ISOB_HDR = re.compile('Isòbara a ([\\d,]+) MPa')

ISO_COLS = ['T', 'v', 'u', 'h', 's']
PROP_LETTERS = set('TPvuhs')


def sat_columns(letters):
    """Deriva los nombres de columna de la fila de cabecera.

    Sustancias puras   : 'T P v v u u h h s s'    (10 columnas)
    Mezclas zeotropicas: 'T P P v v u u h h s s'  (11 columnas: presion de
    burbuja y de rocio, porque tienen deslizamiento de temperatura).
    Regla: la 1a letra es el indice; despues, las letras repetidas
    consecutivamente forman el par (liquido, vapor) y las sueltas van solas.
    """
    names = ['idx']
    pairs = []
    i = 1
    while i < len(letters):
        L = letters[i]
        if i + 1 < len(letters) and letters[i + 1] == L:
            pairs.append((len(names), len(names) + 1))
            names += [L + 'l', L + 'v']
            i += 2
        else:
            names.append('dep')
            i += 1
    return names, pairs

warnings = []


def warn(msg):
    warnings.append(msg)


def row_text(r):
    return ' '.join(w['text'] for w in r)


def find_units_row(rows, y0, y1, x0, x1):
    """Localiza la fila de unidades (la que contiene 'kJ/(kg') del bloque."""
    best = None
    for r in rows:
        t = r[0]['top']
        if not (y0 <= t <= y1):
            continue
        inb = [w for w in r if x0 <= xc(w) <= x1]
        if not inb:
            continue
        if 'kJ/(kg' in ' '.join(w['text'] for w in inb):
            best = (t, inb)
    return best


def temp_unit(units_tokens):
    """Devuelve 'C' o 'K' leyendo la fila de unidades del bloque.

    El PDF escribe el grado de tres formas distintas segun la pagina:
    '⁰C' (U+2070) como un token, 'ºC', y 'o' 'C' partido en dos tokens.
    Por eso se compara sobre la cadena sin espacios.
    """
    flat = ''.join(w['text'] for w in units_tokens)
    if '⁰C' in flat or 'ºC' in flat or '°C' in flat or 'oC' in flat:
        return 'C'
    if any(w['text'] == 'K' for w in units_tokens):
        return 'K'
    return None


def numeric_in(rows, y0, y1, x0, x1):
    toks = []
    for r in rows:
        t = r[0]['top']
        if not (y0 < t <= y1):
            continue
        for w in r:
            if is_num(w['text']) and x0 <= xc(w) <= x1:
                toks.append(w)
    return toks


def _tol(anchors):
    gaps = [anchors[i + 1] - anchors[i] for i in range(len(anchors) - 1)]
    return min(min(gaps) / 2.0 - 0.5, 20.0)


def extract_block(rows, y0, y1, x0, x1, ncols, label, pairs=None):
    """Extrae un bloque tabular de ncols columnas usando anclas de columna.

    'pairs' son los pares de columnas (liquido, vapor) que el PDF fusiona en
    la fila del punto critico, donde imprime un solo valor centrado sobre las
    dos. Si la asignacion normal deja tokens sueltos, se reintenta contra las
    anclas fusionadas y el valor se duplica en ambas columnas (que es lo
    fisicamente correcto en el punto critico: v_l = v_v = v_c, etc.).
    """
    toks = numeric_in(rows, y0, y1, x0, x1)
    if len(toks) < ncols * 3:
        return []
    anchors = learn_anchors(toks, ncols)
    tol = _tol(anchors)
    manchors, mmap = None, None
    if pairs:
        keep = [i for i in range(ncols) if not any(i == b for a, b in pairs)]
        manchors = []
        mmap = []
        for i in keep:
            pr = [p for p in pairs if p[0] == i]
            if pr:
                a, b = pr[0]
                manchors.append((anchors[a] + anchors[b]) / 2.0)
                mmap.append((a, b))
            else:
                manchors.append(anchors[i])
                mmap.append((i,))
    out = []
    for r in rows:
        t = r[0]['top']
        if not (y0 < t <= y1):
            continue
        cells = [w for w in r if is_num(w['text']) and x0 <= xc(w) <= x1]
        if not cells:
            continue
        try:
            vals, dropped = assign_row(cells, anchors, tol=tol)
        except ValueError:
            vals, dropped = None, 1
        if dropped and manchors:
            try:
                mv, mdrop = assign_row(cells, manchors, tol=_tol(manchors))
            except ValueError:
                mv, mdrop = None, 1
            if mdrop == 0 and mv is not None and mv[0] is not None:
                vals = [None] * ncols
                for val, idxs in zip(mv, mmap):
                    for k in idxs:
                        vals[k] = val
                dropped = 0
        if vals is None:
            warn('%s: fila no asignable y=%.0f' % (label, t))
            continue
        # Sin valor en la columna indice no es una fila de datos: es ruido de
        # pagina (el numero de pagina del pie, marcas de agua...). Se descarta
        # en silencio; solo se avisa de tokens perdidos en filas que si valen.
        if vals[0] is None:
            continue
        if dropped:
            warn('%s: %d token(s) sin columna en y=%.0f' % (label, dropped, t))
        out.append(vals)
    return out


def main():
    pdf = pdfplumber.open(PDF)
    substances = []
    cur = None

    for pi, page in enumerate(pdf.pages):
        pno = pi + 1
        ws = upright_words(page)
        rows = group_rows(ws)
        texts = [row_text(r) for r in rows]

        # --- cabecera de sustancia -----------------------------------
        for txt in texts:
            m = SUBST_RE.match(txt.strip())
            if m:
                cur = {'id': int(m.group(1)),
                       'name': norm_dashes(m.group(2)).strip(),
                       'molar_mass_g_mol': None, 'critical': {},
                       'sat_T': None, 'sat_P': None, 'isobars': []}
                substances.append(cur)
            mm = MOLAR_RE.search(txt)
            if mm and cur and cur['molar_mass_g_mol'] is None:
                cur['molar_mass_g_mol'] = parse_num(mm.group(1))

        page_txt = '\n'.join(texts)
        is_sat = bool(SAT_TITLE.search(page_txt))
        # Red de seguridad: si la pagina tiene cabeceras de isobara, es de
        # sobrecalentado aunque el titulo no case (erratas del PDF).
        is_sup = bool(SUP_TITLE.search(page_txt)) or bool(ISOB_HDR.search(page_txt))

        # --- punto critico (bloque de cabecera de cada sustancia) -----
        if cur is not None and not cur['critical']:
            for i, txt in enumerate(texts):
                # Ojo: la fila de unidades de la tabla de saturacion empieza
                # igual ('K MPa m3/kg kJ/kg ...'), asi que hay que exigir que
                # la fila termine ahi. Ademas 'm3/kg' puede venir partido en
                # 'm' '3' '/kg' por el superindice.
                flat = txt.replace(' ', '')
                if flat in ('KMPam3/kg', 'KMPam³/kg') and i + 1 < len(rows):
                    nums = [parse_num(w['text']) for w in rows[i + 1]
                            if is_num(w['text'])]
                    if len(nums) >= 3:
                        cur['critical'] = {'Tc_K': nums[0], 'Pc_MPa': nums[1],
                                           'vc_m3kg': nums[2]}
                        if len(nums) >= 4:
                            cur['critical']['omega'] = nums[3]
                    break

        # --- tablas de saturacion ------------------------------------
        if is_sat and cur is not None:
            u = find_units_row(rows, 0, page.height, 0, page.width)
            if u is None:
                warn('p%d: sin fila de unidades en tabla de saturacion' % pno)
            else:
                uy, utok = u
                # La cabecera da el numero real de columnas: 10 en sustancias
                # puras, 11 en mezclas zeotropicas (dos presiones).
                hdr = None
                for r in rows:
                    if r[0]['top'] < uy:
                        tx = [w['text'] for w in r]
                        if (len(tx) >= 10 and tx[0] in 'TP'
                                and all(t in PROP_LETTERS for t in tx)):
                            hdr = tx
                if hdr is None:
                    warn('p%d: cabecera de saturacion no encontrada' % pno)
                else:
                    names, pairs = sat_columns(hdr)
                    data = extract_block(rows, uy + 1, page.height, 0, page.width,
                                         len(names), 'p%d sat' % pno, pairs=pairs)
                    key = 'sat_T' if hdr[0] == 'T' else 'sat_P'
                    tbl = cur[key]
                    if tbl is None:
                        tbl = cur[key] = {'index': hdr[0], 'T_unit': temp_unit(utok),
                                          'columns': names, 'rows': [], 'pages': []}
                    elif tbl['columns'] != names:
                        warn('p%d: columnas incoherentes %s vs %s'
                             % (pno, tbl['columns'], names))
                    tbl['rows'].extend(data)
                    tbl['pages'].append(pno)

        # --- tablas isobaras -----------------------------------------
        if is_sup and cur is not None:
            heads = []
            for r in rows:
                for j, w in enumerate(r):
                    if w['text'] == 'Isòbara':
                        m = ISOB_HDR.match(' '.join(x['text'] for x in r[j:j + 4]))
                        if m:
                            heads.append({'P': parse_num(m.group(1)),
                                          'x': w['x0'], 'y': r[0]['top']})
            if not heads:
                warn('p%d: pagina de isobaras sin cabeceras' % pno)
                continue
            ys = sorted(set(round(h['y'], 1) for h in heads))
            for h in heads:
                yi = ys.index(round(h['y'], 1))
                ybot = ys[yi + 1] - 2 if yi + 1 < len(ys) else page.height
                band = [g for g in heads if round(g['y'], 1) == round(h['y'], 1)]
                # El corte entre las dos isobaras de una fila NO es el punto medio
                # de sus titulos (eso parte la tabla izquierda): se deduce de las
                # propias columnas numericas, partiendo entre la 5a y la 6a.
                xsplit = page.width
                if len(band) == 2:
                    toks = numeric_in(rows, h['y'], ybot, 0, page.width)
                    try:
                        a = learn_anchors(toks, 10)
                        xsplit = (a[4] + a[5]) / 2.0
                    except ValueError:
                        xsplit = (min(g['x'] for g in band)
                                  + max(g['x'] for g in band)) / 2.0
                        warn('p%d y=%.0f: corte por titulos (fallback)' % (pno, h['y']))
                left = h['x'] < xsplit
                bx0, bx1 = (0, xsplit) if left else (xsplit, page.width)
                u = find_units_row(rows, h['y'], ybot, bx0, bx1)
                if u is None:
                    warn('p%d P=%s: sin fila de unidades' % (pno, h['P']))
                    continue
                uy, utok = u
                data = extract_block(rows, uy + 1, ybot, bx0, bx1, 5,
                                     'p%d P=%s' % (pno, h['P']))
                cur['isobars'].append({'P_MPa': h['P'], 'T_unit': temp_unit(utok),
                                       'columns': ISO_COLS, 'rows': data,
                                       'page': pno})

    for s in substances:
        s['isobars'].sort(key=lambda b: b['P_MPa'])

    doc = {
        'meta': {
            'source_pdf': os.path.basename(PDF),
            'generator': 'tools/extract_pdf.py',
            'note': 'Fuente unica de verdad. No editar a mano: regenerar con el script.',
            'units': {'P': 'MPa', 'v': 'm3/kg', 'u': 'kJ/kg', 'h': 'kJ/kg',
                      's': 'kJ/(kg K)', 'T': 'ver campo T_unit de cada tabla'},
        },
        'substances': substances,
        'warnings': warnings,
    }
    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=1))

    nv = 0
    for s in substances:
        for t in (s['sat_T'], s['sat_P']):
            if t:
                nv += sum(1 for r in t['rows'] for v in r if v is not None)
        for b in s['isobars']:
            nv += sum(1 for r in b['rows'] for v in r if v is not None)
    print('sustancias: %d' % len(substances))
    print('isobaras  : %d' % sum(len(s['isobars']) for s in substances))
    print('valores   : %d' % nv)
    print('avisos    : %d' % len(warnings))
    for w in warnings[:20]:
        print('   ! ' + w)


if __name__ == '__main__':
    main()
