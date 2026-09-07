# -*- coding: utf-8 -*-
"""El text de docs/GUIA_ESTUDIANT.pdf, en catala.

Separat de tools/gen_guia.py, que nomes porta la maquetacio i les pantalles.
Aixi el text es pot llegir i corregir sense passar per codi de dibuix.

To: es una referencia, no un fullet. Els titols NOMENEN, no narren; no s'hi
justifica per que una cosa es com es si al lector no li canvia res del que ha
de fer; i les frases de segona persona es reserven per a les instruccions.

Els numeros que hi surten NO estan escrits a ma: els calculen engine.py i
lk.py, i tools/pantalla.py els posa dins de les captures. Els que apareixen al
text de corregut estan copiats d'aquestes captures, i tests/test_guia.py
comprova que segueixen coincidint.

    python tools/gen_guia.py        (--png deixa cada pagina en un PNG)
"""
from __future__ import unicode_literals



# ================================================================ PORTADA
def portada(g, f):
    g.portada(
        'TAULES',
        "El llibre de taules de Termodinàmica, dins de l'HP Prime",
        ['Propietats de les 14 substàncies',
         'i mètodes generalitzats de Lee-Kesler',
         '', 'HP Prime G2'])
    g.y = 5.30
    g.imatge(f['menu'], ample=3.3)


# ================================================================ 1. QUE FA
def part_que_es(g, f):
    g.h1('1.  Què fa')
    g.par(
        'Consulta de propietats termodinàmiques. Cobreix les 14 substàncies '
        'del PDF de taules de l’assignatura —aigua, amoníac, CO₂, mercuri, '
        'cinc refrigerants i sis hidrocarburs— i els mètodes generalitzats '
        'de Lee-Kesler. Interpola linealment, com les taules de paper.')
    g.taula(
        ['Botó', 'Dóna', 'Quan'],
        [['1  TAULES', 'l’estat sencer d’una substància',
          'la substància és a taules'],
         ['2  GAS REAL', 'Z, v i les discrepàncies d’un estat',
          'l’enunciat dóna Tc, Pc i ω'],
         ['3  PROCÉS REAL', 'Δh, Δs i Δu entre dos estats',
          'ídem, per a un balanç']],
        [0.22, 0.44, 0.34])
    g.par(
        'Cada botó s’obre amb el dit o amb la tecla del seu número. A '
        'qualsevol pantalla: [Esc] torna enrere, [Help] obre l’ajuda i '
        '[View] obre el menú.')


# ============================================================ 2. INSTAL·LAR
def part_instal(g, f):
    g.h1('2.  Instal·lar-la', trenca=False)
    g.par('Un sol fitxer: la carpeta TAULES.hpappdir.')
    g.punts([
        'Instal·lar l’HP Connectivity Kit (hpcalcs.com/download) i '
        'connectar-hi la calculadora. Ha d’aparèixer a l’arbre de '
        'l’esquerra.',
        'Arrossegar la carpeta TAULES.hpappdir sencera A SOBRE de la '
        'calculadora, dins de la finestra del Connectivity Kit.',
        'A la calculadora: tecla [Apps] i icona TAULES.',
    ])

    g.h2('Comprovar que ha anat bé')
    g.par(
        'Tres entrades amb el resultat que han de donar. Si les tres '
        'surten, està instal·lada.')
    g.taula(
        ['Botó', 'Entrada', 'Ha de sortir'],
        [['1', 'Aigua, P=3, T=350', 'h = 3116.06   s = 6.7449'],
         ['2', 'Tc=305.3 Pc=4.87 w=0.099, T=793.78 P=14.61', 'Z = 1.0305'],
         ['3', 'Tc=280 Pc=5 w=0.09 cp*=0, 308/10 → 308/5',
          'ds = 17.3861 J/molK']],
        [0.10, 0.52, 0.38])

    g.h2('Si s’obre i no calcula')
    g.par(
        'Arrossegar-la ja la carrega, i normalment no cal res més. Però '
        'aquesta app porta les taules a dins i és gran, i hi ha constància '
        'que un programa prou gran pot necessitar que se’l compili un cop '
        'abans de funcionar. Si les tres proves de dalt no donen el que '
        'toca, cal entrar al catàleg de programes i compilar-la:')
    g.codi(['[Shift] [Program]  ->  TAULES  ->  Edit  ->  Check  ->  [Esc]'])
    g.par(
        'El «Check» és el que compila. Si respon «No errors in the '
        'program», ja està compilada i es torna a provar la taula de '
        'dalt.')


