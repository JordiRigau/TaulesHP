# Análisis del plan y decisiones de arquitectura

Documento de referencia del proyecto. La primera sección es la importante:
**siete premisas del planteamiento inicial resultaron incorrectas o
incompletas**, y tres de ellas cambian la arquitectura entera. Todo lo demás se
deriva de ahí.

El planteamiento tal como se escribió, sin corregir, está en
[`PLANTEAMIENTO_INICIAL.md`](PLANTEAMIENTO_INICIAL.md).

---

## 1. Correcciones a las premisas de partida

### 1.1 El PDF es texto nativo, no un escaneado → **fuera Gemini**

El prompt daba por supuesto un pipeline de extracción con la API de Gemini,
schemas de *structured output*, troceado del PDF y un presupuesto de ~10 €.

Comprobado: las 80 páginas tienen **cero imágenes** y ~5.000 caracteres de
texto extraíble cada una. Además las tablas están **centradas por columna con
una desviación menor de 0,2 pt**, así que la posición horizontal de cada
número identifica su columna sin ambigüedad.

Consecuencia: la extracción es **determinista, exacta y gratuita**. Un LLM aquí
solo añadiría riesgo de alucinación sobre datos que se pueden leer con
certeza. `tools/extract_pdf.py` recupera **42.892 valores con 0 avisos**.

> Esto libera los ~10 € y, más importante, elimina la clase de error más
> peligrosa: un número plausible pero inventado.

### 1.2 No hay una sustancia, hay **catorce**

El prompt hablaba solo de agua. El PDF contiene:

| | | |
|---|---|---|
| B1 R-718 (Agua) | B6 Benceno | B11 R-507A |
| B2 Metano | B7 R-134a | B12 R-717 (Amoníaco) |
| B3 Etano | B8 R-404A | B13 R-744 (CO₂) |
| B4 Propano | B9 R-407C | B14 Mercurio |
| B5 Etileno | B10 R-410A | |

Esto multiplica por ~5 el volumen de datos y obliga a un selector de sustancia
en la app y a decidir **cuáles se cargan** (ver §4).

### 1.3 Las unidades cambian entre sustancias

Agua y refrigerantes tabulan **T en °C**; metano, etano, propano, etileno,
benceno, CO₂ y mercurio, **en K**. La app no puede asumir una unidad: cada
sustancia lleva la suya y la pantalla la muestra.

### 1.4 Sí hay datos de **líquido comprimido**

El prompt planteaba aproximar el líquido comprimido por líquido saturado a la
misma T "porque el PDF probablemente no lo trae". **Sí lo trae**: las tablas
de sobrecalentado se titulan *"Propietats de líquids subrefredats i vapors
rescalfats"* y cada isóbara arranca en la zona líquida, atraviesa el salto de
saturación y sigue en vapor.

Consecuencia: **la aproximación no hace falta**, y no hay que señalizar nada en
pantalla porque el dato es real y tabulado.

### 1.5 Cuatro sustancias tienen **once columnas**, no diez

R-404A, R-407C, R-410A y R-507A son **mezclas zeotrópicas**: tienen
deslizamiento de temperatura, así que su tabla de saturación lleva
`T P P v v u u h h s s` — presión de burbuja **y** de rocío.

Fijar 10 columnas corrompía silenciosamente esas cuatro sustancias. El
extractor ahora deduce las columnas de la cabecera. El modelo interno unifica
puras y mezclas guardando siempre los dos valores (en una pura coinciden), de
modo que **el código de la calculadora tiene un solo camino**.

### 1.6 La rejilla NO es tan dentada como se temía — el problema real es otro

El prompt anticipaba que *"cada isóbara empieza a una T distinta y puede no
tener datos a la T pedida"*. En agua es aún mejor de lo esperado: **las 44
isóbaras comparten exactamente la misma rejilla de T** (0,011 · 25 · 50 · … ·
800 °C, 35 filas) más las dos filas de saturación insertadas donde toque.

