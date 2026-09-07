# -*- coding: utf-8 -*-
"""Genera docs/PRUEBAS_CALCULADORA.md desde el motor de referencia.

Se genera en vez de escribirse a mano por la misma razon que el bloque de
datos PPL: escrito a mano se cae una columna sin que nadie se entere (paso:
faltaba u en media tabla). Si cambia el motor o los datos, se regenera.
"""
from __future__ import unicode_literals
import io, math, os, sys

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


def empate(v, n):
    """Si el valor cae justo en la mitad al redondear a n decimales.

    Esta tabla la formatea Python (`%.2f`) y la app imprime
    STRING(ROUND(x, n)). Son dos caminos, y en un empate exacto pueden dar
    distinto ultimo digito. No se sabe cual imprime la calculadora -- el
    interprete del kit redondea hacia arriba y Python no --, asi que lo unico
    honesto es senalar los casos donde puede bailar.
    """
    if v is None:
        return False
    f = 10.0 ** n
    arriba = math.floor(abs(v) * f + 0.5) / f * (1 if v >= 0 else -1)
    return float('%.*f' % (n, v)) != arriba


def empates(casos):
    """Los casos donde los dos redondeos discrepan, listados como texto."""
    fuera = []
    for i, (key, idx, pair, a, b, entrada, nota) in enumerate(casos, 1):
        st = E.solve(E.get(key), pair, a, b)
        cuales = [k for k, n in (('T', 2), ('u', 2), ('h', 2), ('s', 4))
                  if empate(st[k], n)]
        if cuales:
            fuera.append('el caso %d (`%s`)' % (i, '`, `'.join(cuales)))
    if not fuera:
        return ''
    if len(fuera) == 1:
        return fuera[0]
    return ', '.join(fuera[:-1]) + ' y ' + fuera[-1]


