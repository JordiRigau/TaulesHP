# -*- coding: utf-8 -*-
"""Carga master.json y lo normaliza a una estructura uniforme.

Unifica sustancias puras y mezclas zeotropicas: la mezcla tiene deslizamiento
de temperatura (presion de burbuja != presion de rocio), y la sustancia pura
es simplemente el caso de deslizamiento nulo. Asi el resto del codigo no
necesita dos caminos distintos.
"""
from __future__ import unicode_literals
import io, json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, 'data', 'master.json')

PROPS = ['v', 'u', 'h', 's']


def slug(name):
    """'R-718 (Aigua)' -> 'AIGUA' ; 'Metà' -> 'META' (ASCII, para la Prime)."""
    m = re.search(r'\(([^)]+)\)', name)
    base = m.group(1) if m else name
    base = unicodedata.normalize('NFKD', base)
    base = ''.join(c for c in base if not unicodedata.combining(c))
    return re.sub(r'[^A-Za-z0-9]', '', base).upper()


def _row_to_dict(cols, row):
    return dict(zip(cols, row))


dedup_log = []


def _dedup(rows, label):
    """Elimina filas repetidas identicas, conservando los pares de saturacion.

    El PDF reimprime algunas filas: en las isobaras de 0,50 y 0,60 MPa del
    amoniaco, las filas de 300, 310 y 320 C aparecen dos veces. Una T repetida
    con valores DISTINTOS si es legitima (liquido y vapor saturados a la misma
    T), asi que solo se descarta la fila que coincide en todos los campos.
    Dejarlas pasaria intervalos de anchura cero al interpolador.
    """
    out = []
    for r in rows:
        if out and out[-1] == r:
            dedup_log.append(label)
            continue
        out.append(r)
    return out


def load(path=MASTER):
    doc = json.load(io.open(path, encoding='utf-8'))
    out = []
    for s in doc['substances']:
        cr = s['critical']
        sub = {
            'name': s['name'],
            'key': slug(s['name']),
            'molar_mass': s['molar_mass_g_mol'],
            'Tc_K': cr.get('Tc_K'), 'Pc_MPa': cr.get('Pc_MPa'),
            'vc': cr.get('vc_m3kg'), 'omega': cr.get('omega'),
            'blend': False,
            'T_unit': None,
            'sat_by_T': [], 'sat_by_P': [], 'isobars': [],
        }
        units = set()

        t = s['sat_T']
        if t:
            units.add(t['T_unit'])
            cols = t['columns']
            sub['blend'] = 'Pl' in cols
            for r in t['rows']:
                d = _row_to_dict(cols, r)
                P = d.get('dep')
                row = {'T': d['idx'],
                       'Pl': d.get('Pl', P), 'Pv': d.get('Pv', P)}
                for p in PROPS:
                    row[p + 'l'] = d[p + 'l']
                    row[p + 'v'] = d[p + 'v']
                sub['sat_by_T'].append(row)
            sub['sat_by_T'].sort(key=lambda r: r['T'])
            sub['sat_by_T'] = _dedup(sub['sat_by_T'], '%s sat(T)' % sub['name'])

        t = s['sat_P']
        if t:
            units.add(t['T_unit'])
            cols = t['columns']
            for r in t['rows']:
                d = _row_to_dict(cols, r)
                T = d.get('dep')
                row = {'P': d['idx'],
                       'Tl': d.get('Tl', T), 'Tv': d.get('Tv', T)}
                for p in PROPS:
                    row[p + 'l'] = d[p + 'l']
                    row[p + 'v'] = d[p + 'v']
                sub['sat_by_P'].append(row)
            sub['sat_by_P'].sort(key=lambda r: r['P'])
            sub['sat_by_P'] = _dedup(sub['sat_by_P'], '%s sat(P)' % sub['name'])

        for b in s['isobars']:
            units.add(b['T_unit'])
            rows = [dict(zip(b['columns'], r)) for r in b['rows']]
            rows.sort(key=lambda r: r['T'])
            rows = _dedup(rows, '%s isobara %s' % (sub['name'], b['P_MPa']))
            sub['isobars'].append({'P': b['P_MPa'], 'page': b['page'], 'rows': rows})
        sub['isobars'].sort(key=lambda b: b['P'])

        units.discard(None)
        sub['T_unit'] = units.pop() if len(units) == 1 else ('MIXTO:%s' % sorted(units))
        out.append(sub)
    return out


def to_K(sub, T):
    return T + 273.15 if sub['T_unit'] == 'C' else T


def interp(x, xs, ys):
    """Interpolacion lineal simple; None si x cae fuera del rango."""
    if x < xs[0] or x > xs[-1]:
        return None
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            if xs[i + 1] == xs[i]:
                return ys[i]
            f = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + f * (ys[i + 1] - ys[i])
    return ys[-1]