Pero aparece un problema **más sutil y más peligroso**, que sí hay que
resolver: como las isóbaras cubren todo el rango de T, a la temperatura pedida
las dos isóbaras vecinas **sí tienen datos, pero pueden estar en fases
distintas**.

> Ejemplo real: a **0,15 MPa y 115 °C** el agua es vapor sobrecalentado
> (T_sat = 111,35 °C). La isóbara vecina de arriba, 0,20 MPa, satura a
> 120,21 °C: a esos mismos 115 °C su tabla da **líquido**.
> Interpolar entre un vapor (v ≈ 1,2 m³/kg) y un líquido (v ≈ 0,001 m³/kg)
> daría un número absurdo — y con pinta de razonable.

Es decir: el riesgo no es *"falta el dato"* (que se detecta solo), sino
*"hay un dato de la fase equivocada"* (que no se detecta). Ver §3.3.

### 1.7 h_g y u_g **no son monótonas**: la inversa sobre saturación no es única

`h_g(T)` y `u_g(T)` pasan por un **máximo** bastante antes del punto crítico
(en agua, hacia 235 °C) y luego caen. Además el **benceno es un fluido
retrógrado ("seco")**: su `s_g` **crece** con T, al revés que el agua.

Consecuencias de diseño:
- Invertir h o s **sobre la curva de saturación** no tiene solución única →
  la app nunca lo hace: invierte **dentro de una isóbara** (donde h y s sí son
  monótonas con T, verificado) o despeja x directamente.
- Cualquier validación que imponga un sentido fijo a las columnas produce
  falsos positivos. Hay que deducir el sentido de los datos.

---

## 2. Estado del pipeline de datos

```
Tablas_propiedades_individualizadas.pdf
        │  tools/extract_pdf.py      (determinista, por geometría)
        ▼
   data/master.json          ← ÚNICA fuente de verdad, no se edita a mano
        │  tools/model.py           (normaliza puras/mezclas, deduplica)
        ├─► tools/validate.py  → data/validation_report.txt
        ├─► tools/engine.py    → motor de referencia en Python
        ├─► tools/gen_ppl.py    → ppl/TDAT_*.hpprgm   (uno por sustancia)
        └─► tools/gen_merged.py → ppl/compacte/       (2 o 3 elementos)
```

### Averías del PDF que hubo que resolver (todas silenciosas)

| # | Avería | Casos | Si no se corrige |
|---|--------|-------|------------------|
| 1 | Signo `−` como palabra suelta (`'‐' '50'`) | 109 en 30 págs | **71 filas con el signo cambiado**: −57,82 se leía +57,82 |
| 2 | Decimal partido (`'0'` + `',943324'`) | 28 | v = 0 en vez de 0,943324 |
| 3 | Fila del punto crítico con celdas fusionadas | 14 | se perdían v, u, h, s del punto crítico |
| 4 | Grado escrito de 3 formas (`⁰C`, `ºC`, `o`+`C`) | — | unidad de T sin identificar |
| 5 | Filas reimpresas dos veces (isóbaras NH₃ 0,5 y 0,6) | 6 | intervalos de anchura cero al interpolar |
| 6 | Título sin dos puntos (págs. 65-66) | 12 isóbaras | 12 tablas no extraídas |

La nº 1 es la que justifica todo el esfuerzo de validación: **no produce ningún
error**, solo respuestas equivocadas.

### Erratas del PDF original (no son fallos de extracción)

Las 4 están en la tabla de **mercurio**, sustancia sin isóbaras y de uso
improbable. Se dejan tal cual —el maestro es fiel al PDF— pero quedan
registradas en `data/validation_report.txt`:

| T (K) | Columna | Valor impreso | Debería rondar |
|-------|---------|---------------|----------------|
| 743,15 | v_v | 0,0054 | ≈ 0,0537 |
| 743,15 | u_v | 394,72 | ≈ 367,2 |
| 513,15 | s_v | 4,0353 | ≈ 1,0353 |
| 1003,15 | s_v | 0,8120 | ≈ 0,8196 |

