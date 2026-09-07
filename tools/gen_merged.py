# -*- coding: utf-8 -*-
"""Genera la version COMPACTA: 2 elementos en la calculadora en vez de 18.

Reparto:

    TDAT   (programa)  todas las sustancias + el registro TSUBS/TNAMS
    TAULES (app)       motor + interfaz + generalizados + ganchos de la app

Y una tercera, la de UN elemento, con los datos tambien dentro de la app:
es la que se reparte a los estudiantes, porque se arrastra un solo fichero.

Los metodos generalizados (ppl/GENER.txt) van SIEMPRE dentro de la app, en
las dos variantes. No llevan datos -salen de la ecuacion de Lee-Kesler- y no
tienen que ser accesibles desde otro programa, asi que no ganan nada
viviendo fuera. El menu de botones (ppl/MENU.txt) es la pantalla de entrada
y va con ellos.

Por que 2 y no 1: cabe todo dentro de la app, pero entonces el programa de la
app pasa de ~26 KB a ~330 KB y editarlo en la calculadora se vuelve incomodo.
Separar lo que cambia (el codigo, pequeno) de lo que no cambia nunca (los
datos, enorme) es mas practico y deja el catalogo de programas con una sola
entrada.

Ademas genera la variante de 3 elementos (ppl/compacte/ con sufijo _LIB):

    TDAT     (programa)  dades
    TERMOLIB (programa)  motor, cridable des de qualsevol altre programa o app
    TAULES   (app)       nomes interficie

Hace falta si algun dia se quiere OTRA app que use el motor: lo que se exporta
desde el programa de una app queda ligado a esa app, mientras que lo exportado
desde un programa del catalogo es global sin discusion. Cuesta un elemento mas
y a cambio el motor es reutilizable.

Uso:
    python tools/gen_merged.py            # las sustancias por defecto
    python tools/gen_merged.py --all
    python tools/gen_merged.py AIGUA AMONIAC R134A R410A
"""
from __future__ import unicode_literals
import io, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import load
import gen_ppl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPL = os.path.join(ROOT, 'ppl')
OUT = os.path.join(PPL, 'compacte')

CAB = '''// %s
// GENERADO por tools/gen_merged.py -- NO EDITAR A MANO.
// Se regenera desde data/master.json y los fuentes de ppl/.
// ===================================================================

'''


def sin_cabecera(txt):
    """Quita el bloque de comentarios inicial de un fuente, para no arrastrar
    tres cabeceras dentro del mismo fichero."""
    lines = txt.split('\n')
    i = 0
    while i < len(lines) and (lines[i].startswith('//') or not lines[i].strip()):
        i += 1
    return '\n'.join(lines[i:]).strip()


def exports(txt):
    """Nombres exportados, para detectar colisiones al juntar ficheros."""
    out = set()
    for m in re.finditer(r'^EXPORT\s+(\w+)\s*\(', txt, re.M):
        out.add(m.group(1))
    for m in re.finditer(r'^EXPORT\s+([A-Za-z]\w*)\s*:?=', txt, re.M):
        out.add(m.group(1))
    for m in re.finditer(r'^EXPORT\s+([A-Za-z]\w*(?:\s*,\s*[A-Za-z]\w*)*)\s*;',
                         txt, re.M):
        out |= {x.strip() for x in m.group(1).split(',')}
    return out


