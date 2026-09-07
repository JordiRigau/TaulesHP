# Manual de uso

> **¿Eres estudiante y es tu primera vez?** Esta página es la referencia
> rápida. Para aprender a usarla, con ejemplos resueltos paso a paso y las
> pantallas, está [`GUIA_ESTUDIANT.pdf`](GUIA_ESTUDIANT.pdf), en catalán.

## El menú

Al abrir la app salen tres botones. Cada uno responde **al dedo y a su tecla**,
que va dibujada dentro:

```
 1.  TAULES               propietats d'una substancia
 2.  GAS REAL             un estat: Z, v i discrepancies
 3.  PROCES REAL          dos estats: dh, ds i du
```

El **1** es lo de siempre: las tablas de las 14 sustancias, y es lo que cuenta
el resto de esta página. El **2** y el **3** sustituyen la otra mitad del libro
—los diagramas generalizados— y están al final.

> La tecla siempre funciona. Que funcione el dedo depende de `MOUSE`, que no se
> puede ejecutar en el PC: sólo se puede confirmar en la calculadora. Por eso
> el número va dibujado dentro del botón y no es un adorno.

## El formulario

```
Sust   [ R-718 (Aigua)          v]
Dada 1 [ P [MPa]  v]  = [ 3        ]
Dada 2 [ T [C]    v]  = [ 350      ]
```

Los desplegables dicen **qué** dos magnitudes conoces y **con qué unidad**; los
campos numéricos, su valor. Se escribe el número tal cual, sin comillas, y el
orden no importa: (h,P) vale lo mismo que (P,h).

Los campos son variables globales, así que **la pantalla recuerda la última
combinación**: si siempre haces (P,h), sólo tecleas dos números.

### Las dos entradas de temperatura

`T [C]` y `T [K]`: eliges la escala que tengas y la calculadora convierte a la
de la tabla. Cada sustancia está tabulada en una (agua y refrigerantes en °C;
metano, etano, propano, etileno, benceno, CO₂ y mercurio en K), pero **no
necesitas saber cuál**: los resultados dan siempre las dos.

> Se hizo así porque `INPUT` construye sus etiquetas **una sola vez**: es un
> diálogo modal, así que una unidad que dependiera de la sustancia no podría
> refrescarse al cambiarla dentro del formulario. Ofreciendo las dos, la
> etiqueta no tiene que cambiar nunca.

### Pares admitidos

Cualquier combinación de dos entre **P, T, x, v, u, h, s**, salvo las que no
llevan ni P ni T —(h,s), (u,v)…—, que exigirían una búsqueda en dos
dimensiones sobre toda la rejilla y no se usan en la asignatura.

**Mercurio** sólo admite pares que empiecen por T *(T,x)*, *(T,h)*, *(T,s)*…:
el PDF no le da tabla indexada por presión ni isóbaras.

## La pantalla de resultados

Da T (en °C **y** K), P, v, u, h, s, x y la región a la vez, más:

- **Contexto de saturación** — `Tsat = 233.85 C   sobreescalfament +116.2`,
  para ver de un vistazo cuánto te separas de la campana.
- Un **aviso naranja** (`!`) si el resultado se apoyó en la curva de saturación
  porque una isóbara vecina estaba en otra fase.

Fuera del rango tabulado da **error visible**; nunca extrapola.

| Tecla | Qué hace |
|---|---|
| cualquiera | vuelve al formulario |
| `[View]` | menú: *Nou calcul* · *Ajuda* · *Sortir* |
| `[Help]` | ayuda en pantalla |
| `[Esc]` | salir |