### ¿Guardar las dos tablas de saturación (por T y por P)?

Son la misma curva, así que había que medir el coste de tirar una. Se
reconstruyó `T_sat(P)` interpolando linealmente la tabla por T y se comparó con
la tabla por P:

| Sustancia | Error medio | Error máximo |
|---|---|---|
| Agua | 0,113 °C | **0,303 °C** (a 0,001 MPa) |
| Benceno | 0,070 K | 0,398 K |
| Amoníaco | 0,039 °C | 0,092 °C |
| R-134a | 0,033 °C | 0,070 °C |

**Decisión: se guardan las dos.** 0,3 °C es un error visible en una solución de
examen, cuesta poco (~11 % del bloque de datos) y evita depender de interpolar
linealmente una curva exponencial. Regla operativa del motor: *si el dato es P,
se usa la tabla por P; si el dato es T, la tabla por T.*

---

## 3. La pieza central: determinación de región y enrutado

### 3.1 Tabla de pares de entrada admitidos

`ids`: 1=P 2=T 3=x 4=v 5=u 6=h 7=s

| Par | Regiones posibles | Ruta de cálculo | Notas |
|---|---|---|---|
| **(P,T)** | L / V | `T_sat(P)` de la tabla por P → compara → doble interpolación | **Ambiguo si T = T_sat**: no determina el estado, hace falta x. La app avisa y toma x = 0 |
| **(P,x)** | Bifásica | directo `y = y_f + x(y_g − y_f)` | El más barato. En mezclas informa de T de burbuja y de rocío |
| **(T,x)** | Bifásica | ídem con la tabla por T | |
| **(P,h)** | L / M / V | compara h con h_f(P), h_g(P) | **El caso estrella** del examen |
| **(P,s)** | L / M / V | ídem | Procesos isentrópicos |
| **(P,v)** | L / M / V | ídem | v_f y v_g difieren en 3 órdenes: región muy bien condicionada |
| **(P,u)** | L / M / V | ídem | |
| **(T,h)/(T,s)/(T,v)/(T,u)** | L / M / V | ídem con tabla por T; si es monofásico, busca P entre isóbaras | Menos frecuente |
| (T,P) con T=T_sat | — | mal condicionado | Ver arriba |
| (h,s), (u,v)… | — | **no soportado** | Requeriría búsqueda 2D sobre toda la rejilla; no se usa en la asignatura |

### 3.2 Lógica de decisión (idéntica en Python y en PPL)

```
dado (P, y):                       y ∈ {v,u,h,s}
    leer y_f(P), y_g(P) de la tabla de saturación por P
    si  y <  y_f   → LÍQUIDO COMPRIMIDO  → invertir dentro de la isóbara
    si  y_f ≤ y ≤ y_g → BIFÁSICO         → x = (y − y_f)/(y_g − y_f)   [directo]
    si  y >  y_g   → VAPOR SOBRECALENTADO→ invertir dentro de la isóbara

dado (P, T):
    leer T_burbuja(P), T_rocío(P)
    T < T_b → LÍQUIDO ;  T > T_r → VAPOR ;  entre medias → BIFÁSICO (falta x)
```

### 3.3 Cómo se resuelve el problema de la fase cruzada (§1.6)

Al interpolar en P entre dos isóbaras a la temperatura T:

1. Se determina **primero** la región del estado buscado.
2. Dentro de cada isóbara vecina se interpola **solo en la rama de esa fase**
   (cada isóbara está partida en rama líquida y rama vapor por el salto de v).
3. Si una vecina **no tiene esa fase** a esa T, no se interpola contra ella.
   Se sustituye por el **estado de saturación a esa misma T**, que es la
   frontera física correcta, y se marca el resultado en pantalla con
   `! veïna en altra fase: s'usa saturació`.

Nunca se mezclan fases en silencio. El caso está cubierto por el test
`test_neighbour_other_phase` (0,15 MPa / 115 °C).

