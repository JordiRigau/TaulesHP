# -*- coding: utf-8 -*-
"""Escribe los ficheros que se ARRASTRAN a la calculadora.

Cada variante tiene su carpeta, y un build solo vacia la suya:

    ppl/build/dev/         3 elementos: TDAT + TERMOLIB + TAULES
    ppl/build/dos/         2: el motor dentro de la app
    ppl/build/estudiants/  1: TODO dentro de TAULES.hpappdir

Compartian carpeta, asi que cada build se llevaba por delante el anterior y
"donde esta la otra version" tenia por respuesta "hay que rehacerla".

Antes esto no se podia y habia que pegar el texto en el editor del
Connectivity Kit: .hpprgm es un contenedor binario y se creia que solo el CK
sabia escribirlo. No es asi -- dentro va el fuente en UTF-16LE, verbatim -- y
hp-prime-kit lo escribe desde el PC. Su escritor esta contrastado contra una
G2 real, asi que aqui nos limitamos a llamarlo.

Antes de escribir nada pasa el linter sobre los tres ficheros a la vez
(--set), que ademas avisa de nombres exportados que chocarian como globales.
Si el linter da error, no se genera: mas vale no tener el binario que tener
uno que la calculadora rechace en el examen.

Necesita hp-prime-kit:

    https://github.com/JordiRigau/hp-prime-kit

Si no esta instalado se salta con instrucciones, y queda la ruta de pegar de
docs/INSTALACION.md. El repositorio sigue funcionando sin el.

Uso:
    python tools/gen_merged.py --all     # primero, genera ppl/compacte/
    python tools/build_hp.py             # 3 elementos -> build/dev/
    python tools/build_hp.py --dos       # 2 elementos -> build/dos/
    python tools/build_hp.py --tot       # 1: todo dentro -> build/estudiants/
"""
from __future__ import unicode_literals
import io, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPACTE = os.path.join(ROOT, 'ppl', 'compacte')
BUILD = os.path.join(ROOT, 'ppl', 'build')
ICONO = os.path.join(ROOT, 'icon', 'icon_blau.png')


def busca_kit():
    """La raiz de hp-prime-kit, de mas especifico a mas general.

    El mismo orden que tests/test_ppl_motor.py, para que instalar el kit una
    vez sirva para las dos cosas.
    """
    candidatos = []
    if os.environ.get('HP_PRIME_KIT'):
        candidatos.append(os.environ['HP_PRIME_KIT'])
    candidatos += [
        os.path.join(os.path.expanduser('~'), '.claude', 'skills', 'hp-prime'),
        os.path.join(os.path.dirname(ROOT), 'hp-prime-kit'),
    ]
    for d in candidatos:
        if os.path.isfile(os.path.join(d, 'hpkit', 'program.py')):
            return d
    return None


def escribe_programa(program, fuente, destino):
    """Fuente .txt -> .hpprgm, y se vuelve a leer antes de darlo por bueno.

    Leerlo de vuelta cuesta milisegundos y descarta la peor averia posible:
    un binario con la longitud mal puesta, que la calculadora acepta y abre
    con el codigo cortado.
    """
    f = open(program.default_template(), 'rb')
    try:
        plantilla = f.read()
    finally:
        f.close()
    texto = program.normalize_source(
        io.open(fuente, encoding='utf-8').read())
    datos = program.write(plantilla, texto)
    if program.read(datos)[0] != texto:
        raise RuntimeError('%s: lo escrito no se lee igual, NO instalar'
                           % os.path.basename(destino))
    f = open(destino, 'wb')
    try:
        f.write(datos)
    finally:
        f.close()
    print('  %-24s %8.1f KB   <- %s'
          % (os.path.basename(destino), len(datos) / 1024.0,
             os.path.relpath(fuente, ROOT)))