# ============================================================== 3. TAULES
def part_taules(g, f):
    g.h1('3.  Botó 1: TAULES')
    g.par(
        'De les set propietats —P, T, x, v, u, h, s— l’enunciat en dóna dues, '
        'i amb dues l’estat queda fixat. Es diu quines són i quant valen, i '
        'la pantalla dóna les set.')
    g.imatge(f['e1_form'], ample=2.5,
             peu='Els desplegables, quines magnituds; els camps, el valor.')
    g.punts([
        'El primer desplegable tria la substància.',
        '«Dada 1» i «Dada 2» trien la magnitud, amb la seva unitat.',
        'Els camps són numèrics: el nombre s’escriu sense cometes.',
        'L’ordre és indiferent: (h, P) i (P, h) donen el mateix.',
        'La pantalla recorda l’última combinació.',
    ])

    g.h2('Parells admesos')
    g.par(
        'Qualsevol parell de P, T, x, v, u, h i s, amb la condició que una '
        'de les dues sigui P o T. Els parells sense cap de les dues —(h, s), '
        '(u, v)— no s’accepten. El mercuri només admet parells que comencin '
        'per T. La temperatura té dues entrades, T [C] i T [K], i el '
        'resultat dóna sempre les dues.')

    g.h2('Avisos i errors')
    g.imatges2(f['t4_res'], f['t5_err'], ample=2.2,
               peu='Esquerra: avís taronja. Dreta: fora de rang.')
    g.punts([
        'Avís taronja ( ! ): el càlcul s’ha recolzat en la corba de '
        'saturació perquè una de les isòbares veïnes estava en una altra '
        'fase. El valor és bo, però l’aproximació és més grossera que '
        'la de la resta.',
        'Error vermell: la dada cau fora del rang tabulat i l’app no '
        'extrapola. Causes habituals: una unitat equivocada, un valor '
        'impossible a aquella pressió, o un parell no admès.',
    ])


