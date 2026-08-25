# -*- coding: utf-8 -*-
"""Genera la version COMPACTA: 2 elementos en la calculadora en vez de 18.

Reparto:

    TDAT   (programa)  todas las sustancias + el registro TSUBS/TNAMS
    TAULES (app)       motor + interfaz + ganchos de la app

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
    tdat = '\n'.join(partes) + '\n'

    # ---- 2) TAULES: motor + interficie + ganxos de la app ------------
    lib = io.open(os.path.join(PPL, 'TERMOLIB.hpprgm'), encoding='utf-8').read()
    ui = io.open(os.path.join(PPL, 'TERMO.hpprgm'), encoding='utf-8').read()
    app = io.open(os.path.join(PPL, 'APP_TAULES.hpprgm'), encoding='utf-8').read()

    dup = (exports(lib) & exports(ui)) | (exports(lib) & exports(app)) \
        | (exports(ui) & exports(app))
    if dup:
        print('ERROR: noms exportats repetits entre fitxers: %s' % sorted(dup))
        return 1

    taules = (CAB % 'TAULES (App) - motor + interficie'
              + '// ============ MOTOR (ve de ppl/TERMOLIB.hpprgm) ============\n'
              + sin_cabecera(lib)
              + '\n\n// ========= INTERFICIE (ve de ppl/TERMO.hpprgm) =========\n'
              + sin_cabecera(ui)
              + '\n\n// ====== GANXOS DE LA APP (ve de ppl/APP_TAULES.hpprgm) ======\n'
              + sin_cabecera(app) + '\n')

    # variante de 3 elementos: el motor se queda fuera, en su programa, para
    # que otra app pueda llamarlo
    nota_lib = ('// El motor va a part, al programa TERMOLIB, perque una altra\n'
                '// app el pugui cridar.\n\n')
    taules_lib = (CAB % 'TAULES (App) - nomes interficie'
                  + nota_lib
                  + '// ========= INTERFICIE (ve de ppl/TERMO.hpprgm) =========\n'
                  + sin_cabecera(ui)
                  + '\n\n// ====== GANXOS DE LA APP (ve de ppl/APP_TAULES.hpprgm) ======\n'
                  + sin_cabecera(app) + '\n')

    for nom, txt in (('TDAT', tdat), ('TAULES_APP', taules),
                     ('TAULES_APP_LIB', taules_lib),
                     ('TERMOLIB', io.open(os.path.join(PPL, 'TERMOLIB.hpprgm'),
                                          encoding='utf-8').read())):
        # Solo .txt: es lo que se pega en el editor del Connectivity Kit.
        # El .hpprgm de verdad es binario y lo escribe el CK al guardar.
        with io.open(os.path.join(OUT, nom + '.txt'), 'w',
                     encoding='utf-8') as f:
            f.write(txt)

    print('ppl/compacte/  -- %d substancies' % len(hechos))
    print('-' * 58)
    print('  %-16s %7.1f KB   programa de dades' % ('TDAT', len(tdat) / 1024.0))
    print('  %-16s %7.1f KB   programa de la app'
          % ('TAULES_APP', len(taules) / 1024.0))
    print('-' * 58)
    print('  %-16s %7.1f KB   nomes interficie (variant de 3)'
          % ('TAULES_APP_LIB', len(taules_lib) / 1024.0))
    print('  %-16s %7.1f KB   motor a part (variant de 3)'
          % ('TERMOLIB', os.path.getsize(os.path.join(PPL, 'TERMOLIB.hpprgm'))
             / 1024.0))
    print('-' * 58)
    print('  variant de 2: TDAT + TAULES_APP')
    print('  variant de 3: TDAT + TERMOLIB + TAULES_APP_LIB  (motor reutilitzable)')
    print('  en comptes de %d elements' % (len(hechos) + 4))
    print('  substancies: %s' % ', '.join(h[0] for h in hechos))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
