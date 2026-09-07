# -*- coding: utf-8 -*-
"""Ejecuta el PPL de los metodos generalizados y lo compara con tools/lk.py.

Es el mismo arnes que test_ppl_motor.py hace con las tablas, aplicado a la
otra mitad. Y hace falta por el mismo motivo: sin el, la clase de fallo que
queda suelta es que el PPL y el Python calculen cosas distintas. Cada uno
seria coherente consigo mismo, los dos pasarian sus pruebas, y la calculadora
daria en el examen un numero que el PC no da.

Aqui el riesgo es concreto y tiene nombre: la busqueda de la raiz Vr. El
Python barre una rejilla logaritmica de 400 puntos y biseca 80 veces; el PPL,
que ha de caber en una calculadora, barre 150 y biseca 40. Si esa poda mueve
la raiz elegida en algun sitio, es aqui donde se ve.

Necesita el interprete de PPL de hp-prime-kit. Si no esta instalado, la
prueba se SALTA en vez de fallar.

    python tests/test_ppl_gener.py
"""
from __future__ import unicode_literals
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import lk

PPLDIR = os.path.join(ROOT, 'ppl')
TOOLS = os.path.join(ROOT, 'tools')
TOL = 1e-6

PASS, FAIL = [], []


def note(ok, msg):
    (PASS if ok else FAIL).append(msg)


def busca_interprete():
    candidatos = []
    if os.environ.get('HP_PRIME_KIT'):
        candidatos.append(os.environ['HP_PRIME_KIT'])
    candidatos += [
        os.path.join(os.path.expanduser('~'), '.claude', 'skills', 'hp-prime'),
        os.path.join(os.path.dirname(ROOT), 'hp-prime-kit'),
    ]
    for d in candidatos:
        if os.path.isfile(os.path.join(d, 'hpkit', 'interp.py')):
            return d
    return None


def cerca(a, b, tol=TOL):
    return abs(a - b) <= tol * (abs(b) + 1.0)


# La rejilla del propio diagrama generalizado: las Tr y Pr que trae impresas
# la carta, mas la region critica, que es donde el metodo es mas delicado.
TRS = [0.60, 0.70, 0.80, 0.90, 0.95, 1.00, 1.02, 1.05, 1.10, 1.20, 1.30,
       1.50, 1.70, 2.00, 2.60, 3.00, 4.00]
PRS = [0.010, 0.050, 0.100, 0.200, 0.400, 0.600, 0.800, 1.000, 1.200,
       1.500, 2.000, 3.000, 5.000, 7.000, 10.00]
WS = [0.0, 0.099, 0.199, 0.583]


def barrido_trpr(m):
    """Z0, Z1, Z y las dos discrepancias en toda la rejilla de la carta."""
    n = 0
    for tr in TRS:
        for pr in PRS:
            ppl = m.call('TGPIT', tr, pr, 0.099)
            try:
                ref = lk.generalizado(tr, pr, 0.099)
            except lk.NoConverge:
                ref = None
            if ref is None:
                note(ppl[10] < 0,
                     'TGPIT(%.2f,%.3f): el PPL da resultado y lk.py no'
                     % (tr, pr))
                continue
            if ppl[10] < 0:
                note(False, 'TGPIT(%.2f,%.3f): el PPL no encuentra raiz'
                     % (tr, pr))
                continue
            mal = []
            for i, k in enumerate(('z0', 'z1', 'z', 'dh0', 'dh1', 'dh',
                                   'ds0', 'ds1', 'ds')):
                if not cerca(ppl[i], ref[k]):
                    mal.append('%s %.10g vs %.10g' % (k, ppl[i], ref[k]))
            note(not mal, 'TGPIT(%.2f,%.3f): %s'
                 % (tr, pr, '; '.join(mal)) if mal
                 else 'TGPIT(%.2f,%.3f)' % (tr, pr))
            n += 1
    return n