> Los códigos son **posiciones en la rejilla del teclado, no ASCII**. Los tres
> que usa la app están confirmados: `[Help]`=3 y `[View]`=9 medidos tecla a
> tecla en una G2, `[Esc]`=4 de dos apps publicadas que coinciden y encaja en
> la rejilla ([`interface.md` del
> kit](https://github.com/JordiRigau/hp-prime-kit/blob/main/docs/reference/interface.md#5-the-keyboard)).
> Si alguno no fuese correcto, esa tecla cae en el caso por defecto —volver al
> formulario— y no se rompe nada. Están al principio de `ppl/TERMO.txt`
> (`TKHELP`, `TKESC`, `TKVIEW`): corregir uno es cambiar un número. Teclea
> `TKEY` en Home —**sin paréntesis**, que en Home dan *syntax error*— y te dice
> el código de la tecla que pulses.

## El salto entre dos estados: ya no está

Se quitó. Guardaba los dos últimos estados y restaba el segundo menos el
primero. Sobre el papel parece útil; en la práctica lo que se encadena casi
siempre es *una propiedad* del primer estado como segunda dato del segundo —la
entropía en una turbina isentrópica, por ejemplo— y esa parte la app ya la
hace. La resta final es una que se hace de cabeza, y el «cuál era el 1 y cuál
el 2» daba más problemas de los que ahorraba.

---

# Métodos generalizados (botones 2 y 3)

Para el parcial. Sustituyen el **diagrama de compresibilidad** y las **dos
cartas de funciones de discrepancia**, que son lo único que quedaba por leer a
ojo. No llevan ninguna tabla dentro: salen de la ecuación de Lee-Kesler, que es
justamente con la que se calcularon esas cartas.

## Si la sustancia está en las tablas, no hay que escribir nada

El desplegable **`Sust`**, primer campo de las dos pantallas, carga Tc, Pc, ω
y M de la sustancia elegida. Sale de `master.json`, donde ya estaban esas
constantes sin usarse.

No es un lujo: hay preguntas que **nombran la sustancia y no dan sus
constantes** —«s'expandeix isotèrmicament etilè» (30/10/2019), «5 mol d'etilè…
utilitzant mètodes generalitzats» (31/10/2024)—, y sin el desplegable había que
buscarlas fuera del aparato. Con las constantes de la tabla, las dos preguntas
siguen dando la opción oficial.

El `cp*` **no** sale de ahí: las tablas dan propiedades del fluido real, no la
capacidad calorífica de gas ideal, y el enunciado siempre la da cuando hace
falta.

Con `(manual)` valen las del formulario de constantes, que es el caso de la
mayoría de preguntas: las que dan un fluido sin nombre.

## Sólo se pide lo que de verdad falta

Primero **el problema**, y después las constantes **si hacen falta**:

```
GAS REAL - un estat                Constants del fluid   (sólo con «(manual)»)
  Sust [ Etilè              v]       Tc[K] [300]   Pc[MPa] [5]
  T [K] [197.7]  P[MPa] [6.05]       w [0.089]     M [120]
  v m3/mol [0]
```

- **Sustancia del desplegable** → Tc, Pc, ω y M salen de las tablas y no se
  pide nada más: **un solo diálogo**.
- **`(manual)`** → un segundo diálogo con las cuatro constantes.
- **`cp*` aparte**, y sólo en `PROCES REAL`, que es la única pantalla que lo
  usa. Nunca sale de las tablas: aquéllas dan el fluido real y el `cp*` es del
  gas ideal. La fila se lee como la fórmula —`cp* = [a] + T*[b]`—; si es constante,
  `b = 0`.

Enseñar un campo que luego se ignora es la peor opción: quien lo edita cree
que sirve y el resultado sale resuelto y equivocado. Por eso con una sustancia
elegida no se enseñan Tc, Pc, ω ni M — los sobrescribiría el desplegable.

Van en diálogos separados porque `INPUT` es modal y no admite más de tres
filas sin salir de lo que se sabe que funciona.

La **cabecera de la pantalla de resultados repite las constantes** —con el
nombre de la sustancia delante, si viene del desplegable—, que es lo que impide
arrastrar la Tc del problema anterior sin enterarte.

| Campo | Qué es | Unidad |
|---|---|---|
| `Tc` | temperatura crítica | **K** |
| `Pc` | presión crítica | **MPa** |
| `w` | factor acéntrico ω — 0 si el enunciado no lo da | — |
| `M` | masa molar; con `M>0` además da los valores por kg | g/mol |
| `cp* =` | el término constante, la **a** de `cp* = a + b·T` | **J/(mol·K)** |
| `+ T*` | la pendiente, la **b**; 0 si `cp*` es constante | J/(mol·K²) |

> **Si el enunciado ya te da Tr y Pr** —pasa, la 4 del 08/04/2026 es así— pon
> `Tc=1` y `Pc=1` y escribe Tr y Pr en los campos de T y P. No hay que
> convertir nada.

## Botón 2 — `GAS REAL`: un estado

Pides `T` y `P`, y da lo que se leería en las tres cartas de una vez:

```
Tr = 2.6000     Pr = 3.0000

Z0 = 1.0137   Z1 = 0.1706
Z  = 1.0305

(h-h*)/RTc:  0=-0.4217  1=0.3756
             = -0.3846
(s-s*)/R:    0=-0.1641  1=-0.0408
             = -0.1682

v = 0.0044... m3/mol
```

Los términos salen **separados en 0 y 1** a propósito: es lo que hay escrito en
el papel, así que se puede contrastar carta por carta si algo no cuadra.

> **El signo.** Aquí `h−h*` es **real menos ideal**, o sea negativo. Muchos
> apuntes tabulan `(h*−h)/RTc`, que es el mismo número al revés. La pantalla lo
> escribe entero en cada línea para que no haya duda.

### El depósito rígido

Si en vez de la presión conoces el **volumen molar**, escríbelo en `v` y la
presión pasa a ser el resultado — sale en verde. Con `v = 0` se usa la `P`.
Aquí no hay iteración: con (T, v) el estado ya está fijado.

Es la pregunta 1 del 28/10/2025, y a mano obliga a tantear presiones hasta que
el volumen cuadre.

## Botón 3 — `PROCES REAL`: el proceso 1 → 2

Es lo que pide el balance. Pides los dos estados y da:

```
dh = 3536.3 J/mol
ds = 3.8586 J/molK
du = 1835.8 J/mol
```

que es la receta del apunte hecha entera —ir al gas ideal, hacer el camino
allí, y volver—:

```
dh = ∫cp* dT                + (dh₂ − dh₁)·R·Tc
ds = ∫cp*/T dT − R·ln(P₂/P₁) + (ds₂ − ds₁)·R
du = dh − R·(Z₂T₂ − Z₁T₁)
```

Hay **un solo** campo `v`, no dos: si el recipiente es rígido el volumen molar
es el mismo en los dos estados, que es justo el caso en que lo conoces. Con
`v > 0` las dos presiones se calculan y se enseñan.

**Dos números más, y sólo cuando toca:** si `T1 == T2` añade `q = T·ds`, y si
las dos presiones coinciden añade `w = −P·dv`. No aparecen si la condición no
se cumple de verdad — decidir qué proceso es sigue siendo tuyo.

## Lo que no hace

**Fuera de donde el método vale, dice `Sense solucio`**, nunca un número. El
caso que existe de verdad es dar un `v` que caiga **dentro de la campana**: ahí
la ecuación da presión negativa y no hay estado. Por `(T, P)` no puede pasar.

## Probar el motor sin calculadora

```bash
python -c "import sys;sys.path.insert(0,'tools');import engine as E;print(E.fmt(E.state_PT(E.get('AIGUA'),3.0,350.0)))"
```

Y los generalizados:

```bash
python -c "import sys;sys.path.insert(0,'tools');import lk;print(lk.generalizado(2.6,3.0,0.099))"
```