### 3.4 Interpolación y búsqueda inversa

- **Lineal siempre**, `v` incluida, y en el orden en que se hace a mano:
  **primero en T** dentro de cada isóbara, **después en P** entre isóbaras.
  El objetivo es reproducir el cálculo del examen, no el valor más exacto:
  el número tiene que poder justificarse en el papel. Tiene un coste conocido
  y acotado (§6).
- **Nunca se extrapola.** Fuera del rango tabulado se lanza error visible
  (`FueraDeRango` en Python, región = −1 y pantalla roja en la Prime).
- **Inversa en bifásico**: despeje directo de x.
- **Inversa en monofásico**: se invierte por bisección **la misma función** que
  usa el cálculo directo, así ida y vuelta son coherentes. La monotonía de h y
  s con T a P constante (verificada sobre los datos) garantiza unicidad.
- **Precisión de pantalla**: las tablas traen 4-7 cifras significativas y se
  muestran T (2 dec.), P (5 signif.), v (6 signif.), u/h (2 dec.), s (4 dec.),
  x (4 dec.). No se enseñan decimales que no existen.

---

## 4. Estructura de datos y memoria

Formato en la Prime, **igual para puras y mezclas** (un solo camino de código):

```
xxST : n × 11   [T, Pl, Pv, vl, vv, ul, uv, hl, hv, sl, sv]   saturación por T
xxSP : n × 11   [P, Tl, Tv, vl, vv, ul, uv, hl, hv, sl, sv]   saturación por P
xxIX : m × 4    [P, primera_fila, n_filas, filas_rama_líquida]  índice
xxIS : N × 5    [T, v, u, h, s]                 todas las isóbaras seguidas
xxMD : {nombre, unidadT, mezcla, Tc, Pc, M, omega, vc}
```

**Por qué matrices y no listas de listas ni strings**: el acceso `M(i,j)` en
PPL es directo y no necesita recorrer; una lista de listas obliga a indexar en
dos pasos y un string exigiría parsear en tiempo de ejecución. El precio es que
la rejilla dentada no cabe en una matriz rectangular — y por eso las isóbaras
van **concatenadas en una sola matriz** con un índice `IX` aparte, en vez de
rellenar con centinelas (que desperdiciaría ~40 % en las sustancias con
isóbaras de longitud muy desigual).

El campo `filas_rama_líquida` de `IX` es el que permite interpolar en la rama
correcta sin volver a detectar el salto de fase en cada consulta.

### Tamaño

| Sustancia | Fuente PPL | | Sustancia | Fuente PPL |
|---|---|---|---|---|
| **Agua** | **64,9 KB** | | R-407C | ~21 KB |
| **Amoníaco** | **30,6 KB** | | R-404A | ~20 KB |
| **R-134a** | **16,7 KB** | | Benceno | ~20 KB |
| Etileno | ~28 KB | | R-410A | ~19 KB |
| Etano | ~27 KB | | Mercurio | ~8 KB |
| Propano / CO₂ / Metano | ~24-26 KB | | **Las 14 juntas** | **~374 KB** |

**Decisión inicial: cargar solo las que se usan** (agua + amoníaco + R-134a =
112 KB), por miedo al tiempo de compilación. **Revisada después**: compila sin
problema y se cargan las 14, porque no saber cuál pide el examen es peor que
309 KB de sobra.

Los tres campos finales de `xxMD` —M, ω y v_c— no los usa la app de tablas.
Están porque son justo lo que necesita una app de gases: `R = R_u/M`, y
`T_c`/`P_c`/`ω` dan el factor de compresibilidad generalizado. Ver
[`API.md`](API.md).

### Cuántos elementos van a la calculadora

Los datos empezaron repartidos en un fichero por sustancia (18 elementos en
total). Se fusionaron después, porque el catálogo de programas quedaba
ilegible:

