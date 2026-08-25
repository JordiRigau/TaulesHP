<img src="icon/icon_blau_x4.png" width="80" align="right" alt="icono">

# TermoHP — tablas de propiedades termodinámicas para HP Prime G2

App de consulta de propiedades termodinámicas para calculadora **HP Prime G2**.
Le das dos magnitudes cualesquiera de entre **P, T, x, v, u, h, s** y devuelve
el estado completo —las siete más la región— con **interpolación lineal, la
misma que se hace a mano en clase**.

Cubre las **14 sustancias** del PDF de tablas de la asignatura: agua, amoníaco,
CO₂, mercurio, cinco refrigerantes y seis hidrocarburos. Todo sale de ese PDF
de 80 páginas: **42.892 valores extraídos de forma determinista**, validados y
compilados a PPL.

> **El PDF de tablas no está en este repositorio.** Es material docente y no se
> redistribuye. Con él en la raíz del proyecto, un comando reconstruye los
> datos — ver [Rehacer todo desde el PDF](#rehacer-todo-desde-el-pdf).

```
Sust   [ R-718 (Aigua)          v]          →  T = 350.00 C  (623.15 K)
Dada 1 [ P [MPa]  v]  = [ 3        ]           P = 3 MPa      v = 0.090556
Dada 2 [ T [C]    v]  = [ 350      ]           h = 3116.06    s = 6.7449
                                               VAPOR SOBREESCALFAT
```

**Estado: terminado y en uso.** Funciona en una G2 real (firmware 2.4.15515),
1599 pruebas en verde —más 2223 si se ejecuta el PPL de verdad— y contrastado
contra las soluciones oficiales del profesor con una desviación máxima del
1,3 %.

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
```

Los datos **nunca se editan a mano**. Si un valor está mal, se corrige el
extractor o el maestro y se regenera todo.

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

**1599 comprobaciones en tres niveles**, porque cada uno ve cosas que los otros
no pueden ver:

| Nivel | Cuántas | Contra qué | Qué caza |
|---|---|---|---|
| Motor — `tests/test_engine.py` | 549 | nodos tabulados, tablas publicadas (Çengel/NIST) y el cálculo a mano rehecho aparte | errores de algoritmo |
| Capa de datos PPL — `tests/test_ppl_layout.py` | 1008 | replica la aritmética de índices de la calculadora | desfases de una fila, **en el PC y no en el examen** |
| Aceptación — `tests/test_aceptacion.py` | 42 | problemas ya resueltos, con su solución oficial | que la app **sirva**, no que sea coherente |

Y un cuarto que **ejecuta el PPL de verdad**:

| | |
|---|---|
| Conformidad — `tests/test_ppl_motor.py` | **2223** comprobaciones: interpreta `ppl/TERMOLIB.hpprgm` en el PC y lo compara con el motor de Python sobre casos sacados de los propios datos |

Caza lo que ninguno de los otros tres puede ver: que el PPL y el Python
**calculen cosas distintas**. Cada uno es coherente consigo mismo, los dos
pasan sus pruebas, y la app da un resultado que el PC no da. Necesita el
intérprete de [hp-prime-kit](https://github.com/JordiRigau/hp-prime-kit); si
no está instalado, se salta en vez de fallar.

Los datos se validan aparte con criterios independientes del extractor —no
«hizo lo que dice» sino «los números cumplen física conocida»—: **0 incidencias
estructurales o físicas**, y por el camino aparecieron **4 erratas del PDF
original**, todas en la tabla de mercurio.

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

Son **3 elementos** que se pegan una sola vez con el HP Connectivity Kit;
a partir de ahí, pasarlo a otra calculadora es arrastrar tres ficheros.

```bash
python tools/gen_merged.py --all
```

y pegar `TDAT.txt` → `TERMOLIB.txt` → `TAULES_APP_LIB.txt` en ese orden.
**El procedimiento completo, las variantes y la copia de seguridad están en
[`docs/INSTALACION.md`](docs/INSTALACION.md)**, y la comprobación de que ha
quedado bien en [`docs/PRUEBAS_CALCULADORA.md`](docs/PRUEBAS_CALCULADORA.md).

## Usar

Dos desplegables dicen **qué** magnitudes conoces y con qué unidad, dos campos
numéricos **cuánto**. El orden no importa, la pantalla recuerda la última
combinación, los dos últimos estados se guardan solos para dar el salto Δh, Δu,
Δs… entre ellos, y fuera del rango tabulado da error visible: **nunca
extrapola**. → [`docs/USO.md`](docs/USO.md)

## Dónde corre, cuánto ocupa y cómo va

Probado en **HP Prime G2, firmware 2.4.15515 (2025-09-15)**, en la calculadora
física y en el Virtual Calculator. En G1 no está probado.

| | |
|---|---|
| Datos, fuente PPL (14 sustancias) | 309 KB |
| **Datos, ya en la calculadora** | **978 KB** (×3,16) |
| Motor + interfaz, fuente | 30 KB |
| Números almacenados | 43.796 |

El binario ocupa más que el fuente porque la Prime guarda las matrices en su
propio formato numérico, no como texto. Frente a los 256 MB de RAM de la G2 es
un 0,4 %. Un efecto secundario útil: los datos viajan **ya compilados**, así que
a quien reciba la app le abre al instante.

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
           engine.py  gen_ppl.py  gen_merged.py  gen_pruebas.py
data/      master.json               ← única fuente de verdad (generada)
ppl/       TERMOLIB.hpprgm           ← motor        (escrito a mano)
           TERMO.hpprgm              ← interfaz     (escrito a mano)
           APP_TAULES.hpprgm         ← ganchos app  (escrito a mano)
           TDAT_*.hpprgm  txt/       ← por sustancia (GENERADO)
           compacte/                 ← versión de 2 y 3 elementos (GENERADO)
tests/     test_engine.py  test_ppl_layout.py  test_aceptacion.py
           test_ppl_motor.py         ← ejecuta el PPL (necesita hp-prime-kit)
docs/      ver abajo
icon/      icon_*.png                ← icono de la app (GENERADO)
```

Sólo `ppl/TERMOLIB`, `ppl/TERMO` y `ppl/APP_TAULES` están escritos a mano. Los
datos —`data/`, `ppl/TDAT_*`, `ppl/txt/` y `ppl/compacte/TDAT.txt`— se generan
desde el PDF y no se versionan; el resto de `ppl/compacte/` sí, para poder
instalar la app sin tener el PDF a mano.

## Documentación

| | |
|---|---|
| [`docs/ANALISIS.md`](docs/ANALISIS.md) | **el documento de referencia**: premisas corregidas, averías del PDF, determinación de región, estructura de datos, decisiones de UI, estrategia de pruebas y riesgos |
| [`docs/INSTALACION.md`](docs/INSTALACION.md) | montaje, variantes, transferencia y copia de seguridad |
| [`docs/USO.md`](docs/USO.md) | manual de la app |
| [`docs/API.md`](docs/API.md) | llamar al motor desde otra app de la Prime |
| [`docs/CHEATSHEET_PPL.md`](docs/CHEATSHEET_PPL.md) | PPL: lo que se usa aquí, las trampas y los límites no documentados |
| [`docs/PRUEBAS_CALCULADORA.md`](docs/PRUEBAS_CALCULADORA.md) | batería de casos para verificar la instalación (generada) |
| [`docs/PLANTEAMIENTO_INICIAL.md`](docs/PLANTEAMIENTO_INICIAL.md) | el plan de partida, sin corregir, para contrastar |

## Rehacer todo desde el PDF

Pon `Tablas_propiedades_individualizadas.pdf` en la raíz y:

```bash
python tools/extract_pdf.py && python tools/validate.py && python tools/gen_ppl.py --all && python tools/gen_merged.py --all && python tests/test_engine.py && python tests/test_ppl_layout.py && python tests/test_aceptacion.py && python tests/test_ppl_motor.py
```

Python 3.7+ y `pdfplumber` (ver [`requirements.txt`](requirements.txt)); el
motor y los tres bancos de pruebas no necesitan nada más que la stdlib. Sin el
PDF no se puede regenerar: el repositorio publica el código, no los datos.

## Pendiente

- La sección «C. Propietats generalitzades» del PDF (diagramas de
  compresibilidad) no está extraída; la app no la cubre.
- En los 35 huecos grandes, `v` se aleja del valor real por interpolar lineal.
  Es deliberado, no un error.
- 4 erratas del PDF en la tabla del mercurio, localizadas pero no corregidas:
  se dejan como están para no separarse de la fuente.

## Licencia

MIT — ver [`LICENSE`](LICENSE). El PDF de tablas y las soluciones de la
asignatura son material docente ajeno y no se incluyen.