# ============================================================ 4. GAS REAL
def part_gener(g, f):
    g.h1('4.  Botó 2: GAS REAL')
    g.par(
        'Per als enunciats que no donen cap substància sinó les seves '
        'constants: «un fluid del qual se sap Tc = 300 K, Pc = 5 MPa i '
        'ω = 0,089». És el mètode generalitzat, que l’enunciat també pot '
        'anomenar correlacions de Pitzer o funcions de discrepància.')
    g.par(
        'Tots els fluids es comporten aproximadament igual en coordenades '
        'reduïdes:')
    g.codi(['        Tr = T / Tc            Pr = P / Pc'])
    g.par(
        'i el factor de compressibilitat surt d’un únic gràfic, amb la '
        'correcció del factor acèntric ω:')
    g.codi(['        Z = Z0 + w * Z1'])
    g.par(
        'A mà són tres gràfics —un per a Z i un per a cada discrepància— i '
        'de cadascun, dues corbes: sis lectures per estat. La pantalla les '
        'dóna totes.')

    g.h2('Si la substància és a taules, no cal escriure res')
    g.par(
        'Hi ha preguntes que anomenen la substància i NO donen les seves '
        'constants: «s’expandeix isotèrmicament etilè» (30/10/2019) o '
        '«5 mol d’etilè… utilitzant mètodes generalitzats» (31/10/2024). '
        'El desplegable «Sust» del formulari les carrega de les taules: Tc, '
        'Pc, ω i M surten soles.')
    g.imatges2(f['g5_form'], f['g5_res'],
               peu='Triant Etilè, les constants no es teclegen.')
    g.par(
        'La capçalera ho diu: mentre digui un nom, les constants són les '
        'd’aquella substància. «(manual)» és el cas de la majoria de '
        'preguntes: les que donen un fluid sense nom.')

    g.h2('Quan cal escriure les constants')
    g.par(
        'Primer es demana el problema. Amb «(manual)» ve un segon formulari '
        'amb Tc, Pc, ω i M; amb una substància del desplegable no ve, perquè '
        'no falta res. Només es demana el que de veritat manca.')
    g.imatge(f['g_const'], ample=2.9,
             peu='Amb «(manual)»: aquest formulari; amb una substància, no.')
    g.par(
        'El cp* és a part i el demana només PROCÉS REAL, que és l’única '
        'pantalla que el fa servir. No surt mai de les taules: aquestes '
        'donen el fluid real, i el cp* és del gas ideal.')
    g.imatge(f['g_cp'], ample=2.9,
             peu='La fila es llegeix com la fórmula. Si cp* és constant, '
                 'b = 0.')
    g.taula(
        ['Camp', 'Què hi va', 'Unitat'],
        [['Tc', 'temperatura crítica', 'K'],
         ['Pc', 'pressió crítica', 'MPa'],
         ['w', 'factor acèntric ω; 0 si no el donen', '—'],
         ['M', 'massa molar; amb M > 0 també dóna valors per kg', 'g/mol'],
         ['cp* =', 'el terme constant, la a de cp* = a + b·T', 'J/(mol·K)'],
         ['+ T*', 'el pendent, la b; 0 si cp* és constant', 'J/(mol·K²)']],
        [0.16, 0.59, 0.25])

    g.h2('Exemple 1  ·  turbina de gas')
    g.par(
        'Parcial del 8 d’abril de 2026. Un gas entra a una turbina a '
        'Tr = 2,6 i Pr = 3. Dades: Tc = 305,3 K, Pc = 4870 kPa, ω = 0,099, '
        'cp* = 1,75 kJ/kg·K, R = 0,2765 kJ/kg·K.')
    g.par(
        'La Pc ve en kPa i el camp la vol en MPa: 4.87. L’entrada és '
        'T = 2,6 × 305,3 = 793,78 K i P = 3 × 4,87 = 14,61 MPa.')
    g.imatges2(f['g1_form'], f['g1_res'],
               peu='Les sis lectures dels tres gràfics.')
    g.par(
        'Els termes surten separats en 0 i 1, i després el combinat: són els '
        'mateixos nombres del gràfic, contrastables un per un.')

    g.h3('Signe de la discrepància')
    g.par(
        'La pantalla dóna h − h*, real menys gas ideal, negatiu a la zona '
        'útil. Molts apunts tabulen (h* − h)/RTc, el mateix nombre amb el '
        'signe canviat. Cada línia porta el conveni escrit.')

    g.h2('Si l’enunciat dóna Tr i Pr')
    g.par(
        'Amb Tc = 1 i Pc = 1 a les constants, els camps de T i P ja són Tr i '
        'Pr, i no cal multiplicar res.')
    g.imatges2(f['g2_const'], f['g2_form'],
               peu='Tc=1 i Pc=1: els camps de T i P són Tr i Pr.')

    g.h2('Exemple 2  ·  dipòsit rígid')
    g.par(
        'Parcial del 28 d’octubre de 2025. Un recipient rígid de 12 dm³ '
        'conté 144,3 mol d’un fluid a 345 K. Dades: Tc = 300 K, '
        'Pc = 7,5 MPa, ω = 0. Quina pressió hi ha a dins?')
    g.par(
        'La dada no és la pressió sinó el volum, '
        'v = 0,012 / 144,3 = 8,316e-5 m³/mol. S’escriu al camp «v» i la P es '
        'deixa tal com estigui: amb v > 0 la pressió passa a ser el '
        'resultat, en verd.')
    g.imatges2(f['g3_form'], f['g3_res'],
               peu='Amb v donat, la P és la incògnita.')
    g.par(
        'Surt P = 16,1373 MPa; a 315 K, 10,3608 MPa. La caiguda és '
        '−5,78 MPa, l’opció «−6 MPa» del test.')

    g.h2('Sense solució')
    g.par(
        'Un volum que cau dins de la campana no correspon a cap estat: allà '
        'l’equació dóna pressió negativa.')
    g.imatge(f['g4_res'], ample=2.9,
             peu='Dins de la campana no hi ha solució.')
    g.par(
        'Amb (T, P) això no pot passar. Si surt, l’error típic és haver '
        'posat el volum per kg en comptes de per mol.')


