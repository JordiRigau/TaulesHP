<img src="icon/icon_blau_x4.png" width="80" align="right" alt="icono">

# TermoHP — tablas de propiedades termodinámicas para HP Prime G2

App de consulta de propiedades termodinámicas para calculadora **HP Prime G2**:
14 sustancias (agua, amoníaco, R-134a, refrigerantes, hidrocarburos, CO₂,
mercurio). Das dos magnitudes cualesquiera y devuelve el estado completo —
T, P, v, u, h, s, x y la región— con interpolación lineal, la misma que se hace
a mano en clase.

Todo sale de un PDF de 80 páginas de tablas: **42.892 valores extraídos de forma
determinista**, validados, y compilados a PPL.

> **El PDF de tablas no está en este repositorio.** Es material docente y no se
> redistribuye. Con él en la raíz del proyecto, un comando reconstruye los datos
> (ver [Rehacer todo desde el PDF](#rehacer-todo-desde-el-pdf)).

## Lo que tiene de interesante

**La extracción no usa ningún LLM**, y no porque el PDF fuera fácil. Es texto
nativo, y dentro de cada bloque las columnas están centradas con una desviación
menor de 0,2 pt: eso hace que la posición horizontal identifique la columna sin
ambigüedad. Pero **primero hay que encontrar el bloque**, y ahí está el trabajo:

- Las isóbaras vienen **en mosaico**: 228 tablas repartidas en 49 páginas, en
  rejillas de 2×2 y 2×3 — 4,7 tablas por página. Hay que segmentar la página
  antes de poder leer nada.
- El corte entre las dos tablas de una fila **no puede ser el punto medio de
  sus títulos**: eso parte la tabla izquierda por la mitad. Se deduce de las
  propias columnas numéricas, partiendo entre la quinta y la sexta.
- El número de columnas **no es fijo**: 10 en sustancias puras y 11 en las
  mezclas zeotrópicas. Se lee de la cabecera, porque fijarlo corrompía cuatro
  sustancias en silencio.
- Dentro de cada isóbara está el **salto de fase**, con su fila de líquido y su
  fila de vapor. En 176 de las 228 tablas, y hay que localizarlo para no
  interpolar a través de él.

Lo que sí es determinista y exacto es el resultado: 42.892 valores, cero
avisos, reproducible con un comando. Donde un modelo sólo podría igualarlo y
añadiría el riesgo de inventarse una cifra.

**Seis averías silenciosas del PDF**, que no dan ningún error y sólo producen
respuestas equivocadas. La peor: el signo `−` sale como palabra suelta en 109
sitios, lo que hacía leer **71 filas con el signo cambiado**. Están todas en
[`docs/ANALISIS.md`](docs/ANALISIS.md) §2.

**Cuatro erratas del PDF original** localizadas por el validador, todas en la
tabla de mercurio.

**Siete premisas del planteamiento inicial resultaron falsas** y tres cambiaron
la arquitectura entera: hay 14 sustancias y no una, las unidades cambian entre
ellas, cuatro son mezclas zeotrópicas con 11 columnas en vez de 10, y sí hay
datos de líquido comprimido. El contraste entre
[el planteamiento](docs/PLANTEAMIENTO_INICIAL.md) y
[el análisis](docs/ANALISIS.md) es buena parte de la historia.

**El índice de líquido y vapor no se puede detectar por la T repetida.** En una
sustancia pura las dos filas de saturación comparten temperatura, pero en las
mezclas zeotrópicas hay deslizamiento y están a T **distintas** — en R-404A a
0,14 MPa, burbuja a −39,24 °C y rocío a −38,53 °C. De las 176 isóbaras con
salto de fase, **109 repiten la T y 67 no**. Se detecta por el salto de volumen
específico, que es de tres órdenes de magnitud en ambos casos, y cada isóbara
guarda cuántas filas son de la rama líquida para no volver a buscarlo en cada
consulta.

**El problema difícil no era el que parecía.** No es la rejilla dentada, sino
que al interpolar entre dos isóbaras vecinas una puede estar en **otra fase**:
a 0,15 MPa y 115 °C el agua es vapor, pero la isóbara de 0,20 MPa da líquido a
esa misma temperatura. Interpolar entre ambas daría un número absurdo con pinta
de razonable.

**1599 pruebas** en tres niveles: 549 del motor contra nodos tabulados, tablas
publicadas y el cálculo a mano rehecho aparte, 1008 de la capa de datos PPL
—que replica la aritmética de índices de la calculadora para cazar desfases de
una fila **en el PC y no en el examen**— y **42 de aceptación contra problemas
ya resueltos**, con su solución oficial.

**La prueba de aceptación encontró dos fallos que los otros 1557 tests no
podían ver**, porque el motor era coherente consigo mismo en los dos. Los dos
hacían que la app diera **error en vez de un número**; ninguno devolvía un
resultado equivocado:

1. **Por encima de la presión crítica no hay curva de saturación**, y la
   determinación de región se caía. Afectaba a 30 isóbaras de 6 sustancias,
   14 de ellas del agua (25 a 100 MPa) — presiones de ciclo Rankine
   supercrítico, nada exótico.
2. **El corte líquido/vapor de cada isóbara se buscaba por el salto de
   volumen.** Cerca del punto crítico ese salto se encoge y **10 isóbaras se
   quedaban sin rama de vapor**, incluidas las del agua a 17,5 y 20 MPa: a esas
   presiones, cualquier consulta de vapor sobrecalentado fallaba. Se busca
   ahora por la temperatura de saturación repetida.

Los dos están medidos y razonados en
[`docs/ANALISIS.md`](docs/ANALISIS.md#6-estrategia-de-pruebas).

**El port a PPL, documentado**: cinco intentos hasta dar con el límite de
variables por `LOCAL`, con las cuatro hipótesis falsas que se descartaron por el
camino → [`docs/CHEATSHEET_PPL.md`](docs/CHEATSHEET_PPL.md).

## Dónde corre, cuánto ocupa y cómo va

**Probado en HP Prime G2, firmware 2.4 revisión 15515 (2025-09-15)**, tanto en
la calculadora física como en el Virtual Calculator. Las notas de esa versión
no tocan la sintaxis de PPL, así que debería funcionar igual en revisiones
cercanas. En **G1 no está probado**: el hardware es más lento y tiene menos
memoria, aunque el firmware es el mismo — si alguien lo prueba, me interesa
saberlo.

### Tamaño

| | |
|---|---|
| Fuente PPL de los datos (14 sustancias) | 309 KB |
| **Ya en la calculadora** | **978 KB** |
| Motor + interfaz | 60 KB |
| Números almacenados | 43.796 |

El binario ocupa **3,16 veces** el fuente porque la Prime guarda las matrices
en su propio formato numérico, no como texto. Frente a los 256 MB de RAM de la
G2 es irrelevante — un 0,4 %.

Un efecto secundario útil: los datos viajan **ya compilados**. Quien reciba la
app no espera ninguna compilación, le abre al instante.

### Rendimiento

Todo el acceso es **búsqueda binaria sobre matriz**, nunca recorrido lineal:

- La matriz mayor son las 1.540 filas de isóbaras del agua → **11 comparaciones
  como mucho** para localizar el intervalo.
- Una interpolación doble son 2 búsquedas y 12 multiplicaciones. Instantánea.
- La búsqueda inversa (dado *h* o *s*, hallar *T*) hace **60 iteraciones de
  bisección**, cada una con su doble interpolación. Se nota, pero por debajo
  del segundo.
- Lo más lento es **cambiar de sustancia**: `TLOAD` copia las matrices. Por eso
  sólo se recarga si el índice cambió de verdad.

### Lo que impone la calculadora

Restricciones reales de PPL que dieron forma al diseño, todas documentadas en
[`docs/CHEATSHEET_PPL.md`](docs/CHEATSHEET_PPL.md):

| Limitación | Qué obligó a hacer |
|---|---|
| **Máx. 7-8 variables por `LOCAL`** | declararlas en grupos de 6 |
| **No hay excepciones** | convenio propio: región `-1` + mensaje, y `{}` en las funciones que devuelven listas |
| **No se puede indexar el retorno de una llamada** | `d := DIM(M); n := d(1);` en vez de `DIM(M)(1)` |
| **`INPUT` construye sus etiquetas una sola vez** | la temperatura ofrece `[C]` y `[K]` fijas, en vez de una etiqueta que dependa de la sustancia |
| **Una app en blanco no tiene vista donde reposar** | el menú se dibuja en pantalla, no cuelga de `[View]` |
| **Lo exportado por el programa de una app queda ligado a esa app** | el motor vive en un programa del catálogo, para poder reutilizarlo |
| **Matrices y listas 1-based** | los índices se generan ya en base 1, y hay 1008 pruebas que lo verifican |

## Estado

| Pieza | Estado |
|---|---|
| Extracción del PDF (42.892 valores, 14 sustancias) | ✅ determinista, 0 avisos |
| Validación de datos | ✅ 0 incidencias; 4 erratas del PDF localizadas |
| Motor de referencia en Python | ✅ 517 pruebas en verde |
| Capa de datos PPL (índices, ramas) | ✅ 1008 pruebas en verde |
| Código PPL en la calculadora | ✅ funcionando en G2, firmware 2.4.15515 |
| Contraste con soluciones oficiales | ✅ 42 comprobaciones en verde, desviación máxima 1,3 % |

---

## Instalar

Son **3 elementos**. Se pegan una sola vez; a partir de ahí todo se hace
arrastrando.

> **Por qué hay que pegar la primera vez:** `.hpprgm` es un formato binario
> (cabecera `7C 61 8A B2`, tabla de símbolos, fuente en UTF-16LE). Los ficheros
> de `ppl/` son texto y el Connectivity Kit los rechaza si los arrastras. El
> binario lo tiene que escribir él, y sólo lo hace al guardar un programa.

1. Instala el **HP Connectivity Kit** — <https://hpcalcs.com/download/>
2. Conecta la calculadora (o abre el Virtual Calculator) y ábrelo. Aparece en
   el árbol de la izquierda; si sale en gris, doble clic.
3. Genera los ficheros: `python tools/gen_merged.py --all`
4. Crea cada programa con **clic derecho → Nuevo** sobre *Program*, con el
   nombre exacto, y pega dentro el `.txt`:

   | Nombre | Pegar | KB | Qué es |
   |---|---|---|---|
   | `TDAT` | `ppl/compacte/TDAT.txt` | 309 | las 14 sustancias |
   | `TERMOLIB` | `ppl/compacte/TERMOLIB.txt` | 15 | motor de cálculo |

5. Crea la app: `[Apps]` → tecla **(Save)** → *Base App*: **None** → nombre
   **`TAULES`** → OK. Selecciónala, pulsa `[Shift][1]` y `[▲]` para llegar a su
   programa, y pega `ppl/compacte/TAULES_APP_LIB.txt`.
6. `[Apps]` → icono `TAULES`.

**El orden importa**: un programa sólo ve las funciones de otro si se compiló
después. `TDAT` → `TERMOLIB` → la app.

<details>
<summary>Variantes</summary>

`gen_merged.py` deja cuatro ficheros en `ppl/compacte/`:

- **3 elementos** (recomendada): `TDAT` + `TERMOLIB` + `TAULES_APP_LIB`. El
  motor vive en un programa del catálogo, así que **otra app puede llamarlo**.
- **2 elementos**: `TDAT` + `TAULES_APP` (motor dentro de la app). Un elemento
  menos, pero lo exportado desde el programa de una app queda ligado a esa app
  y deja de ser reutilizable.

Y en `ppl/txt/` está la versión por sustancia (un fichero cada una), por si
quieres cargar sólo algunas: `python tools/gen_ppl.py --list` las enumera.

Si cambias de variante, **borra antes los programas de la anterior**: dejarlos
daría nombres globales duplicados.

</details>

---

## Uso

```
Sust   [ R-718 (Aigua)          v]
Dada 1 [ P [MPa]  v]  = [ 3        ]
Dada 2 [ T [C]    v]  = [ 350      ]
```

Los desplegables dicen **qué** dos magnitudes conoces y **con qué unidad**; los
campos numéricos, su valor. Se escribe el número tal cual, sin comillas, y el
orden no importa: (h,P) vale lo mismo que (P,h).

**La temperatura tiene dos entradas, `T [C]` y `T [K]`**: eliges la escala que
tengas y la calculadora convierte a la de la tabla. Cada sustancia está
tabulada en una (agua y refrigerantes en °C; metano, etano, propano, etileno,
benceno, CO₂ y mercurio en K), pero **no necesitas saber cuál**: los resultados
dan siempre las dos.

> Se hizo así porque `INPUT` construye sus etiquetas **una sola vez**: es un
> diálogo modal, así que una unidad que dependiera de la sustancia no podría
> refrescarse al cambiarla dentro del formulario. Ofreciendo las dos, la
> etiqueta no tiene que cambiar nunca.

Los campos son variables globales, así que **la pantalla recuerda la última
combinación**: si siempre haces (P,h), sólo tecleas dos números.

La pantalla de resultados da T (en °C **y** K), P, v, u, h, s, x y la región a
la vez, más:

- **Contexto de saturación** — `Tsat = 233.85 C   sobreescalfament +116.2`,
  para ver de un vistazo cuánto te separas de la campana.
- Un **aviso naranja** (`!`) si el resultado se apoyó en la curva de saturación
  porque una isóbara vecina estaba en otra fase.

| Tecla | Qué hace |
|---|---|
| cualquiera | vuelve al formulario |
| `[View]` | menú: *Nou calcul* · *Salt estat 1 → 2* · *Ajuda* · *Sortir* |
| `[Help]` | ayuda en pantalla |
| `[Esc]` | salir |

Los **dos últimos estados calculados se guardan solos**: el anterior es el
estado 1 y el nuevo el 2. El *Salt estat 1 → 2* resta 2 menos 1 y da Δh, Δu,
Δs, Δv, ΔT y ΔP. Calcula primero el inicial y después el final — **el orden
decide el signo**.

Fuera del rango tabulado da **error visible**; nunca extrapola.

> Sólo el código de `[Enter]` (30) está confirmado; `[Help]`=3, `[Esc]`=4 y
> `[View]`=9 están deducidos del mapa de teclas. Si alguno no fuese correcto,
> esa tecla cae en el caso por defecto —volver al formulario— y no se rompe
> nada. Están al principio de `ppl/TERMO.hpprgm` (`TKHELP`, `TKESC`, `TKVIEW`):
> corregir uno es cambiar un número. `TKEY()` dice el código de la tecla que
> pulses.

**Mercurio** sólo admite pares que empiecen por T *(T,x)*, *(T,h)*, *(T,s)*…:
el PDF no le da tabla indexada por presión ni isóbaras.

---

## Pasarlo a otra calculadora

Una vez instalado, el Connectivity Kit ya tiene los binarios en

```
Documentos\HP Connectivity Kit\Calculators\<tu calculadora>\
```

Son **tres**: `TDAT.hpprgm`, `TERMOLIB.hpprgm` y la carpeta `TAULES.hpappdir`.
Ésos son los ficheros finales: se copian como cualquier otro y **se arrastran**
a otra calculadora dentro del CK. Nada de pegar, nada de nombres que teclear.

Dos detalles que lo hacen cómodo:

- Los `TDAT` guardan las matrices **ya compiladas**, no el código fuente. Quien
  los recibe no espera ninguna compilación: le abre al instante.
- La Prime también admite transferencia **directa entre calculadoras por USB
  OTG** (opción *Send* de los catálogos), sin PC de por medio.

Para que el que lo reciba compruebe que ha quedado bien, que haga dos cálculos
de [`docs/PRUEBAS_CALCULADORA.md`](docs/PRUEBAS_CALCULADORA.md) — por ejemplo
agua a `P=3`, `T=350`, que debe dar **h = 3116.06** y **s = 6.7449**.

---

## Rehacer todo desde el PDF

Pon `Tablas_propiedades_individualizadas.pdf` en la raíz y:

```bash
python tools/extract_pdf.py && python tools/validate.py && python tools/gen_ppl.py --all && python tools/gen_merged.py --all && python tests/test_engine.py && python tests/test_ppl_layout.py
```

**Si un valor está mal, se corrige el extractor o el maestro y se regenera.**
Los ficheros de datos no se editan nunca a mano.

Probar el motor sin calculadora:

```bash
python -c "import sys;sys.path.insert(0,'tools');import engine as E;print(E.fmt(E.state_PT(E.get('AIGUA'),3.0,350.0)))"
```

## Estructura

```
tools/     extract_pdf.py  pdfcommon.py  model.py  validate.py
           engine.py  gen_ppl.py  gen_merged.py  gen_pruebas.py
data/      master.json               ← única fuente de verdad (generada)
           validation_report.txt
ppl/       TERMOLIB.hpprgm           ← motor        (escrito a mano)
           TERMO.hpprgm              ← interfaz     (escrito a mano)
           APP_TAULES.hpprgm         ← ganchos app  (escrito a mano)
           TDAT_*.hpprgm  txt/       ← por sustancia (GENERADO)
           compacte/                 ← versión de 2 y 3 elementos (GENERADO)
tests/     test_engine.py  test_ppl_layout.py
docs/      ANALISIS.md  API.md  CHEATSHEET_PPL.md
           PRUEBAS_CALCULADORA.md  PLANTEAMIENTO_INICIAL.md
icon/      icon_*.png                ← icono de la app (GENERADO)
```

## Copia de seguridad

`ppl/` y `data/master.json` en el PC y en la nube. Si la calculadora se
resetea:

- con los binarios del Connectivity Kit a mano: **arrastrar los 3 ficheros**,
  menos de un minuto;
- desde cero: 3 pegados, unos 5 minutos;
- si se pierde el PC: basta el PDF y este repositorio —
  `python tools/extract_pdf.py` reconstruye `master.json` byte a byte.

## Contraste con las soluciones oficiales

Que la app sea coherente con el PDF no significa que acierte. Lo que decide es
si reproduce **lo que el profesor da por bueno**, así que
`tests/test_aceptacion.py` rehace problemas ya resueltos de principio a fin:

- **Tema 1** del cuaderno de problemas de la asignatura (depósito rígido de
  agua, metano, propano, amoníaco, etano).
- **Ciclo Rankine** con recalentamiento, regeneración y calor de proceso.
  Encadena 11 consultas a las tablas y los errores se arrastran de una a
  otra. Sale al **1,3 %**, y la potencia de la caldera al 0,003 %.
- **Ciclo frigorífico de R-134a en dos etapas** con cámara de separación.
  Sale al **0,63 %**.

Las soluciones oficiales están resueltas con **EES**, que trabaja con
propiedades de fluido real en vez de interpolar en una tabla. La desviación que sale es
por tanto el error de las tablas *más* el de la interpolación: es el techo, no
una estimación optimista.

### Dos fallos de concepto que destapó

Ninguno lo habrían cogido las otras pruebas, porque el motor era coherente
consigo mismo en los dos casos. Y ninguno daba un número equivocado: los dos
hacían que la app **fallara con un error** donde debía dar un resultado.

1. **Región supercrítica.** Por encima de la presión crítica no hay curva de
   saturación, y la determinación de región se caía. Afectaba a 30 isóbaras
   de 6 sustancias, 14 de ellas del agua (25 a 100 MPa).

2. **El corte líquido/vapor de cada isóbara.** Se detectaba por el salto de
   volumen con umbral ×5. Cerca del punto crítico `v_f` y `v_g` convergen y
   el salto no llega: **10 isóbaras se quedaban sin rama de vapor**, entre
   ellas las del agua a 17,5 y 20 MPa, que son presiones normales de ciclo
   Rankine — a esas presiones ninguna consulta de vapor sobrecalentado
   funcionaba.

   Y no es que el umbral estuviera mal puesto: **no existe ninguno que
   sirva**. En el etilè a 5,0 MPa el cambio de fase es un ×1,45 y el paso
   siguiente, que no es cambio de fase, es un ×1,68 — el salto de verdad es
   *más pequeño* que el de al lado. Ahora el corte se busca por la
   **temperatura de saturación repetida**, que en una sustancia pura es
   inequívoca, y el volumen solo se usa en las mezclas zeotrópicas, donde hay
   deslizamiento y la T no se repite.

### Una limitación que se ha dejado a propósito

La app interpola **siempre lineal**, `v` incluida: primero en T dentro de cada
isóbara, después en P entre isóbaras. Es exactamente lo que se hace a mano.

No es lo más exacto, y se sabe por qué. `v` no es lineal en P sino casi
hiperbólica (`v ≈ ZRT/P`), así que donde el PDF pega un salto grande la recta
se queda lejos del valor real:

| salto P₂/P₁ | casos | cuánto se aleja la recta |
|---|---|---|
| < 1,25 | 55 % | **0,26 %** |
| 1,25 – 1,5 | 27 % | 0,88 % |
| 1,5 – 2 | 6 % | 2,62 % |
| > 2 | 13 % | **10,07 %** |

Son **35 huecos grandes sobre 214 pares de isóbaras**, casi todos a presión
baja (`0,06→0,1`, `0,1→0,2`, `0,2→0,4`) más el del amoníaco `1,8→3,0`.

Se ha elegido reproducir el método y no corregirlo, porque **el número que da
la app tiene que ser el que se puede justificar en el papel**. De poco sirve
un resultado más exacto que no cuadra con la interpolación que uno acaba de
escribir.

El coste está acotado y hay un caso conocido donde se nota: el problema 17 del
cuaderno pide 1 mol de amoníaco a 2,5 MPa y 340 K. La tabla salta de 1,8 a
3,0 MPa; a mano —y en la app— sale **0,9952 dm³**, y la solución oficial dice
**0,9202**, un 8 % menos. Ese valor no se puede obtener interpolando
linealmente entre esas dos isóbaras. La app lo anota como limitación conocida
en vez de disimularlo, y `tests/test_engine.py` comprueba que el resultado
coincide con el cálculo a mano rehecho aparte, hasta 1e-9.

## Pendiente

- La sección «C. Propietats generalitzades» del PDF (diagramas de
  compresibilidad) no está extraída; la app no la cubre.
- En los 35 huecos grandes, `v` se aleja del valor real por interpolar lineal
  (ver arriba). Es deliberado, no un error.
- 4 erratas del PDF en la tabla del mercurio, localizadas pero no corregidas:
  se dejan como están para no separarse de la fuente.
