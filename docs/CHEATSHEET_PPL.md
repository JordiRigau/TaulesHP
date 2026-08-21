# Cheat sheet de HP PPL para este proyecto

Solo lo que se usa en `ppl/TERMOLIB.hpprgm` (motor) y `ppl/TERMO.hpprgm` (interfaz). La referencia
oficial mezcla comandos matemáticos con sintaxis de programación y explica mal
los casos límite, así que esto está ordenado por lo que hace falta aquí.

> **Verifica en el emulador antes de fiarte.** La forma rápida de aprender PPL
> no es leer el manual entero, sino pegar fragmentos de 5 líneas en el editor
> del Virtual Calculator y usar los errores del compilador como respuesta. El
> compilador señala la línea y suele bastar.

## Fuentes recomendadas

| Fuente | Para qué sirve |
|---|---|
| *HP Prime Programming Reference* (HP) | referencia puntual de comandos, no para aprender |
| **hpmuseum.org/forum** (subforo HP Prime) | la mejor: código completo y comentado, y explicación de comportamientos reales |
| **en.hpprime.club** (E. Shore / H. Klaver) | tutoriales con ejemplos que funcionan |
| **Eddie's Math and Calculator Blog** | programas cortos comentados |
| **hpcalc.org** | archivo de programas; buscar ahí antes de escribir nada |

Antes de ampliar esto, busca en hpcalc.org y en el foro si ya existe una app de
tablas de vapor para Prime: ver cómo otro resolvió el almacenamiento de tablas
irregulares vale más que cualquier tutorial genérico.

---

## Estructura de un fichero

```ppl
// comentario de línea

EXPORT VAR1, VAR2;              // variables globales, persisten entre usos
EXPORT MIDATO:=[[1,2],[3,4]];   // global con valor inicial

EXPORT FUNC(a, b)
BEGIN
  LOCAL x, y;                   // TODOS los locales, al principio del BEGIN
  x := a + b;
  RETURN x;
END;
```

- `EXPORT` hace visible la función/variable desde otros programas y desde Home.
- Sin `EXPORT` es privada del fichero.
- El `;` final de `END;` es obligatorio.

## Asignación y tipos

```ppl
x := 5;              // asignación (también vale  5 ▶ x)
L := {1, 2, 3};      // lista        → L(1) es 1   (1-BASED)
M := [[1,2],[3,4]];  // matriz       → M(2,1) es 3 (fila, columna)
s := "texto";        // cadena
```

**Todo es 1-based.** El error más común al portar desde Python.

| Necesidad | PPL |
|---|---|
| tamaño de lista o cadena | `SIZE(L)` |
| dimensiones de matriz | `d := DIM(M);` y luego `d(1)`, `d(2)`. **Nunca `DIM(M)(1)`** |
| añadir al final de lista | `L(SIZE(L)+1) := v;` |
| concatenar cadenas | `"a" + "b"` |
| número → cadena | `STRING(x)` |
| cadena → número | `EXPR("2000/3")` — evalúa expresiones enteras |
| tipo de una variable | `TYPE(v)` (0 real, 2 cadena, 6 lista, 3 matriz…) |

## Control de flujo

```ppl
IF cond THEN ... ELSE ... END;          // END, no ENDIF
FOR i FROM 1 TO n DO ... END;
FOR i FROM n DOWNTO 1 DO ... END;
WHILE cond DO ... END;
REPEAT ... UNTIL cond;                  // se ejecuta al menos una vez
BREAK;  CONTINUE;
CASE
  IF c1 THEN ... END;
  IF c2 THEN ... END;
  DEFAULT ...
END;
IFTE(cond, siVerdad, siFalso)           // versión expresión
```

- Comparación de igualdad: `==`. Asignación: `:=`. Distinto: `<>`.
- Lógicos: `AND`, `OR`, `NOT`.
- **No hay excepciones.** Aquí se devuelve una región `-1` y un mensaje en la
  variable global `TERR`.

## Números útiles

```ppl
IP(x)      // parte entera        FLOOR(x)  CEILING(x)
ROUND(x,n) // n decimales         ABS(x)  MIN(a,b)  MAX(a,b)
LOG(x)     // logaritmo decimal   1E-9  notación científica válida en fuente
```

## Entrada y salida

```ppl
// Formulario: devuelve 1 si Aceptar, 0 si Cancelar.
// Las variables han de existir y tener ya el tipo correcto.
INPUT({v1, v2}, "Título", {"Etiq1:", "Etiq2:"}, {"ayuda1", "ayuda2"});

CHOOSE(var, "Título", "op1", "op2", "op3");   // menú; var recibe el índice
MSGBOX("mensaje");
PRINT("al terminal");
```

Dibujo en pantalla (320×240), que es lo que usa `TSHOW`:

```ppl
RECT();                                  // borra la pantalla
TEXTOUT_P("texto", x, y, fuente, color); // fuente 1..7; color con RGB(r,g,b)
WAIT(-1);                                // espera tecla y devuelve su código
```

`WAIT(-1)` devuelve el código de la tecla: `49` es `1`, `50` es `2` (ASCII).

## Errores de sintaxis reales (y los que resultaron ser falsos)