def barrido_w(m):
    """Que la combinacion de Pitzer se haga igual con cualquier w."""
    for w in WS:
        for tr, pr in ((0.90, 0.20), (1.10, 1.50), (2.00, 5.00)):
            ppl = m.call('TGPIT', tr, pr, w)
            ref = lk.generalizado(tr, pr, w)
            mal = [k for i, k in ((2, 'z'), (5, 'dh'), (8, 'ds'))
                   if not cerca(ppl[i], ref[k])]
            note(not mal, 'TGPIT w=%.3f (%.2f,%.2f): %s'
                 % (w, tr, pr, ','.join(mal)) if mal
                 else 'TGPIT w=%.3f (%.2f,%.2f)' % (w, tr, pr))


def barrido_vr(m):
    """La rama (Tr, Vr), la del deposito rigido: no itera, pero evalua el
    fluido de referencia al mismo Vr y ese detalle es facil de perder."""
    for tr in (0.90, 1.00, 1.05, 1.15, 1.50, 2.50):
        for vr in (0.15, 0.25, 0.50, 1.00, 3.00, 20.0):
            ppl = m.call('TGPITV', tr, vr, 0.099)
            try:
                ref = lk.generalizado_tv(tr, vr, 0.099)
            except lk.NoConverge:
                # dentro de la campana la ecuacion da presion negativa: los
                # dos motores han de negarse, y en el mismo sitio
                note(ppl[10] < 0,
                     'TGPITV(%.2f,%.2f): lk.py lo rechaza y el PPL no'
                     % (tr, vr))
                continue
            if ppl[10] < 0:
                note(False, 'TGPITV(%.2f,%.2f): el PPL lo rechaza y lk.py no'
                     % (tr, vr))
                continue
            mal = []
            for i, k in enumerate(('z0', 'z1', 'z', 'dh0', 'dh1', 'dh',
                                   'ds0', 'ds1', 'ds')):
                if not cerca(ppl[i], ref[k]):
                    mal.append('%s %.10g vs %.10g' % (k, ppl[i], ref[k]))
            note(not mal, 'TGPITV(%.2f,%.2f): %s'
                 % (tr, vr, '; '.join(mal)) if mal
                 else 'TGPITV(%.2f,%.2f)' % (tr, vr))


def barrido_raiz(m):
    """La raiz elegida, ahi donde la isoterma tiene TRES.

    Por debajo de la critica y por debajo de la presion de saturacion hay
    tres raices, y las dos implementaciones han de quedarse con la misma: la
    mayor, que es la de vapor. Un barrido mas grueso podria saltarse la
    primera y devolver la de en medio, que no tiene sentido fisico.
    """
    ks = {'simple': lk.SIMPLE, 'refer': lk.REFER}
    tres = 0
    for nom in sorted(ks):
        for tr in (0.70, 0.80, 0.90, 0.95):
            for pr in (0.01, 0.05, 0.10, 0.20, 0.50):
                raices = lk._raices_vr(ks[nom], tr, pr)
                if not raices:
                    continue
                if len(raices) > 1:
                    tres += 1
                ppl = m.call('TGVR', m.globals_['TGKS' if nom == 'simple'
                                                else 'TGKR'], tr, pr)
                note(cerca(ppl, raices[-1], 1e-6),
                     'TGVR %s(%.2f,%.2f) %.10g vs %.10g  [%d arrels]'
                     % (nom, tr, pr, ppl, raices[-1], len(raices)))
    return tres


