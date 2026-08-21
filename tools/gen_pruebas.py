# -*- coding: utf-8 -*-
"""Genera docs/PRUEBAS_CALCULADORA.md desde el motor de referencia.

Se genera en vez de escribirse a mano por la misma razon que el bloque de
datos PPL: escrito a mano se cae una columna sin que nadie se entere (paso:
faltaba u en media tabla). Si cambia el motor o los datos, se regenera.
"""
from __future__ import unicode_literals
import io, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'PRUEBAS_CALCULADORA.md')

# (sust, indice_en_TSUBS, par, a, b, etiquetas de entrada, que comprueba)
CASOS = [
    ('R134A', 3, 'Px', 0.2, 1.0, 'P=0.2 · x=1',
     'vapor saturado: x=1 debe dar exactamente h_g'),
    ('R134A', 3, 'Px', 0.2, 0.0, 'P=0.2 · x=0',
     'líquido saturado: x=0 debe dar exactamente h_f'),
    ('R134A', 3, 'PT', 0.14, 20.0, 'P=0.14 · T=20',
     'isóbara tabulada: sobre un nodo debe devolver el valor de la tabla'),
    ('AIGUA', 1, 'PT', 3.0, 350.0, 'P=3 · T=350',
     'nodo exacto; la tabla publicada da h=3116,1'),
    ('AIGUA', 1, 'Ps', 0.075, 6.7449, 'P=0.075 · s=6.7449',
     '**inversa** por entropía, cae dentro de la campana'),
    ('AIGUA', 1, 'PT', 1.3, 375.0, 'P=1.3 · T=375',
     '**doble interpolación** (entre las isóbaras de 1,2 y 1,4 MPa)'),
    ('AIGUA', 1, 'Ph', 1.0, 500.0, 'P=1 · h=500',
     '**líquido comprimido** con datos reales del PDF, sin aproximar'),
    ('AIGUA', 1, 'PT', 0.15, 115.0, 'P=0.15 · T=115',
     '**fase cruzada**: la isóbara de 0,2 MPa da líquido a esa T → aviso'),
    ('AMONIAC', 2, 'Ph', 0.2, 1200.0, 'P=0.2 · h=1200',
     'bifásico por entalpía en otra sustancia'),
]

FUERA = [
    ('AIGUA', 1, 'PT', 1.0, 2000.0, 'P=1 · T=2000', 'T por encima de lo tabulado'),
    ('AIGUA', 1, 'Ph', 1.0, 99999.0, 'P=1 · h=99999', 'h imposible a esa presión'),
]


def etiqueta(st):
    """Region tal como debe verse en pantalla.

    El motor marca toda la campana como bifasica, tambien en los extremos.
    Es correcto para el calculo, pero en pantalla x=0 y x=1 son las fronteras
    y conviene decirlo con ese nombre.
    """
    if st['region'] == E.LIQUID:
        return 'LIQUID COMPRIMIT'
    if st['region'] == E.VAPOR:
        return 'VAPOR SOBREESCALFAT'
    x = st['x']
    if x is not None and x <= 1e-9:
        return 'LIQUID SATURAT'
    if x is not None and x >= 1 - 1e-9:
        return 'VAPOR SATURAT'
    return 'BIFASIC'


def sig(v, n):
    if v is None:
        return '--'
    return '%.*g' % (n, v)