Firmware de referencia: **2.4.15515 (2025-09-15)**, G2. Sus notas de versión
sólo mencionan aritmética exacta con fracciones y multiplicación implícita:
**ningún cambio en la sintaxis de PPL**.

### Confirmado — la causa real de los fallos de este proyecto

| Lo que no compila | Por qué | Forma correcta |
|---|---|---|
| **`LOCAL` con demasiadas variables** | límite de **7–8 por sentencia** según firmware. Da *syntax error* al comprobar el programa, **señalando la línea del `LOCAL`** | varias sentencias `LOCAL` seguidas (aquí se usan grupos de 6) |
| `n := SIZE(M)(1);` | no se puede indexar el resultado de una llamada | `d := DIM(M);`<br>`n := d(1);` |
| `EXPORT A:=1, B:=2, …;` | falló con 7 variables inicializadas en una línea | una declaración por línea |

Evidencia del límite de `LOCAL`, medida sobre programas que funcionan en esta
misma calculadora: `TRAFOS` declara **8** y compila; `Cargas Trifásicas`,
`FPefectivo` y `Etec_4_LINIES` se quedan en **7**. Las funciones que fallaban
aquí declaraban **13, 16 y 18**.

### Descartado — hipótesis que resultaron FALSAS

No las repitas: cada una costó una ronda de compilación.

| Hipótesis | Por qué es falsa |
|---|---|
| «`RETURN` dentro de un `FOR`/`REPEAT` no vale» | `INTERP.hpprgm`, que funciona, tiene **2** |
| «letra + dígito está reservado (`r2`, `y1`)» | `Etec_4_LINIES` usa `L12, L13, L14, L15…` como locales |
| «`LOCAL m` choca con las matrices `M0..M9`» | correlación casual: lo que fallaba era el número de locales |
| «varios locales con valor inicial en una línea» | el tutorial de E. Shore usa `local x1:=160, x2:=299, x3:=21` |

### Precaución razonable, sin confirmar

- `i` (unidad imaginaria) y `e` (número de Euler) como nombres de local: aquí
  se renombraron antes de tener evidencia, así que no se llegó a comprobar.
  Prefijar los locales (`zm`, `zres`…) sale gratis y evita la duda.

### Cómo se encontró: medir, no teorizar

Costó **cinco rondas** porque el compilador señala la línea del `LOCAL` sin
decir qué sobra, y como el error no se movía cada hipótesis parecía plausible.
Lo que lo resolvió fue dejar de razonar sobre la sintaxis y **medir los
programas que ya funcionaban en esa misma calculadora**, tabulando sus rasgos
(máximo de locales por sentencia, `RETURN` en bucles, longitud de línea).
La comparación señaló el número de locales de inmediato.

**Lección de método**: ante un error que no se mueve tras un arreglo, busca
código que ya funcione en el mismo entorno y compara métricas. Y contrasta la
sintaxis con documentación real en vez de fiarte de la memoria.

Fuentes: [More undocumented programming limitations in the HP Prime](https://www.hpmuseum.org/cgi-bin/archv021.cgi?read=254706) ·
[HP Prime Programming Tutorial (E. Shore)](https://literature.hpcalc.org/community/hpprime-prog-tutorial.pdf) ·
[Firmware G2 2.4.15515](https://www.hpcalc.org/details/7783)

## Trampas encontradas en este proyecto

| Trampa | Detalle |
|---|---|
| **1-based** | matrices y listas empiezan en 1; `IX` guarda ya índices 1-based |
| **`LOCAL` al principio** | declarar un local a media función es error de compilación |
| **`END`, nunca `ENDIF`/`ENDFOR`** | |
| **`==` vs `:=`** | `IF x = 1` no es lo que parece |
| **Matrices por valor** | pasar una matriz grande a una función la **copia**. Por eso el motor accede a los globales `TST/TSP/TIX/TIS` en vez de recibirlos como argumento |
| **`EXPR("")` falla** | comprueba siempre `SIZE(s) > 0` antes de evaluar un campo |
| **Nombres de variable** | los globales exportados comparten espacio con Home: usa prefijos (`T…`) para no chocar |
| **Decimal en el fuente** | el código fuente usa siempre `.`, aunque la calculadora muestre `,` |
| **Acceso dinámico** | `EXPR("AIGUAST")` devuelve la matriz cuyo nombre se construye al vuelo; se hace **una vez** al cargar sustancia, nunca por elemento |

## Patrón de búsqueda binaria usado en el motor

```ppl
EXPORT TBRK(M, c, x, r0, n)   // tramo [i,i+1] de la columna c que contiene x
BEGIN
  LOCAL lo, hi, mid;
  IF n < 2 THEN RETURN 0; END;
  IF x < M(r0, c) - 1E-9 THEN RETURN 0; END;          // fuera de rango:
  IF x > M(r0 + n - 1, c) + 1E-9 THEN RETURN 0; END;  // devuelve 0, no extrapola
  lo := r0; hi := r0 + n - 1;
  WHILE hi - lo > 1 DO
    mid := IP((lo + hi) / 2);
    IF M(mid, c) <= x THEN lo := mid; ELSE hi := mid; END;
  END;
  RETURN lo;
END;
```

Devolver `0` en vez de saturar al extremo es deliberado: **un número plausible
pero inventado en un examen es peor que un error claro.**
