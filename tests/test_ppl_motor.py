# -*- coding: utf-8 -*-
"""Ejecuta el PPL de verdad y lo compara con el motor de referencia.

Los otros tres arneses no pueden ver esto. test_engine.py prueba el motor de
Python; test_ppl_layout.py prueba la ARITMETICA DE INDICES reimplementandola
en Python; test_aceptacion.py prueba que el motor de Python reproduce las
soluciones del profesor. Ninguno ejecuta ppl/TERMOLIB.hpprgm.

Y ahi cabe una clase entera de fallos: que el PPL y el Python calculen cosas
distintas. Cada uno es coherente consigo mismo, los dos pasan sus pruebas, y
la app da un resultado que el PC no da. Fue exactamente lo que paso con la
region supercritica: el arreglo entro en engine.py y en TPT, pero no en TPY,
y durante 30 isobaras de 6 sustancias la calculadora daba error donde el PC
daba un numero.

Necesita el interprete de PPL de hp-prime-kit:

    https://github.com/JordiRigau/hp-prime-kit

Si no esta instalado, la prueba se SALTA en vez de fallar: el repositorio
sigue siendo autocontenido con sus tres arneses.

    python tests/test_ppl_motor.py
"""
from __future__ import unicode_literals
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import engine as E

PPLDIR = os.path.join(ROOT, 'ppl')
TOL = 1e-6

PASS, FAIL = [], []


def note(ok, msg):
    (PASS if ok else FAIL).append(msg)


def busca_interprete():
    """Donde puede estar pplrun.py, de mas especifico a mas general."""
    candidatos = []
    if os.environ.get('HP_PRIME_KIT'):
        candidatos.append(os.path.join(os.environ['HP_PRIME_KIT'], 'scripts'))
    candidatos += [
        os.path.join(os.path.expanduser('~'), '.claude', 'skills',
                     'hp-prime', 'scripts'),
        os.path.join(os.path.dirname(ROOT), 'hp-prime-kit', 'scripts'),
        os.path.join(ROOT, 'tools'),
    ]
    for d in candidatos:
        if os.path.isfile(os.path.join(d, 'pplrun.py')):
            return d
    return None


def carga_ppl(pplrun):
    """Lo mismo que se pega en la calculadora, en orden de compilacion."""
    m = pplrun.Maquina()
    m.carga_fichero(os.path.join(PPLDIR, 'TDAT_REG.hpprgm'))
    for f in sorted(glob.glob(os.path.join(PPLDIR, 'TDAT_*.hpprgm'))):
        if not f.endswith('REG.hpprgm'):
            m.carga_fichero(f)
    m.carga_fichero(os.path.join(PPLDIR, 'TERMOLIB.hpprgm'))
    return m


REGIONES = {E.LIQUID: 0, E.MIX: 1, E.VAPOR: 2, E.SUPER: 3}