def main():
    L = []
    L.append('# Batería de pruebas en la calculadora')
    L.append('')
    L.append('Generado por `tools/gen_pruebas.py` desde el motor de referencia.')
    L.append('**No editar a mano**: si cambian el motor o los datos, se regenera.')
    L.append('')
    L.append('Que compile no significa que calcule bien. Estos casos cubren **todas '
             'las rutas del motor**: cada región, la interpolación doble, la '
             'búsqueda inversa, la regla de la palanca, el caso de fase cruzada y '
             'el fallo fuera de rango.')
    L.append('')
    L.append('> **Antes de empezar**: ten la app instalada y comprueba que la '
             'sustancia del caso aparece en el desplegable. El montaje está en '
             'el README.')
    L.append('')
    L.append('En cada caso: ejecuta `TERMO()`, elige la sustancia, pon las dos '
             'magnitudes en los desplegables `Dada 1` / `Dada 2` y teclea sus '
             'valores. Los campos de valor son numéricos: el número se escribe '
             'directamente, sin comillas. El orden de las dos no importa.')
    L.append('')
    L.append('## Casos')
    L.append('')
    L.append('| # | Sust | Entrada | T | P | v | u | h | s | x | Región |')
    L.append('|---|---|---|---|---|---|---|---|---|---|---|')
    notas = []
    for i, (key, idx, pair, a, b, entrada, nota) in enumerate(CASOS, 1):
        sub = E.get(key)
        st = E.solve(sub, pair, a, b)
        u = 'K' if sub['T_unit'] == 'K' else 'C'
        L.append('| %d | %d %s | `%s` | %s %s | %s | %s | %s | %s | %s | %s | %s |'
                 % (i, idx, sub['name'], entrada,
                    ('%.2f' % st['T']), u,
                    sig(st['P'], 5), sig(st['v'], 6),
                    ('%.2f' % st['u']), ('%.2f' % st['h']), ('%.4f' % st['s']),
                    ('%.4f' % st['x']) if st['x'] is not None else '--',
                    etiqueta(st)))
        aviso = ' — **debe salir el aviso naranja**' if st['avisos'] else ''
        notas.append('%d. %s%s' % (i, nota, aviso))
    L.append('')
    L.append('## Fuera de rango — debe dar pantalla roja de ERROR, nunca un número')
    L.append('')
    L.append('| # | Sust | Entrada | Qué prueba |')
    L.append('|---|---|---|---|')
    for j, (key, idx, pair, a, b, entrada, nota) in enumerate(FUERA, len(CASOS) + 1):
        sub = E.get(key)
        try:
            E.solve(sub, pair, a, b)
            estado = 'AVISO: el motor NO falla, revisar'
        except Exception:
            estado = nota
        L.append('| %d | %d %s | `%s` | %s |' % (j, idx, sub['name'], entrada, estado))
    L.append('')
    L.append('## Qué mira cada caso')
    L.append('')
    L.extend(notas)
    L.append('')
    L.append('## Después')
    L.append('')
    w = E.get('AIGUA')
    s1 = E.state_PT(w, 3.0, 350.0)
    s2 = E.state_Py(w, 0.075, 's', s1['s'])
    L.append('Calcula el caso 4 y después el 5 (se guardan solos, sin pulsar '
             'nada) y ejecuta `TDELTA()`. Debe dar:')
    L.append('')
    L.append('```')
    for k, d, un in (('h', 2, 'kJ/kg'), ('u', 2, 'kJ/kg'), ('s', 4, 'kJ/kgK'),
                     ('v', 6, 'm3/kg'), ('T', 2, 'C'), ('P', 5, 'MPa')):
        L.append('d%s = %.*f %s' % (k, d, s2[k] - s1[k], un))
    L.append('```')
    L.append('')
    L.append('Es el trabajo de una turbina isentrópica de 3 MPa y 350 °C hasta '
             '75 kPa: **w = −Δh = %.2f kJ/kg**.' % (s1['h'] - s2['h']))
    L.append('')
    L.append('## Lo que aún falta')
    L.append('')
    L.append('**La prueba de aceptación de verdad**: 3-5 problemas ya resueltos de '
             'la asignatura, de principio a fin. Si no reproduce las soluciones '
             'oficiales, la app no sirve por muy verdes que estén estas pruebas.')

    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('escrito %s (%d casos + %d fuera de rango)'
          % (os.path.relpath(OUT, ROOT), len(CASOS), len(FUERA)))


if __name__ == '__main__':
    main()