def main(argv):
    subs = {s['key']: s for s in load()}
    if '--all' in argv:
        keys = gen_ppl.DEFAULT + [k for k in sorted(subs)
                                  if k not in gen_ppl.DEFAULT]
    else:
        keys = [a for a in argv[1:] if not a.startswith('--')] or gen_ppl.DEFAULT
    keys = [k for k in keys if k in subs]

    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    # ---- 1) TDAT: todos los datos en un solo programa ----------------
    partes = [CAB % 'TDAT - dades de totes les substancies']
    hechos = []
    for k in keys:
        partes.append(gen_ppl.gen_substance(subs[k]))
        hechos.append((subs[k]['key'][:6], subs[k]['name']))
    partes.append('// registre: quines substancies hi ha carregades')
    partes.append('EXPORT TSUBS:={%s};'
                  % ','.join('"%s"' % h[0] for h in hechos))
    partes.append('EXPORT TNAMS:={%s};'
                  % ','.join('"%s"' % h[1].replace('"', "'") for h in hechos))

    # Constantes criticas, para el desplegable de los metodos generalizados.
    # Ya estaban en master.json y no se usaban: sin esto, una pregunta que
    # nombra la sustancia -"s'expandeix etile", 30/10/2019 y 31/10/2024- y NO
    # da Tc, Pc ni w obliga a buscarlas fuera del aparato, que es justo lo que
    # la app tendria que evitar.
    #
    # TGNOMS lleva "(manual)" delante, asi que el indice del desplegable es el
    # de TGCRI mas uno. El acentrico del mercurio no esta en el PDF: va a 0,
    # que es lo que hace el metodo de dos parametros.
    partes.append('')
    partes.append('// constants critiques: Tc[K], Pc[MPa], w, M[g/mol]')
    partes.append('EXPORT TGNOMS:={"(manual)",%s};'
                  % ','.join('"%s"' % subs[k]['name'].replace('"', "'")
                             for k in keys))
    partes.append('EXPORT TGCRI:=[%s];'
                  % ','.join('[%s,%s,%s,%s]'
                             % (subs[k]['Tc_K'], subs[k]['Pc_MPa'],
                                subs[k]['omega'] or 0, subs[k]['molar_mass'])
                             for k in keys))
    tdat = '\n'.join(partes) + '\n'

    # ---- 2) TAULES: motor + interficie + ganxos de la app ------------
    lib = io.open(os.path.join(PPL, 'TERMOLIB.txt'), encoding='utf-8').read()
    ui = io.open(os.path.join(PPL, 'TERMO.txt'), encoding='utf-8').read()
    gen = io.open(os.path.join(PPL, 'GENER.txt'), encoding='utf-8').read()
    men = io.open(os.path.join(PPL, 'MENU.txt'), encoding='utf-8').read()
    app = io.open(os.path.join(PPL, 'APP_TAULES.txt'), encoding='utf-8').read()

    # Todos contra todos: un nombre exportado es global y dos iguales chocan.
    # Antes eran tres piezas y bastaban tres cruces escritos a mano; con cinco
    # serian diez, y el que se olvidara no daria error hasta la calculadora.
    piezas = [('TERMOLIB', lib), ('TERMO', ui), ('GENER', gen),
              ('MENU', men), ('APP_TAULES', app)]
    for i in range(len(piezas)):
        for j in range(i + 1, len(piezas)):
            dup = exports(piezas[i][1]) & exports(piezas[j][1])
            if dup:
                print('ERROR: noms exportats repetits entre %s i %s: %s'
                      % (piezas[i][0], piezas[j][0], sorted(dup)))
                return 1

    # Lo que va dentro de la app en las DOS variantes. Los generalizados no
    # llevan datos -salen de la ecuacion de Lee-Kesler- y no los necesita
    # ningun otro programa, asi que no ganan nada viviendo fuera.
    cuerpo = ('\n\n// ========= INTERFICIE (ve de ppl/TERMO.txt) =========\n'
              + sin_cabecera(ui)
              + '\n\n// ====== GENERALITZATS (ve de ppl/GENER.txt) ======\n'
              + sin_cabecera(gen)
              + '\n\n// ========= MENU (ve de ppl/MENU.txt) =========\n'
              + sin_cabecera(men)
              + '\n\n// ====== GANXOS DE LA APP (ve de ppl/APP_TAULES.txt) ======\n'
              + sin_cabecera(app) + '\n')

    taules = (CAB % 'TAULES (App) - motor + interficie + generalitzats'
              + '// ============ MOTOR (ve de ppl/TERMOLIB.txt) ============\n'
              + sin_cabecera(lib)
              + cuerpo)

    # variante de 3 elementos: el motor de tablas se queda fuera, en su
    # programa, para que otra app pueda llamarlo
    nota_lib = ('// El motor de taules va a part, al programa TERMOLIB, perque\n'
                '// una altra app el pugui cridar. Els generalitzats no: no\n'
                '// porten dades i no els necessita ningu mes.\n')
    taules_lib = (CAB % 'TAULES (App) - interficie + generalitzats'
                  + nota_lib + cuerpo)

    # variante de 1 elemento: TAMBIEN los datos dentro de la app. Es la que
    # se reparte a los estudiantes. No gana nada tecnico -- al reves, el
    # programa de la app pasa de 36 KB a ~364 KB y editarlo en la calculadora
    # deja de ser comodo -- pero se arrastra UN fichero y desaparece el fallo
    # de instalacion mas facil de cometer, que es el orden.
    nota_tot = ('// TOT dins de l\'app: dades, motor, interficie i menu. Es\n'
                '// la versio d\'un sol fitxer, per no haver de vigilar cap\n'
                '// ordre d\'instal.lacio. Per desenvolupar, fes servir la de\n'
                '// 3 elements: el motor a part es reutilitzable i el programa\n'
                '// de l\'app es prou petit per obrir-lo a la calculadora.\n')
    taules_tot = (CAB % 'TAULES (App) - tot dins: dades + motor + interficie'
                  + nota_tot
                  + '\n// ============ DADES (ve de data/master.json) ============\n'
                  + sin_cabecera(tdat)
                  + '\n\n// ============ MOTOR (ve de ppl/TERMOLIB.txt) ============\n'
                  + sin_cabecera(lib)
                  + cuerpo)

    for nom, txt in (('TDAT', tdat), ('TAULES_APP', taules),
                     ('TAULES_APP_LIB', taules_lib),
                     ('TAULES_APP_TOT', taules_tot),
                     ('TERMOLIB', io.open(os.path.join(PPL, 'TERMOLIB.txt'),
                                          encoding='utf-8').read())):
        # Fuente en texto. El .hpprgm binario que se arrastra a la
        # calculadora lo escribe tools/build_hp.py desde estos ficheros.
        with io.open(os.path.join(OUT, nom + '.txt'), 'w',
                     encoding='utf-8') as f:
            f.write(txt)

    print('ppl/compacte/  -- %d substancies' % len(hechos))
    print('-' * 58)
    print('  %-16s %7.1f KB   programa de dades' % ('TDAT', len(tdat) / 1024.0))
    print('  %-16s %7.1f KB   programa de la app'
          % ('TAULES_APP', len(taules) / 1024.0))
    print('-' * 58)
    print('  %-16s %7.1f KB   interficie + generalitzats (variant de 3)'
          % ('TAULES_APP_LIB', len(taules_lib) / 1024.0))
    print('  %-16s %7.1f KB   motor a part (variant de 3)'
          % ('TERMOLIB', os.path.getsize(os.path.join(PPL, 'TERMOLIB.txt'))
             / 1024.0))
    print('-' * 58)
    print('  %-16s %7.1f KB   TOT dins (variant d\'1, per als estudiants)'
          % ('TAULES_APP_TOT', len(taules_tot) / 1024.0))
    print('-' * 58)
    print('  variant d\'1: TAULES_APP_TOT            (un sol fitxer)')
    print('  variant de 2: TDAT + TAULES_APP')
    print('  variant de 3: TDAT + TERMOLIB + TAULES_APP_LIB  (motor reutilitzable)')
    print('  en comptes de %d elements' % (len(hechos) + 4))
    print('  substancies: %s' % ', '.join(h[0] for h in hechos))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
