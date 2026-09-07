# Usar el motor desde otra app

Sí, el motor es reutilizable — **pero sólo con la variante de 3 elementos**.

## Qué montaje necesitas

| Variante | Elementos | ¿Otra app puede usar el motor? |
|---|---|---|
| 1 elemento | `TAULES` (datos y motor dentro) | ❌ no |
| 2 elementos | `TDAT` + `TAULES` (motor dentro de la app) | ⚠️ no de forma fiable |
| **3 elementos** | `TDAT` + **`TERMOLIB`** + `TAULES` | ✅ sí |

La de 1 elemento es la que se reparte a los estudiantes: se arrastra un solo
fichero, y a cambio todo lo que exporta queda dentro de la app. Si estás
escribiendo otra app, no es la tuya.

Lo que se exporta desde un **programa del catálogo** es global sin discusión y
cualquier programa o app puede llamarlo. Lo que se exporta desde el programa de
una **app** queda ligado a esa app. Por eso, si vas a hacer una segunda app,
usa la variante de 3: el motor se queda en su propio programa.

```bash
python tools/gen_merged.py --all
python tools/build_hp.py
```

y arrastra `ppl/build/dev/TDAT.hpprgm`, `ppl/build/dev/TERMOLIB.hpprgm` y tu app.

> Hay una regla de orden: un programa sólo ve las funciones de otro **si se
> compiló después**. Instala siempre `TDAT` → `TERMOLIB` → tu app.

---

## Antes de nada: cargar la sustancia

Todo el motor trabaja sobre la sustancia activa. Se carga una vez:

```ppl
TLOAD(1);        // 1..SIZE(TSUBS); el orden es el de TNAMS
```

Después quedan disponibles `TMD` (metadatos), `TST`, `TSP`, `TIX`, `TIS`.

## Estado completo a partir de dos magnitudes

Todas devuelven una **lista de 9**:

```
{T, P, v, u, h, s, x, regio, avis}
```

- `regio`: 0 = líquido comprimido · 1 = bifásico · 2 = vapor sobrecalentado ·
  **−1 = error** (y entonces `avis` lleva el motivo).
- `x` vale −1 cuando el estado no está en la campana.
- **Comprueba siempre `st(8) >= 0` antes de usar los números.**

| Función | Qué recibe |
|---|---|
| `TPT(P, T)` | presión y temperatura |
| `TPX(P, x)` | presión y título |
| `TTX(T, x)` | temperatura y título |
| `TPY(P, pr, y)` | presión y una propiedad |
| `TTY(T, pr, y)` | temperatura y una propiedad |

`pr` selecciona la propiedad: **1 = v · 2 = u · 3 = h · 4 = s**

```ppl
LOCAL zst;
TLOAD(1);                       // aigua
zst := TPY(3, 3, 3116.06);      // (P=3 MPa, h=3116.06) -> T=350 C
IF zst(8) >= 0 THEN
  // zst(1)=T  zst(2)=P  zst(3)=v  zst(4)=u  zst(5)=h  zst(6)=s  zst(7)=x
END;
```

## Unidades de temperatura

El motor trabaja **en la unidad en que está tabulada cada sustancia** — °C en
agua y refrigerantes, K en metano, etano, propano, etileno, benceno, CO₂ y
mercurio. `TMD(2)` lo dice: 0 = °C, 1 = K.

Si tu app recoge la temperatura del usuario, convierte antes de llamar:

```ppl
TIDX(zd)        // indice del desplegable de TPROP -> id de magnitud (1..7)
TCONV(zd, zv)   // valor del desplegable -> unidad de la tabla
TTOK(zt)        // T de la tabla -> Kelvin, para mostrarla siempre en las dos
```

`TPROP` es la lista fija de los desplegables, con **dos entradas de
temperatura**: `1 P · 2 T[C] · 3 T[K] · 4 x · 5 v · 6 u · 7 h · 8 s`.

## Sólo la curva de saturación

Devuelven una **lista de 10**, o `{}` si la entrada cae fuera de rango:

