<img src="icon/icon_blau_x4.png" width="80" align="right" alt="icono">

# TermoHP — el libro de tablas de termodinámica, en la HP Prime G2

App para calculadora **HP Prime G2** que sustituye las dos mitades del libro de
tablas de la asignatura. Tres botones:

```
 1.  TAULES               propietats d'una substancia
 2.  GENERALITZADES       Z i discrepancies a (Tr,Pr)
 3.  DISCREPANCIA         proces 1->2:  dh, ds, du
```

**Propiedades de sustancia** (sección B del libro). Le das dos magnitudes
cualesquiera de entre **P, T, x, v, u, h, s** y devuelve el estado completo
—las siete más la región— con **interpolación lineal, la misma que se hace a
mano en clase**. Cubre las **14 sustancias** del PDF: agua, amoníaco, CO₂,
mercurio, cinco refrigerantes y seis hidrocarburos. **42.892 valores extraídos
de forma determinista** de esas 80 páginas, validados y compilados a PPL.

```
Sust   [ R-718 (Aigua)          v]          →  T = 350.00 C  (623.15 K)
Dada 1 [ P [MPa]  v]  = [ 3        ]           P = 3 MPa      v = 0.090556
Dada 2 [ T [C]    v]  = [ 350      ]           h = 3116.06    s = 6.7449
                                               VAPOR SOBREESCALFAT
```

**Métodos generalizados** (sección C). Sustituyen el diagrama de
compresibilidad y las dos cartas de funciones de discrepancia, que es lo que
sale en el parcial. **No llevan ninguna tabla dentro**: aquellas cartas son la
salida tabulada de la ecuación de Lee-Kesler, así que se evalúa la ecuación y
salen los mismos números con más cifras de las que se pueden leer en papel.

```
Tc=305.3 Pc=4.87 w=0.099        →  Tr = 2.6000     Pr = 3.0000
T [K]   = [ 793.78 ]               Z0 = 1.0137   Z1 = 0.1706
P[MPa]  = [ 14.61  ]               Z  = 1.0305
                                   (h-h*)/RTc:  0=-0.4217  1=0.3756
                                                = -0.3846
```