def main(argv):
    dos = '--dos' in argv
    tot = '--tot' in argv
    kit = busca_kit()
    if kit is None:
        print('SALTADO: no se encuentra hp-prime-kit.')
        print('  git clone https://github.com/JordiRigau/hp-prime-kit.git'
              ' ~/.claude/skills/hp-prime')
        print('  o define HP_PRIME_KIT apuntando a donde lo tengas clonado.')
        print('  Sin el, queda la ruta de pegar: docs/INSTALACION.md')
        return 0

    sys.path.insert(0, kit)
    from hpkit import program, appdir, lint

    if tot:
        app_src = os.path.join(COMPACTE, 'TAULES_APP_TOT.txt')
    elif dos:
        app_src = os.path.join(COMPACTE, 'TAULES_APP.txt')
    else:
        app_src = os.path.join(COMPACTE, 'TAULES_APP_LIB.txt')
    # con --tot los datos van dentro de la app: no hay TDAT que escribir
    fuentes = [app_src] if tot else [os.path.join(COMPACTE, 'TDAT.txt'),
                                     app_src]
    if not dos and not tot:
        fuentes.insert(1, os.path.join(COMPACTE, 'TERMOLIB.txt'))
    faltan = [f for f in fuentes if not os.path.isfile(f)]
    if faltan:
        print('Faltan fuentes: %s' % ', '.join(os.path.basename(f)
                                               for f in faltan))
        print('Ejecuta antes: python tools/gen_merged.py --all')
        return 1

    # Gate: los tres van juntos a la calculadora, asi que se miran juntos.
    if lint.check_files(fuentes, as_set=True):
        print('\nEl linter da error: no se genera nada.')
        return 1

    # Solo se vacia la carpeta de ESTA variante: la otra se queda donde
    # estaba, que es lo que permite tener a mano la de los estudiantes y la
    # de desarrollo a la vez.
    nom = 'estudiants' if tot else ('dos' if dos else 'dev')
    dest = os.path.join(BUILD, nom)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)

    print('\nppl/build/%s/  -- variante de %d elemento%s'
          % (nom, 1 if tot else (2 if dos else 3), '' if tot else 's'))
    print('-' * 62)
    if not tot:
        escribe_programa(program, os.path.join(COMPACTE, 'TDAT.txt'),
                         os.path.join(dest, 'TDAT.hpprgm'))
    if not dos and not tot:
        escribe_programa(program, os.path.join(COMPACTE, 'TERMOLIB.txt'),
                         os.path.join(dest, 'TERMOLIB.hpprgm'))

    # La app se construye en blanco (descriptor 'blank'): no hereda de
    # ninguna app de fabrica, que es lo que obliga a dibujar el menu y leer
    # las teclas a mano -- ver docs/ANALISIS.md.
    carpeta = appdir.build('TAULES', [], ICONO, dest, quiet=True,
                           descriptor='blank')
    appdir.put_ppl_program(carpeta, 'TAULES', app_src,
                           program.default_template())
    print('  %-24s %8s     <- %s'
          % ('TAULES.hpappdir', 'carpeta', os.path.relpath(app_src, ROOT)))

    # Comprobacion final: lo que hay en disco es lo que un build daria.
    mal = appdir.check(carpeta, [], ICONO, 'blank', app_src)
    if mal:
        for f, why in mal:
            print('  AVISO %s: %s' % (f, why))
        return 1

    print('-' * 62)
    print('en ppl/build/%s/' % nom)
    if tot:
        print('Arrastra TAULES.hpappdir SOBRE la calculadora en la ventana')
        print('del Connectivity Kit. Es lo unico: los datos van dentro, asi')
        print('que no hay ningun orden que vigilar.')
    else:
        print('Arrastra estos %d elementos SOBRE la calculadora en la ventana '
              'del' % (2 if dos else 3))
        print('Connectivity Kit. La carpeta Calculators\\ es un espejo: '
              'copiarlos')
        print('ahi no instala nada.')
        print('Orden: TDAT -> %sTAULES' % ('' if dos else 'TERMOLIB -> '))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