```ppl
TSATT(T)   // -> {Pl, Pv, vl, vv, ul, uv, hl, hv, sl, sv}
TSATP(P)   // -> {Tl, Tv, vl, vv, ul, uv, hl, hv, sl, sv}
```

En sustancias puras los dos primeros valores coinciden; en las mezclas
zeotrópicas (R-404A, R-407C, R-410A, R-507A) son burbuja y rocío.

## Una sola fase, sin determinar región

```ppl
TSPH(P, T, ph)   // ph: 0 = liquid, 1 = vapor  ->  {v, u, h, s} o {}
```

## Constantes para cálculos de gases

`TMD` lleva los datos que la app de tablas no usa pero una de gases sí:

| Índice | Contenido |
|---|---|
| `TMD(1)` | nombre |
| `TMD(2)` | unidad de T: 0 = °C, 1 = K |
| `TMD(3)` | 1 si es mezcla zeotrópica |
| `TMD(4)` | **T_c [K]** |
| `TMD(5)` | **P_c [MPa]** |
| `TMD(6)` | **M [g/mol]** |
| `TMD(7)` | **ω** (factor acéntrico) |
| `TMD(8)` | **v_c [m³/kg]** |

```ppl
TLOAD(1);
R := 8.314462 / TMD(6);          // kJ/(kg K)   agua -> 0.4615
Tr := (T + 273.15) / TMD(4);     // temperatura reducida
Pr := P / TMD(5);                // presión reducida
```

Con `Tr`, `Pr` y `ω` tienes lo necesario para compresibilidad generalizada;
sólo faltarían las tablas de Z y de las funciones de discrepancia, que **no
están en este PDF** (ver más abajo).

En mercurio, `TMD(7)` vale 0: el PDF no da su factor acéntrico.

## Lo que NO hay en estas tablas

El PDF es de **propiedades individualizadas**: fluidos reales tabulados. No
trae nada de esto, y habría que sacarlo de otra fuente:

- tablas de gas ideal tipo A-17 (h, u, s° frente a T para aire, N₂, O₂…)
- c_p, c_v ni k de gases
- diagrama de compresibilidad Z (sólo tienes T_c, P_c y ω para construirlo)

La sección *«C. PROPIETATS GENERALITZADES»* aparece citada en la página 79 del
PDF, pero **su contenido no está** en el fichero que tenemos: termina en el
mercurio.

Para la fase gaseosa de las 14 sustancias tabuladas sí tienes todo: las
isóbaras cubren el vapor sobrecalentado, que es gas real con sus valores
medidos, mejor que cualquier aproximación de gas ideal.

## Errores

No hay excepciones en PPL. El convenio del motor:

- las funciones de estado devuelven `regio = -1` y el motivo en `avis`
- `TSATT` / `TSATP` / `TSPH` devuelven `{}`
- el último mensaje queda en la global **`TERR`**
- **nunca se extrapola**: fuera del rango tabulado da error, no un número

```ppl
IF zst(8) < 0 THEN
  MSGBOX(zst(9));
END;
```

## Probarlo sin calculadora

El motor se puede ejecutar en el PC tal cual, sobre los mismos ficheros que
vas a instalar, con el intérprete de
[hp-prime-kit](https://github.com/JordiRigau/hp-prime-kit):

```bash
python ~/.claude/skills/hp-prime/hpprime.py run ppl/compacte/TDAT.txt ppl/compacte/TERMOLIB.txt --call "TLOAD(1)" --call "TPY(3,3,3116.06)"
```

No es una reimplementación: es el fichero de verdad. Lo que no cubre lo
levanta como error en vez de inventarse un número, así que si una llamada pasa
es que se ha ejecutado. `INPUT`, `MSGBOX` y el dibujo quedan anotados en vez de
pintarse, de modo que un programa con interfaz también corre entero.

Añade tu propio fichero a la lista y desarrollas la app entera desde el PC:

```bash
python ~/.claude/skills/hp-prime/hpprime.py run ppl/compacte/TDAT.txt ppl/compacte/TERMOLIB.txt MIAPP.txt --call "MIFUNC(1)"
```
