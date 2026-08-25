# Manual de uso

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
| `[View]` | menú: *Nou calcul* · *Salt estat 1 → 2* · *Ajuda* · *Sortir* |
| `[Help]` | ayuda en pantalla |
| `[Esc]` | salir |

> Sólo el código de `[Enter]` (30) está confirmado; `[Help]`=3, `[Esc]`=4 y
> `[View]`=9 están deducidos del mapa de teclas. Si alguno no fuese correcto,
> esa tecla cae en el caso por defecto —volver al formulario— y no se rompe
> nada. Están al principio de `ppl/TERMO.hpprgm` (`TKHELP`, `TKESC`, `TKVIEW`):
> corregir uno es cambiar un número. `TKEY()` dice el código de la tecla que
> pulses.

## El salto entre dos estados

Los **dos últimos estados calculados se guardan solos**: el anterior es el
estado 1 y el nuevo el 2. El *Salt estat 1 → 2* del menú resta 2 menos 1 y da
Δh, Δu, Δs, Δv, ΔT y ΔP, que es lo que pide cualquier balance.

Calcula primero el inicial y después el final — **el orden decide el signo**.

## Probar el motor sin calculadora

```bash
python -c "import sys;sys.path.insert(0,'tools');import engine as E;print(E.fmt(E.state_PT(E.get('AIGUA'),3.0,350.0)))"
```