def barrido_menu(m):
    """La geometria del menu, sin pintar nada.

    Es lo unico de una pantalla que se puede comprobar desde el PC, y cubre
    dos fallos que en la calculadora no dan error: un boton que se sale del
    area de app -que acaba en y=212, debajo empieza la fila de teclas de
    pantalla- y dos zonas sensibles que se solapan, con lo que el segundo
    boton no se podria pulsar nunca.
    """
    n = 3
    cajas = [m.call('TMBTN', float(i)) for i in range(1, n + 1)]
    for i, c in enumerate(cajas, 1):
        note(c[1] >= 0 and c[3] <= 212,
             'TMBTN(%d) se sale del area de app: y de %g a %g' % (i, c[1], c[3]))
        note(c[0] >= 0 and c[2] <= 320,
             'TMBTN(%d) se sale de la pantalla: x de %g a %g' % (i, c[0], c[2]))
    for i in range(len(cajas) - 1):
        note(cajas[i][3] < cajas[i + 1][1],
             'TMBTN(%d) y TMBTN(%d) se solapan' % (i + 1, i + 2))
    # el centro de cada boton ha de dar ESE boton, y el hueco entre dos, cero
    for i, c in enumerate(cajas, 1):
        cy = (c[1] + c[3]) / 2.0
        note(m.call('TMHIT', 160.0, cy) == i,
             'TMHIT en el centro del boton %d no da %d' % (i, i))
    for i in range(len(cajas) - 1):
        hueco = (cajas[i][3] + cajas[i + 1][1]) / 2.0
        note(m.call('TMHIT', 160.0, hueco) == 0,
             'TMHIT en el hueco tras el boton %d deberia dar 0' % (i + 1))
    note(m.call('TMHIT', -1.0, -1.0) == 0, 'sin tacto TMHIT deberia dar 0')
    note(m.call('TMTOUCH')[0] < 0,
         'TMTOUCH deberia degradar a {-1,-1} sin MOUSE, no reventar')


def fluid(m, tc, pc, w, cpa=0.0, cpb=0.0, mm=0.0):
    """Carga las constantes del fluido en los globales del PPL."""
    m.globals_['TGTC'] = tc
    m.globals_['TGPC'] = pc
    m.globals_['TGW'] = w
    m.globals_['TGCPA'] = cpa
    m.globals_['TGCPB'] = cpb
    m.globals_['TGMM'] = mm