> **El PDF de tablas no está en este repositorio.** Es material docente y no se
> redistribuye. Con él en la raíz del proyecto, un comando reconstruye los
> datos — ver [Rehacer todo desde el PDF](#rehacer-todo-desde-el-pdf). Los
> generalizados no lo necesitan: no salen de ninguna tabla.

**Estado: las tablas, terminadas y en uso** en una G2 real (firmware
2.4.15515), contrastadas contra las soluciones oficiales del profesor con una
desviación máxima del 1,3 %. **Los generalizados, escritos y verificados en el
PC**, reproducen **las 21 preguntas** de Pitzer y funciones de discrepancia de
catorce años de exámenes —todas aciertan la opción del test— pero **todavía no
se han probado en la calculadora**. 1620 pruebas en verde, más 2590 si se
ejecuta el PPL de verdad.

---

## Cómo está hecho

```
Tablas_propiedades_individualizadas.pdf   (80 págs, no se redistribuye)
        │  tools/extract_pdf.py     extracción por geometría, sin LLM
        ▼
   data/master.json                 única fuente de verdad (generada)
        ├─► tools/validate.py       física conocida, no "hizo lo que dice"
        ├─► tools/engine.py         motor de referencia en Python
        └─► tools/gen_ppl.py        código PPL para la calculadora
                │
                ▼
        ppl/  motor + interfaz escritos a mano · datos generados
                │  tools/build_hp.py       linter + escritura del binario
                ▼
        ppl/build/dev/         TDAT · TERMOLIB · TAULES  (desarrollo)
        ppl/build/estudiants/  TAULES.hpappdir solo  (todo dentro)
                    (se arrastran a la calculadora)
```

Los datos **nunca se editan a mano**. Si un valor está mal, se corrige el
extractor o el maestro y se regenera todo.

Los generalizados van por su lado y no tocan el PDF, porque no tienen datos:

```
   ecuación de Lee-Kesler (24 constantes publicadas)
        ├─► tools/lk.py      motor de referencia en Python
        └─► ppl/GENER.txt    la misma ecuación en PPL, dentro de la app
                │
                └─► tests/test_ppl_gener.py   los dos, sobre la misma rejilla
```

## Los problemas que costaron el trabajo

Cada uno está medido y razonado en [`docs/ANALISIS.md`](docs/ANALISIS.md); aquí
va el resumen.

**El PDF no da tablas, da páginas.** Es texto nativo y dentro de cada bloque
las columnas están centradas con desviación menor de 0,2 pt, así que la
posición horizontal identifica la columna sin ambigüedad — pero primero hay que
encontrar el bloque. Las isóbaras vienen **en mosaico**: 228 tablas repartidas
en 49 páginas, en rejillas de 2×2 y 2×3. Hay que segmentar la página antes de
poder leer nada, el corte entre las dos tablas de una fila no puede ser el
punto medio de sus títulos (parte la tabla izquierda por la mitad) y el número
de columnas no es fijo. Resultado: **42.892 valores, cero avisos, reproducible
con un comando**, sin pasar por ningún modelo que pudiera inventarse una cifra.

**Seis averías silenciosas del PDF.** No dan ningún error: sólo producen
respuestas equivocadas. La peor, el signo `−` sale como palabra suelta en 109
sitios, lo que hacía leer **71 filas con el signo cambiado**. También decimales
partidos, filas reimpresas y un título sin dos puntos que se llevaba por
delante 12 tablas enteras.

**Siete premisas del planteamiento inicial resultaron falsas**, y tres cambiaron
la arquitectura entera: hay 14 sustancias y no una, las unidades de temperatura
cambian entre ellas, cuatro son mezclas zeotrópicas con 11 columnas en vez de
10, y sí hay datos de líquido comprimido. El contraste entre
[el planteamiento](docs/PLANTEAMIENTO_INICIAL.md) y
[el análisis](docs/ANALISIS.md) es buena parte de la historia del proyecto.

**El problema difícil no era el que parecía.** Se esperaba pelear con la rejilla
dentada; lo peligroso resultó ser que al interpolar entre dos isóbaras vecinas
una puede estar en **otra fase**. A 0,15 MPa y 115 °C el agua es vapor, pero la
isóbara de 0,20 MPa da líquido a esa misma temperatura: interpolar entre ambas
daría un número absurdo con pinta de razonable. Se detecta antes de interpolar
y se sustituye la vecina por el estado de saturación, avisando en pantalla.

**Dónde acaba el líquido y empieza el vapor dentro de una isóbara.** Se buscaba
por el salto de volumen específico, y cerca del punto crítico ese salto se
encoge: **10 isóbaras se quedaban sin rama de vapor**, entre ellas las del agua
a 17,5 y 20 MPa, que son presiones normales de ciclo Rankine. Y no es que el
umbral estuviera mal puesto — **no existe ninguno que sirva**: en el etileno a
5,0 MPa el cambio de fase es un ×1,45 y el paso siguiente, que no es cambio de
fase, es un ×1,68. Ahora el corte se busca por la temperatura de saturación
repetida, y el volumen sólo se usa en las mezclas zeotrópicas, donde hay
deslizamiento y la T no se repite.

**PPL: cinco rondas de compilación por un límite no documentado.** El
compilador señalaba la línea del `LOCAL` sin decir qué sobraba, y como el error
no se movía cada hipótesis parecía plausible. Lo que lo resolvió fue dejar de
razonar sobre la sintaxis y **medir programas que ya funcionaban en esa misma
calculadora**: el límite son **7-8 variables por sentencia `LOCAL`**, y las
funciones que fallaban declaraban 13, 16 y 18. Las cuatro hipótesis falsas que
se descartaron por el camino están anotadas para no repetirlas →
[`docs/CHEATSHEET_PPL.md`](docs/CHEATSHEET_PPL.md).

## Pruebas

**1620 comprobaciones en cuatro niveles**, porque cada uno ve cosas que los
otros no pueden ver:

| Nivel | Cuántas | Contra qué | Qué caza |
|---|---|---|---|
| Motor — `tests/test_engine.py` | 549 | nodos tabulados, tablas publicadas (Çengel/NIST) y el cálculo a mano rehecho aparte | errores de algoritmo |
| Capa de datos PPL — `tests/test_ppl_layout.py` | 1008 | replica la aritmética de índices de la calculadora | desfases de una fila, **en el PC y no en el examen** |
| Aceptación tablas — `tests/test_aceptacion.py` | 42 | problemas ya resueltos, con su solución oficial | que la app **sirva**, no que sea coherente |
| Aceptación generalizados — `tests/test_lk_examenes.py` | 21 | las preguntas de Pitzer y discrepancias de catorce años de exámenes | lo mismo, para la otra mitad |

Y dos que **ejecutan el PPL de verdad**:

| | |
|---|---|
| Conformidad tablas — `tests/test_ppl_motor.py` | **2223** comprobaciones: interpreta `ppl/TERMOLIB.txt` en el PC y lo compara con el motor de Python sobre casos sacados de los propios datos |
| Conformidad generalizados — `tests/test_ppl_gener.py` | **367**: la rejilla entera del diagrama, `ppl/GENER.txt` contra `tools/lk.py`, ocho preguntas de examen resueltas enteras con las funciones del PPL, y la geometría del menú de botones |

Cazan lo que ninguno de los otros puede ver: que el PPL y el Python
**calculen cosas distintas**. Cada uno es coherente consigo mismo, los dos
pasan sus pruebas, y la app da un resultado que el PC no da. Necesitan el
intérprete de [hp-prime-kit](https://github.com/JordiRigau/hp-prime-kit); si
no está instalado, se saltan en vez de fallar.

Los datos se validan aparte con criterios independientes del extractor —no
«hizo lo que dice» sino «los números cumplen física conocida»—: **0 incidencias
estructurales o físicas**, y por el camino aparecieron **4 erratas del PDF
original**, todas en la tabla de mercurio.

### Los generalizados, contra catorce años de exámenes

Las 21 preguntas de Pitzer y funciones de discrepancia que hay en el archivo,
de 2012 a 2026. **La respuesta correcta se lee del PDF, no se teclea**: son
tipo test y la solución oficial marca la opción buena en negrita, que sobrevive
a la extracción.

**Las 21 aciertan la opción.** La desviación respecto al número oficial tiene
mediana **0,10 %**, 14 dentro del 0,2 % y 18 dentro del 1 %; la mayor es 6,6 %
en una pregunta cuya alternativa más cercana está a un factor 2,5, y la
solución oficial se sacó leyendo el gráfico a ojo — que es justo la precisión
que se está midiendo. Dos avisos honestos sobre este banco (constantes críticas
que el enunciado no da, y opciones por parejas) están en
[`docs/ANALISIS.md`](docs/ANALISIS.md#7-métodos-generalizados-por-qué-no-hacen-falta-datos).

El arnés que ejecuta el PPL encontró además **un agujero que tenían los dos
motores a la vez**: con `(T, v)` dentro de la campana la ecuación da presión
negativa, y la discrepancia de entropía lleva un `ln Z` que con ese número
revienta en Python — y en la calculadora podría devolver un complejo y seguir,
que es un resultado resuelto y equivocado. Ahora los dos lo rechazan antes.

### Lo que destapó la prueba de aceptación

Rehace de principio a fin un **ciclo Rankine** con recalentamiento y
regeneración (11 consultas encadenadas, error que se arrastra de una a otra:
sale al **1,3 %**) y un **ciclo frigorífico de R-134a en dos etapas** (al
**0,63 %**). Las soluciones oficiales están resueltas con EES, con propiedades
de fluido real en vez de interpolación en tabla, así que esa desviación es el
techo, no una estimación optimista.

Encontró **dos fallos que los otros 1557 tests no podían ver**, porque el motor
era coherente consigo mismo en ambos: la región supercrítica sin contemplar
(30 isóbaras de 6 sustancias) y el corte líquido/vapor por salto de volumen.
Los dos hacían que la app **diera error en vez de un número**; ninguno devolvía
un resultado equivocado.

## Una limitación deliberada

La app interpola **siempre lineal, `v` incluida**: primero en T dentro de cada
isóbara, después en P entre isóbaras. Exactamente lo que se hace a mano.

No es lo más exacto y se sabe por qué: `v` no es lineal en P sino casi
hiperbólica (`v ≈ ZRT/P`), así que donde el PDF pega un salto grande la recta se
queda lejos. Medido sobre el espaciado real de las tablas, la diferencia entre
interpolar en P y en 1/P va del **0,26 % en el 55 % de los casos** al **10 % en
los 35 huecos grandes** (de 214 pares de isóbaras).

Se ha elegido reproducir el método y no corregirlo, porque **el número que da la
app tiene que ser el que se puede justificar en el papel**. De poco sirve un
resultado más exacto que no cuadra con la interpolación que uno acaba de
escribir a mano. Hay un caso conocido donde se nota —amoníaco a 2,5 MPa, un 8 %
frente a la solución oficial— y está anotado como limitación en vez de
disimulado. El desglose completo está en
[`docs/ANALISIS.md`](docs/ANALISIS.md#6-estrategia-de-pruebas).

---

## Instalar

Se genera en el PC y se **arrastra** a la calculadora en la ventana del HP
Connectivity Kit. Hay dos montajes del mismo código:

```bash
python tools/gen_merged.py --all     # fuentes PPL
python tools/build_hp.py --tot       # 1 fichero: TAULES.hpappdir   ← repartir
python tools/build_hp.py             # 3: TDAT · TERMOLIB · TAULES  ← desarrollar
```

**Para repartir**, `--tot` mete los datos y el motor dentro de la app: se
arrastra un solo fichero y desaparece el fallo de instalación más fácil de
cometer, que es el orden.

**Para desarrollar**, el montaje de 3 deja el motor en un programa del
catálogo, donde **otra app puede llamarlo** (ver [`docs/API.md`](docs/API.md)),
y el programa de la app sigue siendo lo bastante pequeño para abrirlo en la
calculadora. Se arrastran en este orden: `TDAT` → `TERMOLIB` → `TAULES`.

`build_hp.py` necesita
[hp-prime-kit](https://github.com/JordiRigau/hp-prime-kit), que es quien
escribe el contenedor `.hpprgm` desde el PC, y pasa antes el linter sobre todo
lo que va a escribir. Sin el kit queda la ruta de siempre —pegar el texto en
el editor del CK—, que sigue documentada.

**El procedimiento completo, las variantes y la copia de seguridad están en
[`docs/INSTALACION.md`](docs/INSTALACION.md)**, y la comprobación de que ha
quedado bien en [`docs/PRUEBAS_CALCULADORA.md`](docs/PRUEBAS_CALCULADORA.md).

## Usar

Al abrir sale el menú de tres botones. Cada uno responde **al dedo y a su
tecla**, que va dibujada dentro.

**Tablas.** Dos desplegables dicen **qué** magnitudes conoces y con qué unidad,
dos campos numéricos **cuánto**. El orden no importa, la pantalla recuerda la
última combinación, y fuera del rango tabulado da error visible: **nunca
extrapola**.

**Generalizados.** Las constantes del fluido se ponen una vez y se recuerdan, y
la cabecera las repite en pantalla — que es lo que impide arrastrar la Tc del
problema anterior sin enterarte. Si en vez de la presión conoces el **volumen
molar**, lo escribes y la presión pasa a ser el resultado: es el depósito
rígido, que a mano obliga a tantear.

→ [`docs/USO.md`](docs/USO.md)

## Dónde corre, cuánto ocupa y cómo va

Probado en **HP Prime G2, firmware 2.4.15515 (2025-09-15)**, en la calculadora
física y en el Virtual Calculator. En G1 no está probado.

| | |
|---|---|
| Datos, fuente PPL (14 sustancias) | 309 KB |
| Datos, `.hpprgm` que se arrastra | 619 KB (el fuente en UTF-16) |
| **Datos, ya en la calculadora** | **978 KB** (×3,16) |
| Motor + interfaz + generalizados, fuente | 55 KB |
| Números almacenados | 43.796 |

El fichero que se arrastra ocupa el doble que el texto porque dentro va en
UTF-16; y en la calculadora ocupa aún más porque la Prime añade las matrices
**en su propio formato numérico**, además del fuente. Frente a los 256 MB de
RAM de la G2 es un 0,4 %.

Ese bloque compilado es **una caché que la calculadora rehace desde el
fuente** —medido cambiando un número dentro y viendo cómo lo reconstruía—, así
que `TDAT` no hay que pegarlo ni generarle nada: se escribe como cualquier
otro programa. Lo que aún no ha cronometrado nadie es cuánto tarda en
compilar 43.796 números al llegar. Quien lo copie **desde otra calculadora**
lo recibe con la caché ya hecha y no espera nada.

Todo el acceso es **búsqueda binaria sobre matriz**, nunca recorrido lineal: la
matriz mayor son las 1.540 filas de isóbaras del agua, o sea **11 comparaciones
como mucho**. Una interpolación doble es instantánea; lo más lento es la
búsqueda inversa (60 iteraciones de bisección), que se nota pero queda por
debajo del segundo.

### Lo que impuso la calculadora

Restricciones reales de PPL que dieron forma al diseño, todas en
[`docs/CHEATSHEET_PPL.md`](docs/CHEATSHEET_PPL.md):

| Limitación | Qué obligó a hacer |
|---|---|
| Máx. 7-8 variables por `LOCAL` | declararlas en grupos de 6 |
| No hay excepciones | convenio propio: región `-1` + mensaje, `{}` en las funciones que devuelven listas |
| No se puede indexar el retorno de una llamada | `d := DIM(M); n := d(1);` en vez de `DIM(M)(1)` |
| `INPUT` construye sus etiquetas una sola vez | la temperatura ofrece `[C]` y `[K]` fijas, en vez de una etiqueta que dependa de la sustancia |
| Una app en blanco no tiene vista donde reposar | el menú se dibuja en pantalla, no cuelga de `[View]` |
| Lo exportado por el programa de una app queda ligado a esa app | el motor vive en un programa del catálogo, para poder reutilizarlo |
| Matrices y listas 1-based | los índices se generan ya en base 1, y hay 1008 pruebas que lo verifican |

---

## Estructura

```
tools/     extract_pdf.py  pdfcommon.py  model.py  validate.py
           engine.py                 ← motor de tablas (Python)
           lk.py                     ← motor de generalizados (Python)
           gen_ppl.py  gen_merged.py  gen_pruebas.py
           pantalla.py  guia_text.py  gen_guia.py
                                     ← la guía en PDF para estudiantes
           build_hp.py               ← los binarios que se arrastran
data/      master.json               ← única fuente de verdad (generada)
ppl/       TERMOLIB.txt              ← motor tablas   (escrito a mano)
           TERMO.txt                 ← interfaz       (escrito a mano)
           GENER.txt                 ← generalizados  (escrito a mano)
           MENU.txt                  ← menú de botones(escrito a mano)
           APP_TAULES.txt            ← ganchos app    (escrito a mano)
           TDAT_*.txt                ← por sustancia (GENERADO)
           compacte/                 ← los tres montajes (GENERADO)
           build/                    ← .hpprgm y .hpappdir (GENERADO)
tests/     test_engine.py  test_ppl_layout.py  test_aceptacion.py
           test_lk_examenes.py       ← generalizados contra examen
           test_ppl_motor.py         ← ejecuta el PPL (necesita hp-prime-kit)
           test_ppl_gener.py         ← ídem, generalizados
           test_guia.py              ← que la guía no cite números viejos
docs/      ver abajo
icon/      icon_*.png                ← icono de la app (GENERADO)
```

Los cinco `.txt` de `ppl/` marcados arriba están escritos a mano. Los
datos —`data/`, `ppl/TDAT_*` y `ppl/compacte/TDAT.txt`— se generan desde el PDF
y no se versionan; el resto de `ppl/compacte/` sí, para poder instalar la app
sin tener el PDF a mano. `ppl/build/` tampoco se versiona: se rehace en medio
segundo desde `compacte/`.

En `ppl/` todo es **texto**: son fuentes PPL. Los `.hpprgm` de verdad —el
contenedor binario que entiende la calculadora— sólo aparecen en `ppl/build/`,
escritos por `build_hp.py`.

## Documentación

| | |
|---|---|
| [`docs/ANALISIS.md`](docs/ANALISIS.md) | **el documento de referencia**: premisas corregidas, averías del PDF, determinación de región, estructura de datos, decisiones de UI, estrategia de pruebas y riesgos |
| [`docs/INSTALACION.md`](docs/INSTALACION.md) | montaje, variantes, transferencia y copia de seguridad |
| [`docs/GUIA_ESTUDIANT.pdf`](docs/GUIA_ESTUDIANT.pdf) | **guía para estudiantes**, en catalán: 17 páginas con siete ejemplos resueltos y las pantallas paso a paso (generada) |
| [`docs/USO.md`](docs/USO.md) | manual de la app: las tablas y los dos métodos generalizados |
| [`docs/API.md`](docs/API.md) | llamar al motor desde otra app de la Prime |
| [`docs/CHEATSHEET_PPL.md`](docs/CHEATSHEET_PPL.md) | PPL: lo que se usa aquí, las trampas y los límites no documentados |
| [`docs/PRUEBAS_CALCULADORA.md`](docs/PRUEBAS_CALCULADORA.md) | batería de casos para verificar la instalación (generada) |
| [`docs/PLANTEAMIENTO_INICIAL.md`](docs/PLANTEAMIENTO_INICIAL.md) | el plan de partida, sin corregir, para contrastar |

## La guía para estudiantes

[`docs/GUIA_ESTUDIANT.pdf`](docs/GUIA_ESTUDIANT.pdf) — 17 páginas en catalán
para quien cursa la asignatura por primera vez y no ha visto nunca la
calculadora: qué hace y qué **no** hace, cómo instalarla, y siete ejemplos
resueltos paso a paso, cuatro de ellos preguntas reales de parcial.

```bash
python tools/gen_guia.py          # --png deja además cada página suelta
```

**Las capturas de pantalla no son fotos: se dibujan.** `tools/pantalla.py`
reproduce cada `TEXTOUT_P` con sus coordenadas y **pide los números a los
motores**, así que la guía no puede enseñar un valor que la app no dé. Lo
único transcrito a mano son las coordenadas, y por eso el colofón dice que
son reproducciones.

El texto de corrido es otra cosa: frases como *«w = 3116,06 − 2403,01 =
713,05 kJ/kg»* llevan cifras escritas a mano y se quedarían viejas en
silencio. `tests/test_guia.py` recorre la guía con un `Guia` de mentira que
apunta en vez de pintar y **cuenta** cada cifra citada contra lo que dan
`engine.py` y `lk.py`. Cuenta, no busca: con «está o no está» la prueba pasaba
igual tras torcer un número a propósito, porque varias cifras aparecen dos
veces —en la frase y en el pie de la captura—.

## Rehacer todo desde el PDF

Pon `Tablas_propiedades_individualizadas.pdf` en la raíz y:

```bash
python tools/extract_pdf.py && python tools/validate.py && python tools/gen_ppl.py --all && python tools/gen_merged.py --all && python tools/gen_pruebas.py && python tests/test_engine.py && python tests/test_ppl_layout.py && python tests/test_aceptacion.py && python tests/test_lk_examenes.py && python tests/test_ppl_motor.py && python tests/test_ppl_gener.py && python tools/gen_guia.py && python tests/test_guia.py && python tools/build_hp.py
```

Termina en `build_hp.py`, que pasa el linter y deja los ficheros listos para
arrastrar en la carpeta de su variante: `ppl/build/dev/` los tres,
`ppl/build/estudiants/` el único. Si no está el kit, ese último paso y las dos
pruebas `test_ppl_*` se saltan con un aviso y el resto sigue igual. Los
generalizados no dependen del PDF: `test_lk_examenes.py` corre siempre.

Python 3.7+ y `pdfplumber` (ver [`requirements.txt`](requirements.txt)); el
motor y los tres bancos de pruebas no necesitan nada más que la stdlib. Sin el
PDF no se puede regenerar: el repositorio publica el código, no los datos.

## Pendiente

- La sección «C. Propietats generalitzades» del PDF no está extraída, y **ya no
  hace falta**: los diagramas se calculan con Lee-Kesler (`ppl/GENER.txt`), que
  es la ecuación con la que se tabularon. Lo que sigue fuera es la sección A
  —entalpías de formación y entalpías sensibles—, que es lo que necesitaría una
  pantalla de combustión.
- En los 35 huecos grandes, `v` se aleja del valor real por interpolar lineal.
  Es deliberado, no un error.
- 4 erratas del PDF en la tabla del mercurio, localizadas pero no corregidas:
  se dejan como están para no separarse de la fuente.

## Licencia

MIT — ver [`LICENSE`](LICENSE). El PDF de tablas y las soluciones de la
asignatura son material docente ajeno y no se incluyen.