def cerca(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL * (abs(b) + 1.0)


def seguro(fn, *a):
    """Que el motor falle es un resultado que comparar, no una excepcion."""
    try:
        return fn(*a)
    except Exception:
        return None


def compara(nombre, ppl, ref):
    """Compara tambien los ERRORES: que los dos se nieguen en los mismos
    sitios es la mitad del valor. Un lado que da un numero donde el otro
    falla es justo la divergencia que se busca."""
    if ppl is None:
        note(False, '%s: el interprete no ha podido ejecutarlo' % nombre)
        return
    if ppl[7] < 0:
        if ref is None:
            note(True, nombre)
        else:
            note(False, '%s: el PPL da error (%s) y el motor da resultado'
                 % (nombre, ppl[8]))
        return
    if ref is None:
        note(False, '%s: el PPL da resultado y el motor da error' % nombre)
        return
    mal = []
    for i, k in enumerate(('T', 'P', 'v', 'u', 'h', 's')):
        if not cerca(ppl[i], ref[k]):
            mal.append('%s %.10g vs %.10g' % (k, ppl[i], ref[k]))
    xr = ref['x'] if ref['x'] is not None else -1.0
    if not cerca(ppl[6], xr):
        mal.append('x %.10g vs %.10g' % (ppl[6], xr))
    rr = REGIONES.get(ref['region'])
    if rr is None or int(ppl[7]) != rr:
        mal.append('region %d vs %s' % (int(ppl[7]), ref['region']))
    note(not mal, '%s: %s' % (nombre, '; '.join(mal)) if mal else nombre)


def barrido(m, orden):
    """Casos sacados de los PROPIOS DATOS: nodos tabulados, puntos entre dos
    nodos, y las inversas desde cada nodo. Asi el barrido crece con los datos
    y no se queda corto justo donde nadie miro."""
    subs = E.substances()
    for key in sorted(orden):
        sub = subs[key]
        m.llama('TLOAD', float(orden[key]))
        etq = key[:6]

        filas = sub['sat_by_T']
        for fila in filas[::max(1, len(filas) // 6)]:
            T = fila['T']
            for x in (0.0, 0.5, 1.0):
                compara('%s TTX(%.4g,%.1f)' % (etq, T, x),
                        seguro(m.llama, 'TTX', T, x),
                        seguro(E.state_Tx, sub, T, x))

        filas = sub['sat_by_P']
        for fila in filas[::max(1, len(filas) // 6)]:
            P = fila['P']
            for x in (0.0, 1.0):
                compara('%s TPX(%.4g,%.1f)' % (etq, P, x),
                        seguro(m.llama, 'TPX', P, x),
                        seguro(E.state_Px, sub, P, x))

        for b in sub['isobars'][::max(1, len(sub['isobars']) // 5)]:
            P, rows = b['P'], b['rows']
            paso = max(1, len(rows) // 5)
            for j in range(0, len(rows) - 1, paso):
                for T in (rows[j]['T'],
                          (rows[j]['T'] + rows[j + 1]['T']) / 2.0):
                    compara('%s TPT(%.6g,%.6g)' % (etq, P, T),
                            seguro(m.llama, 'TPT', P, T),
                            seguro(E.state_PT, sub, P, T))
                for pr, k in ((3, 'h'), (4, 's')):
                    y = rows[j][k]
                    compara('%s TPY(%.6g,%s,%.8g)' % (etq, P, k, y),
                            seguro(m.llama, 'TPY', P, float(pr), y),
                            seguro(E.state_Py, sub, P, k, y))


def regresion_supercritica(m, orden):
    """El fallo concreto que destapo este arnes, anotado aparte.

    Por encima de Pc no hay curva de saturacion. TPT lo contemplaba y TPY no:
    iba a TSATP, que alli devuelve {}, y salia con "P fora de rang". En la
    calculadora eso significaba que el agua a 25 MPa se podia consultar por
    (P,T) pero no por (P,h) ni por (P,s), que es la expansion isentropica de
    un ciclo Rankine supercritico.

    Se comprueba explicitamente para que no vuelva a entrar aunque alguien
    recorte el barrido de arriba.
    """
    subs = E.substances()
    n = 0
    for key in sorted(orden):
        sub = subs[key]
        Pc = sub['Pc_MPa']
        if not Pc:
            continue
        m.llama('TLOAD', float(orden[key]))
        for b in sub['isobars']:
            if b['P'] <= Pc:
                continue
            n += 1
            fila = b['rows'][len(b['rows']) // 2]
            for pr, k in ((3, 'h'), (4, 's')):
                st = seguro(m.llama, 'TPY', b['P'], float(pr), fila[k])
                nom = ('%s TPY supercritica P=%g %s=%.8g'
                       % (key[:6], b['P'], k, fila[k]))
                if st is None:
                    note(False, '%s: el interprete no ha podido ejecutarlo'
                         % nom)
                elif st[7] < 0:
                    note(False, '%s: da error (%s); deberia resolverla'
                         % (nom, st[8]))
                elif int(st[7]) != 3:
                    note(False, '%s: region %d, deberia ser 3 (supercritica)'
                         % (nom, int(st[7])))
                else:
                    note(True, nom)
    note(n >= 30, 'isobaras supercriticas cubiertas: %d (se esperaban >= 30)'
         % n)


def main():
    d = busca_interprete()
    if d is None:
        print('SALTADA: no se encuentra el interprete de PPL (pplrun.py).')
        print('  Es opcional. Para tenerlo:')
        print('    git clone https://github.com/JordiRigau/hp-prime-kit.git'
              ' ~/.claude/skills/hp-prime')
        print('  o define HP_PRIME_KIT apuntando a donde lo tengas clonado.')
        return 0
    if not glob.glob(os.path.join(PPLDIR, 'TDAT_*.hpprgm')):
        print('No hay ficheros generados: ejecuta tools/gen_ppl.py')
        return 1

    sys.path.insert(0, d)
    import pplrun

    m = carga_ppl(pplrun)
    orden = {}
    for i, k6 in enumerate(m.globales['TSUBS'], 1):
        for key in E.substances():
            if key[:6] == k6:
                orden[key] = i
    print('interprete: %s' % os.path.relpath(d, os.path.expanduser('~')))
    print('PPL cargado: %d funciones, %d sustancias'
          % (len(m.funcs), len(orden)))

    barrido(m, orden)
    regresion_supercritica(m, orden)

    print('PASS: %d' % len(PASS))
    print('FAIL: %d' % len(FAIL))
    for x in FAIL[:30]:
        print('  FAIL ' + x)
    if len(FAIL) > 30:
        print('  ... y %d mas' % (len(FAIL) - 30))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