def barrido_examens(m):
    """Seis preguntas de examen resueltas ENTERAS con las funciones del PPL.

    El barrido de arriba compara PPL contra lk.py, que es lo que caza una
    divergencia de nucleo. Esto cubre lo otro: la capa de unidades. TGEST
    divide por zp*1000000 para pasar de MPa a Pa, y un factor mil ahi da un
    numero perfectamente creible y equivocado que ninguna comparacion contra
    lk.py vería, porque lk.py trabaja en Pa y no tiene esa linea.

    La tolerancia es la del examen -la solucion oficial sale de leer un
    grafico a ojo-, no la de la maquina.
    """
    def chk(ref, calc, oficial, tol):
        ok = abs(calc - oficial) <= tol * abs(oficial)
        note(ok, '%s: %.6g vs %.6g oficial  (%.2f%%)'
             % (ref, calc, oficial, 100 * abs(calc - oficial) / abs(oficial)))

    # 08/04/2026 q4: turbina, entra a Tr=2,6 i Pr=3
    fluid(m, 305.3, 4.87, 0.099)
    g = m.call('TGPIT', 2.6, 3.0, 0.099)
    dh1 = g[5] * 0.2765 * 305.3                    # kJ/kg
    pot = 1.5 * (1.75 * (2.6 * 305.3 - 400.0) + dh1) - 450.0
    chk('08/04/2026 q4  W turbina', -pot, -535.0, 0.01)

    # 28/10/2025 q1 i q2: diposit rigid. Va per TGANY amb v>0, que es
    # exactamente lo que hace la pantalla cuando le das el volumen: la P es
    # la incognita, no un dato.
    fluid(m, 300.0, 7.5, 0.0, 37.4)
    v = 0.012 / 144.3                              # m3/mol
    ga = m.call('TGANY', 345.0, 0.0, v)
    gb = m.call('TGANY', 315.0, 0.0, v)
    chk('28/10/2025 q1  dP', gb[7] - ga[7], -6.0, 0.05)
    ua = ga[2] - (ga[7] * 1e6 * v - 8.314 * 345.0)
    ub = gb[2] - (gb[7] * 1e6 * v - 8.314 * 315.0)
    du = m.call('TGIDH', 345.0, 315.0) - 8.314 * (315.0 - 345.0) + (ub - ua)
    chk('28/10/2025 q2  Q', 144.3 * du / 1000.0, -155.0, 0.08)

    # y el rechazo: el mismo fluido con un volumen que cae dentro de la
    # campana no puede dar un numero
    fluid(m, 300.0, 5.0, 0.0)
    note(m.call('TGANY', 270.0, 0.0, 7.4826e-05)[6] < 0,
         'TGANY dentro de la campana: deberia negarse y da un numero')

    # 09/04/2025 q1 i q2: difusor, amb TGEST i la capa d'unitats
    fluid(m, 300.0, 5.0, 0.089, 43.0, 0.0, 120.0)
    e1 = m.call('TGEST', 300.0, 5.0)
    e2 = m.call('TGEST', 390.0, 25.0)
    chk('09/04/2025 q1  flux massic',
        0.002 * 300.0 / (e1[1] / 0.120), 511.0, 0.02)
    dh = (m.call('TGIDH', 300.0, 390.0) + e2[2] - e1[2]) / 0.120
    chk('09/04/2025 q2  v sortida',
        (300.0 ** 2 - 2 * dh) ** 0.5, 174.1, 0.03)

    # 14/04/2023 q9: dos estats i du
    fluid(m, 190.0, 46.0, 0.0, 34.0)
    e1 = m.call('TGEST', 209.0, 69.0)
    e2 = m.call('TGEST', 228.0, 92.0)
    du = (m.call('TGIDH', 209.0, 228.0) + e2[2] - e1[2]
          - 8.314 * (228.0 * e2[0] - 209.0 * e1[0]))
    chk('14/04/2023 q9  W electric', 85 * du / 1000.0, 49.0, 0.02)

    # 02/11/2021 q7: el cami de l'entropia
    fluid(m, 280.0, 5.0, 0.09, 0.0)
    e1 = m.call('TGEST', 308.0, 10.0)
    e2 = m.call('TGEST', 308.0, 5.0)
    ds = -8.314 * __import__('math').log(0.5) + e2[3] - e1[3]
    chk('02/11/2021 q7  dS univers', 10 * ds, 173.9, 0.01)

    # 30/10/2017 q8: cp* = a + b*T, que es l'unic cas amb pendent
    fluid(m, 408.2, 3.65, 0.0, 19.252, 0.261)
    e1 = m.call('TGEST', 306.15, 5.475)
    e2 = m.call('TGEST', 428.65, 5.475)
    q = (15000.0 / 58.1) * (m.call('TGIDH', 306.15, 428.65)
                            + e2[2] - e1[2]) / 1000.0
    chk("30/10/2017 q8  Q amb cp'", q, 5045.2, 0.01)