def bloque_generalizados():
    """Casos de las dos pantallas de metodos generalizados.

    Salen de tools/lk.py, igual que los de arriba salen de engine.py, y son
    preguntas reales de examen para que el numero que hay que ver en pantalla
    tenga con que compararse fuera del proyecto.
    """
    import lk
    L = ['', '## Métodos generalizados', '']
    L.append('Desde el menú, botón **2** (`GAS REAL`) y botón **3** '
             '(`PROCES REAL`). Las constantes del fluido se ponen una vez '
             'con `View` → *Constants del fluid* y se recuerdan; la cabecera '
             'de cada pantalla las repite, que es lo que evita arrastrar una '
             'Tc del problema anterior.')
    L.append('')
    L.append('**Botón 2 — un estado.** Tc, Pc y ω en *Constants*, luego T y P.')
    L.append('')
    L.append('| # | Constants | Entrada | Z⁰ | Z¹ | Z | (h−h\\*)/RTc | '
             '(s−s\\*)/R |')
    L.append('|---|---|---|---|---|---|---|---|')
    uno = [
        ('Tc=305.3 Pc=4.87 w=0.099', 793.78, 14.61),
        ('Tc=300 Pc=5 w=0.089', 300.0, 5.0),
        ('Tc=190 Pc=46 w=0', 209.0, 69.0),
    ]
    for i, (cte, t, p) in enumerate(uno, 1):
        tc = float(cte.split('Tc=')[1].split()[0])
        pc = float(cte.split('Pc=')[1].split()[0])
        w = float(cte.split('w=')[1].split()[0])
        g = lk.generalizado(t / tc, p / pc, w)
        L.append('| G%d | `%s` | `T=%g · P=%g` | %.4f | %.4f | %.4f | %.4f | '
                 '%.4f |' % (i, cte, t, p, g['z0'], g['z1'], g['z'],
                             g['dh'], g['ds']))
    L.append('')
    L.append('> El signo es el que dice la pantalla: **h−h\\***, real menos '
             'ideal, negativo. Si el apunte tabula (h\\*−h)/RTc, es el mismo '
             'número cambiado de signo.')
    L.append('')
    L.append('**Botón 3 — el proceso 1→2.** Añade `cp*` a las constantes.')
    L.append('')
    L.append('| # | Constants | Entrada | dh [J/mol] | ds [J/molK] | '
             'du [J/mol] |')
    L.append('|---|---|---|---|---|---|')
    dos = [
        ((190.0, 46.0, 0.0, 34.0), 209.0, 69.0, 228.0, 92.0),
        ((280.0, 5.0, 0.09, 0.0), 308.0, 10.0, 308.0, 5.0),
        ((300.0, 5.0, 0.089, 43.0), 300.0, 5.0, 390.0, 25.0),
    ]
    import math
    for i, ((tc, pc, w, cp), t1, p1, t2, p2) in enumerate(dos, 1):
        a = lk.estado_tp(tc, pc * 1e6, w, t1, p1 * 1e6)
        b = lk.estado_tp(tc, pc * 1e6, w, t2, p2 * 1e6)
        dh = cp * (t2 - t1) + b['dh_mol'] - a['dh_mol']
        ds = (cp * math.log(t2 / t1) - lk.R * math.log(p2 / p1)
              + b['ds_mol'] - a['ds_mol'])
        du = dh - lk.R * (b['z'] * t2 - a['z'] * t1)
        L.append('| D%d | `Tc=%g Pc=%g w=%g cp*=%g` | `T1=%g P1=%g · '
                 'T2=%g P2=%g` | %.1f | %.4f | %.1f |'
                 % (i, tc, pc, w, cp, t1, p1, t2, p2, dh, ds, du))
    L.append('')
    L.append('Los tres son preguntas de examen: **D1** es la 9 del 14/04/2023 '
             '(85 mol · du = 49 kJ oficiales), **D2** la 7 del 02/11/2021 '
             '(10 mol · ds = 173,9 J/K oficiales) y **D3** la 2 del '
             '09/04/2025 (difusor, 174,1 m/s oficiales).')
    L.append('')
    L.append('**El depósito rígido.** Si en vez de la presión conoces el '
             'volumen molar, escríbelo en `v` y deja la `P` como esté: con '
             '`v>0` la presión pasa a ser el resultado y sale en verde. Es la '
             'pregunta 1 del 28/10/2025:')
    L.append('')
    tc, pc, w, cp = 300.0, 7.5, 0.0, 37.4
    vv = 0.012 / 144.3
    a = lk.estado_tv(tc, pc * 1e6, w, 345.0, vv)
    b = lk.estado_tv(tc, pc * 1e6, w, 315.0, vv)
    L.append('| # | Constants | Entrada | P1 [MPa] | P2 [MPa] | dP [MPa] |')
    L.append('|---|---|---|---|---|---|')
    L.append('| R1 | `Tc=%g Pc=%g w=%g cp*=%g` | `T1=345 T2=315 · '
             'v1=v2=%.6g` | %.4f | %.4f | %.3f |'
             % (tc, pc, w, cp, vv, a['p'] / 1e6, b['p'] / 1e6,
                (b['p'] - a['p']) / 1e6))
    L.append('')
    L.append('La oficial es **−6 MPa**, que es la opción *a)*; el número '
             'exacto sale a %.2f porque la solución se leyó del gráfico.'
             % ((b['p'] - a['p']) / 1e6))
    L.append('')
    L.append('## Los generalizados fuera de rango')
    L.append('')
    L.append('Con `Tc=300 Pc=5 w=0`, botón 2 y `T=270 · v=7.4826e-5` — un '
             'volumen que cae **dentro de la campana** — la pantalla debe '
             'decir **Sense solucio**, nunca un número: ahí la ecuación de '
             'Lee-Kesler da presión negativa y no hay estado. Es el mismo '
             'criterio que las tablas, donde fuera de rango sale error '
             'visible en vez de una extrapolación silenciosa.')
    L.append('')
    L.append('> Por `(T, P)` este fallo no existe, porque Z = Pr·Vr/Tr sale '
             'positivo siempre. Sólo aparece dando el volumen.')
    return L


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
    L.append('En cada caso: teclea `TERMO` en Home, elige la sustancia, pon las '
             'dos magnitudes en los desplegables `Dada 1` / `Dada 2` y teclea sus '
             'valores. Los campos de valor son numéricos: el número se escribe '
             'directamente, sin comillas. El orden de las dos no importa.')
    L.append('')
    L.append('> **Sin paréntesis.** En Home una función sin argumentos se llama '
             'por su nombre: `TERMO()` responde *syntax error*, `TERMO` la '
             'ejecuta. Dentro del fuente PPL los paréntesis sí son correctos. '
             'Medido en una G2 con el firmware 2.4.15515.')
    L.append('')
    nota = ('> **Compara el valor, no el relleno.** Esta tabla la formatea '
            'Python (`%.2f`); la app imprime `STRING(ROUND(x, n))`, que es otro '
            'camino. Los ceros de la derecha pueden no salir: donde aquí pone '
            '`500.00`, en pantalla puede salir `500`. ')
    ties = empates(CASOS)
    if ties:
        nota += ('Y en un empate exacto el último dígito puede caer al otro '
                 'lado — aquí pasa en %s. ' % ties)
    nota += ('Cuál de los dos imprime la calculadora **no está medido**: si '
             'baila la última cifra, no es la instalación.')
    L.append(nota)
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
    L.append('## Los dos encadenados')
    L.append('')
    w = E.get('AIGUA')
    s1 = E.state_PT(w, 3.0, 350.0)
    s2 = E.state_Py(w, 0.075, 's', s1['s'])
    L.append('Los casos 4 y 5 son el mismo problema: una turbina isentrópica '
             'de 3 MPa y 350 °C hasta 75 kPa. Del 4 sacas s = %.4f, lo metes '
             'como segunda dato del 5, y el trabajo es la resta de las dos '
             'entalpías:' % s1['s'])
    L.append('')
    L.append('```')
    L.append('w = h1 - h2 = %.2f - %.2f = %.2f kJ/kg'
             % (s1['h'], s2['h'], s1['h'] - s2['h']))
    L.append('```')
    L.append('')
    L.append('Si te salen esos dos, la búsqueda inversa funciona, que es la '
             'ruta más larga del motor.')
    L.extend(bloque_generalizados())
    L.append('')
    L.append('## Y en el PC')
    L.append('')
    L.append('Estos casos comprueban que la calculadora hace lo mismo que el '
             'motor de referencia. Que el motor **acierte** lo decide '
             '`tests/test_aceptacion.py` para las tablas y '
             '`tests/test_lk_examenes.py` para los generalizados: los dos '
             'rehacen problemas ya resueltos de la asignatura contra su '
             'solución oficial.')

    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('escrito %s (%d casos + %d fuera de rango)'
          % (os.path.relpath(OUT, ROOT), len(CASOS), len(FUERA)))


if __name__ == '__main__':
    main()