| Reparto | Elementos | Cuándo |
|---|---|---|
| Uno por sustancia | 18 | si quieres cargar sólo algunas |
| `TDAT` + `TAULES` | 2 | lo más limpio |
| **`TDAT` + `TERMOLIB` + `TAULES`** | **3** | **recomendado**: el motor queda en un programa del catálogo y **otra app puede llamarlo** |

No se metió todo dentro de la app (1 elemento) porque el programa pasaría de
~25 KB a ~333 KB y editar la interfaz en la calculadora se volvería incómodo.
Separar lo que cambia (código) de lo que no cambia nunca (datos) sale mejor.

---

## 5. Diseño de la app

### App vs. Programa

Una **Application** (`.hpappdir`) da icono propio, vistas Symb/Plot/Num/Setup,
variables persistentes y ganchos `App.Start()`. Un **Program** suelto vive en
el Program Catalog.

**Elección: empezar como Programa y envolverlo como App al final.** El motor y
la UI son idénticos en ambos casos; lo que aporta la App es el arranque en
menos pulsaciones y la persistencia. Como el `.hpappdir` es un contenedor,
convertirlo después es empaquetado, no reescritura — y desarrollar como
programa permite iterar mucho más rápido en el emulador.

### La decisión de UI: cómo indicar qué dos propiedades se conocen

Se probaron tres formas, en este orden:

| | Menú `CHOOSE` de pares | Formulario con campos en blanco | **Dos desplegables + dos números** |
|---|---|---|---|
| Decisión mental previa | sí | no | no |
| Campo vacío = desconocido | — | sí, pero exige campos de **texto** | no hace falta |
| Comillas al teclear | no | **sí** (los campos de texto las piden) | no |
| Unidad a la vista | no | no | **sí, y cambia con la sustancia** |

**Elegido: dos desplegables + dos campos numéricos.** El formulario con campos
en blanco parecía mejor sobre el papel —una sola pantalla, sin decidir nada
antes— pero en la calculadora obligaba a escribir `"0.2"` con comillas, porque
"vacío" sólo se puede distinguir en un campo de texto. Los desplegables
eliminan el problema de raíz: dicen **qué** conoces, los campos numéricos
**cuánto**, y de paso muestran la unidad.

Detalles que salieron de usarlo:

- El par se **ordena solo**, así que (h,P) vale lo mismo que (P,h).
- Los cuatro campos son globales: la pantalla **recuerda la última
  combinación**. Con (P,h) fijado, un cálculo son dos números.
- La unidad de T del desplegable **cambia con la sustancia** (°C o K), así que
  no se puede equivocar sin verlo.

### La navegación no puede ir en las teclas de vista

Una app en blanco no tiene ninguna vista donde reposar, y eso fuerza la mano:

- si `START()` devuelve el control, la calculadora cae a Home y `[Num]`/`[View]`
  ya no llegan a la app;
- si `START()` no devuelve el control (bucle), se queda el teclado y esas
  teclas tampoco responden.

Las dos cosas no pueden darse a la vez. **Solución: el menú se dibuja.** La
pantalla de resultados lee las teclas ella misma —cualquiera vuelve al
formulario, `[View]` abre el menú, `[Help]` la ayuda, `[Esc]` sale— y siempre
se ve en el pie qué se puede hacer.

Sólo el código de `[Enter]` (30) está confirmado; los otros tres están
deducidos. El diseño falla de forma segura: una tecla con código equivocado cae
en el caso por defecto, que es volver al formulario.

### Estados guardados

Los **dos últimos estados calculados se guardan solos** en `TS1`/`TS2`: el
anterior es el estado 1 y el nuevo el 2. El *Salt estat 1 → 2* del menú da Δh,
Δu, Δs, Δv, ΔT y ΔP de golpe, que es lo que pide cualquier balance.

Antes había que pulsar `1` o `2` para guardarlos, pero eso dependía del código
de tecla que devuelve `WAIT(-1)`, que **no es el ASCII** sino un identificador
de posición. Guardarlos solos ahorra pulsaciones y elimina el problema.