def prova_fitxer_unic(kit):
    """La variante de 1 elemento, la que se reparte a los estudiantes.

    Es un fichero distinto del que prueba todo lo demas: junta los datos, el
    motor de tablas, el de generalizados y la interfaz en un solo programa.
    Los nombres exportados que ahi conviven pasan de ~30 a mas de cien, y una
    colision entre dos de ellos no la veria ninguna otra prueba porque en la
    variante de 3 viven en programas separados.

    Se salta si no esta generado: lleva los datos dentro, asi que no se
    versiona y solo existe despues de `gen_merged.py --all`.
    """
    from hpkit import interp
    ruta = os.path.join(ROOT, 'ppl', 'compacte', 'TAULES_APP_TOT.txt')
    if not os.path.isfile(ruta):
        return False
    m = interp.Machine()
    m.load_file(ruta)
    m.call('TLOAD', 1.0)
    st = m.call('TPT', 3.0, 350.0)
    note(abs(st[4] - 3116.06) < 0.01 and abs(st[5] - 6.7449) < 1e-4,
         'fitxer unic: aigua 3 MPa 350 C dona h=%.2f s=%.4f' % (st[4], st[5]))
    g = m.call('TGPIT', 2.6, 3.0, 0.099)
    ref = lk.generalizado(2.6, 3.0, 0.099)
    note(cerca(g[2], ref['z']) and cerca(g[5], ref['dh']),
         'fitxer unic: TGPIT(2.6,3,0.099) no coincideix amb lk.py')
    note(m.call('TMHIT', 160.0, 60.0) == 1, 'fitxer unic: el menu no respon')

    # Les pantalles d'ajuda dibuixen la seva llista amb interlineat de 17 px
    # des de y=26: a partir de l'onzena linia el text cau per sota de y=212 i
    # ja no es veu. No dona cap error, i mirant el codi no es nota: la llista
    # havia arribat a catorze sense que res avises.
    for nom in ('TGAJUT', 'TMAJUT', 'TAJUT'):
        n = len(m.globals_[nom])
        note(n <= 11, '%s te %d linies i a la pantalla n hi caben 11'
             % (nom, n))

    # El desplegable de substancia: que carregui les MATEIXES constants que
    # dona master.json. Si TGNOMS i TGCRI se separessin algun dia -- una
    # substancia mes, un altre ordre -- el desplegable diria un nom i
    # carregaria les constants d'una altra, i cap altra prova ho veuria.
    import engine as E
    noms = m.globals_['TGNOMS']
    per_nom = {v['name']: v for v in E.substances().values()}
    for i in range(2, len(noms) + 1):
        m.globals_['TGSUB'] = float(i)
        m.call('TGCARR')
        sub = per_nom[noms[i - 1]]
        mal = []
        for camp, glob in (('Tc_K', 'TGTC'), ('Pc_MPa', 'TGPC'),
                           ('omega', 'TGW'), ('molar_mass', 'TGMM')):
            esperat = sub[camp] or 0.0
            if not cerca(m.globals_[glob], esperat, 1e-9):
                mal.append('%s %g vs %g' % (camp, m.globals_[glob], esperat))
        note(not mal, 'TGCARR(%s): %s' % (noms[i - 1], '; '.join(mal)))
    m.globals_['TGSUB'] = 1.0
    return True


# ---------------------------------------------------------------- pantalles
# tools/pantalla.py dibuixa els formularis per a la guia de l'estudiant, i les
# seves definicions estan copiades a ma de les crides INPUT del PPL. Copiades
# a ma vol dir que es poden separar, i ja va passar: es va canviar l'ordre dels
# camps a pantalla.py i el PPL es va quedar com estava, aixi que la guia va
# ensenyar durant dies un formulari que l'app no tenia. Aqui es llegeixen les
# dues fonts i es comparen titol, etiquetes i geometria.
RE_INPUT = re.compile(
    r'INPUT\(\s*\{(.*?)\},\s*"([^"]+)",\s*\{(.*?)\},\s*\{(.*?)\}\s*\);', re.S)
RE_CAMP = re.compile(
    r'\{\s*\w+\s*,\s*(?:\[0\]|\w+)\s*,\s*'
    r'\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(\d+)\s*\}\s*\}')
# El costat Python: formulario('titol', [[fila], [fila]], 'ajuda'). Les files
# van entre [[ i ]], i cada camp es ('etiqueta', valor, x, ample) amb un valor
# que sol ser una crida amb comes a dins -- tsig(tc, 6) --, aixi que no serveix
# tallar per comes.
RE_FORM = re.compile(r"formulario\(\s*'([^']+)',\s*(\[\[.*?\]\])", re.S)
RE_CAMP_PY = re.compile(
    r"\(\s*'([^']*)'\s*,\s*(?:[^(),]|\([^()]*\))*,"
    r"\s*(-?\d+)\s*,\s*(-?\d+)\s*\)")


def _pantalles_ppl(fitxers):
    """{titol: [(etiqueta, x, ample, fila), ...]} de les INPUT del PPL."""
    out = {}
    for ruta in fitxers:
        txt = io.open(ruta, encoding='utf-8').read()
        for camps, titol, etiq, _ in RE_INPUT.findall(txt):
            pos = RE_CAMP.findall(camps)
            noms = re.findall(r'"([^"]*)"', etiq)
            out[titol] = [(noms[i], int(x), abs(int(a)), int(f))
                          for i, (x, a, f) in enumerate(pos)]
    return out