# ========================================================= 5. PROCES REAL
def part_disc(g, f):
    g.h1('5.  Botó 3: PROCÉS REAL')
    g.par(
        'El mateix mètode que el botó 2, per a dos estats. Aquesta és '
        'l’única diferència entre els dos botons: el 2 dóna un estat i el 3 '
        'el salt entre dos, que és el que demana el balanç.')
    g.par(
        'La recepta és anar-se’n al gas ideal restant la discrepància, fer '
        'el camí allà i tornar sumant la de l’estat 2:')
    g.codi([
        'dh = int cp* dT                  + (dh2 - dh1) * R * Tc',
        'ds = int cp*/T dT - R ln(P2/P1)  + (ds2 - ds1) * R',
        'du = dh - R * (Z2 T2 - Z1 T1)',
    ])

    g.h2('Exemple 3  ·  difusor adiabàtic')
    g.par(
        'Parcial del 9 d’abril de 2025. Un fluid es pressuritza en un '
        'difusor adiabàtic des de 50 bar i 300 K fins a 250 bar i 390 K, i '
        'hi entra a 300 m/s. Dades: M = 120 g/mol, Tc = 300 K, Pc = 5 MPa, '
        'ω = 0,089, cp* = 43 J/mol·K. Velocitat a la sortida?')
    g.imatges2(f['p1_form'], f['p1_res'],
               peu='Els dos estats i el salt, amb els valors per kg.')
    g.par(
        'Amb la massa molar posada, la pantalla afegeix la línia «per kg»: '
        'dh = 29,469 kJ/kg. El balanç del difusor és h1 + V1²/2 = h2 + V2²/2:')
    g.codi(['V2 = arrel(300^2 - 2 x 29469)  =  176,2 m/s'])
    g.par('La solució oficial és 174,1 m/s.')

    g.h2('Exemple 4  ·  procés isoterm')
    g.par(
        'Parcial del 2 de novembre de 2021. 10 mol d’un fluid en un '
        'cilindre-pistó adiabàtic, a 308 K constants, amb la pressió baixant '
        'de 10 a 5 MPa. Dades: Tc = 280 K, Pc = 5 MPa, ω = 0,09.')
    g.imatge(f['p2_res'], ample=2.9,
             peu='Amb T1 = T2 apareix la línia isoterma.')
    g.par(
        'Com que les dues temperatures són iguals, la pantalla afegeix '
        'q = T·ds = 5354,9 J/mol; si les iguals fossin les pressions, '
        'afegiria w = −P·dv. Les dues línies només surten quan la condició '
        'es compleix.')
    g.par(
        'D’aquí, ΔS de l’univers = 10 × 17,3861 = 173,9 J/K i el treball '
        'elèctric = 10 × 5354,9 = 53,55 kJ, totes dues oficials.')


# L'ordre del document.
SECCIONS = (portada, part_que_es, part_instal, part_taules,
            part_gener, part_disc)