---

## 6. Estrategia de pruebas

Separada en datos y app, como pedía el prompt.

### Datos — `tools/validate.py` → `data/validation_report.txt`

Comprueba criterios **independientes del extractor** (no "hizo lo que dice",
sino "los números cumplen física conocida"):

- estructura: columnas coherentes, unidad de T única por sustancia, sin huecos;
- fase: v_g > v_f, u_g > u_f, h_g > h_f, s_g > s_f (salvo punto crítico);
- monotonías con el **sentido deducido de los datos** (§1.7);
- **continuidad isóbara ↔ saturación**: las dos filas de saturación de cada
  isóbara deben coincidir con la tabla de saturación a esa P;
- **redundancia** entre las dos tablas de saturación (§2);
- detección de erratas por rotura aislada de monotonía y por picos de un punto.

Resultado actual: **0 incidencias estructurales o físicas**; 4 erratas del PDF
original, todas en mercurio.

### App — `tests/test_engine.py` (549 comprobaciones, todas en verde)

La trampa que advertía el prompt (implementar el mismo algoritmo dos veces solo
detecta errores de transcripción) se evita usando **tres fuentes ajenas al
algoritmo**:

| Fuente | Qué cubre |
|---|---|
| **A. Nodos exactamente tabulados** | interpolar sobre un nodo debe devolver el nodo. Cubre x=0, x=1, punto tabulado, líquido comprimido, y la inversa (de (P,h) tabulado hay que recuperar su T) |
| **B. Tablas de vapor publicadas** (Çengel/NIST) | detecta un fallo coherente consigo mismo pero equivocado. Ej.: agua a 3 MPa/350 °C da h = 3116,06 frente a 3116,1 publicado |
| **C. Casos límite exigidos** | fuera de rango (debe fallar visiblemente), x fuera de [0,1], vecina en otra fase, enrutado de región |

### Capa PPL — `tests/test_ppl_layout.py` (1008 comprobaciones, todas en verde)

Que un programa compile en la Prime no dice nada de si los índices están bien.
Lo que más se rompe al portar a PPL es la **aritmética de índices** (matrices
1-based, isóbaras concatenadas, ramas partidas por un contador).

Este arnés **lee los `.hpprgm` generados**, replica el acceso *exactamente*
como lo hace `TERMO.hpprgm` y lo compara con el motor. Un desfase de una fila
aparece aquí, en el PC, y no en el examen. Verifica además que ningún valor
pierde precisión al serializarse (peor desviación relativa < 1e-15).

### Aceptación — `tests/test_aceptacion.py` (42 comprobaciones, en verde)

La única prueba que puede decir si la app **sirve**. Las otras dos verifican
coherencia interna; esta compara contra lo que el profesor da por bueno.

| Fuente | Qué se rehace | Desviación máx. |
|---|---|---|
| *«Termodinàmica. Tests i problemes»* (ETSEIB-UPC, 2025), Tema 1 | depósito rígido de agua, metano, propano, amoníaco, etano | 0,42 % |
| Ciclo resuelto, con solución oficial | ciclo Rankine con recalentamiento, regeneración y calor de proceso | 1,31 % |
| Ciclo resuelto, con solución oficial | ciclo frigorífico de R-134a en dos etapas con cámara de separación | 0,63 % |

Los dos ciclos son la prueba dura: encadenan 11 y 13 consultas a las tablas, y
el error de cada una se arrastra a la siguiente. El Rankine además pasa por
líquido comprimido a 17,5 MPa, dos expansiones isentrópicas, tres líquidos
saturados y un título por entalpía; el frigorífico añade una inversa `P(T,h)`
y un rendimiento isentrópico, que es una diferencia de dos entalpías parecidas
y por tanto amplifica el error relativo.

Las soluciones oficiales están resueltas con **EES**, que trabaja con
propiedades de fluido real en lugar de interpolar en una tabla. La desviación medida es
entonces el error de las tablas *más* el de la interpolación: es una cota
superior, no una estimación benévola. Que un ciclo entero salga al 1,3 % con
una tabla de papel de por medio es el resultado, no el margen de error.