def _pantalles_py(ruta):
    """El mateix, llegit de les crides formulario() de tools/pantalla.py."""
    out = {}
    txt = io.open(ruta, encoding='utf-8').read()
    for titol, cos in RE_FORM.findall(txt):
        camps = []
        for fila, linia in enumerate(cos[1:-1].split('],')):
            for nom, x, a in RE_CAMP_PY.findall(linia):
                camps.append((nom, int(x), abs(int(a)), fila))
        out[titol] = camps
    return out


def barrido_pantalles():
    ppl = _pantalles_ppl([os.path.join(PPLDIR, n)
                          for n in ('TERMO.txt', 'GENER.txt')])
    py = _pantalles_py(os.path.join(TOOLS, 'pantalla.py'))
    for titol in sorted(set(ppl) | set(py)):
        a, b = ppl.get(titol), py.get(titol)
        if a is None:
            note(False, 'pantalla.py dibuixa "%s" i el PPL no la te' % titol)
        elif b is None:
            note(False, 'el PPL te la pantalla "%s" i la guia no la dibuixa'
                 % titol)
        else:
            note(a == b, 'la pantalla "%s" no coincideix: PPL %s vs guia %s' % (titol, a, b))
    return len(ppl)


# La linia d'ajuda d'INPUT la dibuixa el firmware al peu del dialeg, i com tot
# el que no hi cap a la Prime, es talla sense dir res: el text que sobra no
# existeix per a qui fa servir l'app. Aqui es limita la llargada.
#
# El numero surt de sobreestimar, que es l'unica manera honesta de decidir-ho
# des del PC: 320 px d'ample i un caracter ample de 7 px donen 45. Es fixa en
# 46 -- l'ajuda del volum molar en tenia 64 i a la calculadora es veia
# tallada. Les captures de la guia no serveixen per a aixo: pantalla.py
# dibuixa amb DejaVu, que no es la font de la calculadora.
MAX_AJUDA = 46


def barrido_ajudes():
    n = 0
    for f in ('TERMO.txt', 'GENER.txt'):
        txt = io.open(os.path.join(PPLDIR, f), encoding='utf-8').read()
        for camps, titol, etiq, aj in RE_INPUT.findall(txt):
            noms = re.findall(r'"([^"]*)"', etiq)
            ajudes = re.findall(r'"([^"]*)"', aj)
            note(len(ajudes) == len(noms),
                 '%s: %d etiquetes i %d ajudes' % (titol, len(noms),
                                                   len(ajudes)))
            for i, a in enumerate(ajudes):
                n += 1
                note(len(a) <= MAX_AJUDA,
                     '%s, camp "%s": ajuda de %d caracters i en caben %d: %r'
                     % (titol, noms[i] if i < len(noms) else '?', len(a),
                        MAX_AJUDA, a))
    return n


def main():
    kit = busca_interprete()
    if kit is None:
        print('SALTADO: no se encuentra hp-prime-kit (hpkit/interp.py).')
        print('  git clone https://github.com/JordiRigau/hp-prime-kit.git'
              ' ~/.claude/skills/hp-prime')
        return 0
    sys.path.insert(0, kit)
    from hpkit import interp

    m = interp.Machine()
    m.load_file(os.path.join(PPLDIR, 'GENER.txt'))
    m.load_file(os.path.join(PPLDIR, 'MENU.txt'))

    n = barrido_trpr(m)
    barrido_w(m)
    barrido_vr(m)
    tres = barrido_raiz(m)
    barrido_examens(m)
    barrido_menu(m)
    unic = prova_fitxer_unic(kit)
    npant = barrido_pantalles()
    najud = barrido_ajudes()

    for l in FAIL[:30]:
        print('  FALLA ' + l)
    print('-' * 70)
    print('rejilla (Tr,Pr) comparada: %d puntos' % n)
    print('variante de 1 elemento (estudiantes): %s'
          % ('comprobada' % () if unic else
             'SALTADA, no generada (gen_merged.py --all)'))
    print('pantallas comparadas PPL <-> guia: %d' % npant)
    print('lineas de ayuda de INPUT medidas: %d' % najud)
    print('casos con TRES raices en el barrido de raiz: %d' % tres)
    print('PASS: %d    FAIL: %d' % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