**Encontró dos fallos de concepto** que los otros 1557 tests no podían ver,
porque el motor era coherente consigo mismo en los dos casos — justo lo que
advertía el planteamiento inicial sobre implementar el mismo algoritmo dos
veces. Los dos hacían que la app **fallara con un error** donde debía dar un
número; ninguno devolvía un resultado equivocado. Y sacó a la luz una tercera
cuestión, que no es un fallo sino una decisión de diseño.

#### 1. No se contemplaba la región supercrítica

Por encima de P_c no hay curva de saturación, así que comparar contra T_sat no
tiene sentido y el motor se caía con *«fuera del rango tabulado»*. Afectaba a
**30 isóbaras de 6 sustancias**, 14 de ellas del agua (25 a 100 MPa):
presiones de ciclo Rankine supercrítico, nada exótico. Ahora hay una región
propia y las isóbaras se leen sin exigir fase.

Con P < P_c y T > T_c el estado es vapor sobrecalentado corriente, no
supercrítico: la región la decide **la presión**. Confundirlo rompió un test de
enrutado y sirvió para acotarlo bien.

#### 2. El corte líquido/vapor se buscaba por el salto de volumen

Cada isóbara del PDF trae, seguidas, las filas de líquido subenfriado, las dos
de saturación y las de vapor. Hay que saber dónde corta. Se detectaba por el
salto de `v` con umbral ×5, y cerca del punto crítico eso no funciona: `v_f` y
`v_g` convergen y el salto se queda corto. **10 isóbaras se quedaban sin rama
de vapor**, entre ellas las del agua a 17,5 y 20 MPa — presiones normales de
ciclo Rankine, que es exactamente donde se cayó.

Y no es que el umbral estuviera mal elegido: **no existe ninguno que sirva**.
El contraejemplo está en el etilè a 5,0 MPa, justo por debajo de su presión
crítica (5,0418 MPa):

| T | `v` | |
|---|---|---|
| 281,98 °C | 0,00394 | líquido saturado |
| 281,98 °C | 0,00571 | vapor saturado — **el cambio de fase, ×1,45** |
| 290,0 °C | 0,00957 | ×1,68, y aquí no pasa nada |

El salto de verdad es *más pequeño* que el que viene justo después. Ni un
umbral ni «coger el salto mayor» aciertan.

El criterio bueno es otro: en una sustancia pura las dos filas de saturación
**comparten temperatura**, y eso es inequívoco. El volumen queda solo para las
**mezclas zeotrópicas**, donde hay deslizamiento y la T no se repite (en R-404A
a 0,14 MPa la burbuja está a −39,24 °C y el rocío a −38,53 °C). Ahí sí hay
margen de sobra, porque las mezclas del PDF no llegan tan cerca del crítico:
el salto real más pequeño es ×4,43 y el mayor falso positivo ×1,20, con el
umbral puesto en ×2,0.

Falta un tercer caso: por encima de P_c no hay salto ninguno, pero el agua a
25 MPa cruza la región pseudocrítica con `v` ×3,03 entre 375 y 400 °C, que el
criterio del volumen tomaba por una vaporización. Las isóbaras supercríticas se
marcan al cargar y se devuelven como una sola rama continua.

#### 3. La limitación que se ha dejado a propósito

Este no es un fallo, sino una decisión, y conviene dejarla escrita porque la
prueba de aceptación la señala.

`v` se interpola **linealmente en P**, como se hace a mano. No es lo más
exacto: en un gas *v ≈ ZRT/P* es casi una hipérbola, y entre isóbaras
separadas la recta se aleja. Medido con el espaciado real de las tablas —no
quitando isóbaras, que duplicaría el hueco— la diferencia entre interpolar en
P y en 1/P es:

| salto P₂/P₁ | casos | media | p95 | máximo |
|---|---|---|---|---|
| < 1,25 | 4227 (55 %) | **0,26 %** | 0,85 % | 2,36 % |
| 1,25 – 1,5 | 2076 | 0,88 % | 3,00 % | 5,31 % |
| 1,5 – 2 | 468 | 2,62 % | 6,77 % | 8,43 % |
| > 2 | 972 (13 %) | **10,07 %** | 60,05 % | 85,30 % |

Son **35 huecos grandes sobre 214 pares de isóbaras**, casi todos a presión
baja (`0,06→0,1`, `0,1→0,2`, `0,2→0,4`) más el del amoníaco `1,8→3,0`.

**Por qué se deja así.** El criterio del proyecto siempre fue reproducir el
método del examen, y ahí es donde se usa la app. Un resultado más exacto que
no cuadra con la interpolación que el alumno acaba de escribir en el papel
vale menos que uno reproducible: no se puede defender, y obliga a explicar por
qué la calculadora dice otra cosa que la cuenta de al lado.

**El caso donde se nota.** El problema 17 pide 1 mol de amoníaco a 2,5 MPa y
340 K. La tabla del amoníaco salta de 1,8 a 3,0 MPa, y a 66,85 °C da 1,3742 y
0,7244 dm³/mol. La recta evaluada en 2,5 MPa vale **0,9952**, que es lo que
sale a mano y lo que da la app. La solución oficial es **0,9202** —un 8 %
menos— y no se obtiene interpolando linealmente; en 1/P saldría 0,9193.

Se probó con 1/P y se descartó: de las 42 comprobaciones de aceptación, la
interpolación lineal falla **solo esa una**. Los dos ciclos completos salen
idénticos con los dos métodos, porque sus consultas caen en zonas donde las
isóbaras están juntas. O sea, el cambio no arreglaba nada de lo que se usa a
diario y a cambio separaba la app del lápiz.

La prueba `test_reproduce_la_interpolacion_a_mano` rehace la interpolación
aparte del motor y exige coincidencia a 1e-9, para que nadie vuelva a meter
1/P sin darse cuenta. `test_coste_de_interpolar_v_lineal` deja anotado el
coste, y avisaría si el PDF cambiara y los huecos crecieran.

### Un caso donde ni la app ni el método coinciden con el oficial

En el problema 1.2 —agua a 5 bar con v = 1/970— sale 82,25 °C frente a los
81,9 oficiales. No es un fallo: en esa zona el PDF da `v` con seis decimales y
dv/dT ≈ 6,8·10⁻⁷, así que **medio dígito de redondeo vale 0,7 °C**. La masa que
daría exactamente 81,9 °C es 970,2 kg. Los dos valores son el mismo punto para
lo que estas tablas pueden resolver.

---

## 7. Riesgos y cuellos de botella

| Riesgo | Estado | Mitigación |
|---|---|---|
| PPL sin probar en hardware | **resuelto** | Probado en una G2 real (firmware 2.4.15515): compila, calcula y la batería de casos sale correcta |
| Tiempo de compilación del bloque de datos | acotado | 112 KB por defecto; se puede recortar a solo agua (65 KB) |
| Fase cruzada al interpolar en P | **resuelto** | §3.3, con aviso en pantalla y test dedicado |
| No linealidad de P_sat(T) | **resuelto** | Se guardan las dos tablas; error medido, no supuesto (§2) |
| Erratas del PDF | **acotado** | 4 localizadas, todas en mercurio; validador las detecta si aparecen más |
| Extracción poco fiable | **resuelto** | Determinista y verificada; 6 clases de avería del PDF corregidas |
| Mezclas zeotrópicas mal modeladas | **resuelto** | 11 columnas, burbuja/rocío, unificadas con las puras |
| Pérdida de la app (reset) | **resuelto** | Copia de `ppl/` y `master.json` en PC y nube. Restaurar: arrastrar los 3 binarios del Connectivity Kit (<1 min) o 3 pegados desde cero (~5 min) |
