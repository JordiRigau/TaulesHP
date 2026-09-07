# Batería de pruebas en la calculadora

Generado por `tools/gen_pruebas.py` desde el motor de referencia.
**No editar a mano**: si cambian el motor o los datos, se regenera.

Que compile no significa que calcule bien. Estos casos cubren **todas las rutas del motor**: cada región, la interpolación doble, la búsqueda inversa, la regla de la palanca, el caso de fase cruzada y el fallo fuera de rango.

> **Antes de empezar**: ten la app instalada y comprueba que la sustancia del caso aparece en el desplegable. El montaje está en el README.

En cada caso: teclea `TERMO` en Home, elige la sustancia, pon las dos magnitudes en los desplegables `Dada 1` / `Dada 2` y teclea sus valores. Los campos de valor son numéricos: el número se escribe directamente, sin comillas. El orden de las dos no importa.

> **Sin paréntesis.** En Home una función sin argumentos se llama por su nombre: `TERMO()` responde *syntax error*, `TERMO` la ejecuta. Dentro del fuente PPL los paréntesis sí son correctos. Medido en una G2 con el firmware 2.4.15515.

> **Compara el valor, no el relleno.** Esta tabla la formatea Python (`%.2f`); la app imprime `STRING(ROUND(x, n))`, que es otro camino. Los ceros de la derecha pueden no salir: donde aquí pone `500.00`, en pantalla puede salir `500`. Y en un empate exacto el último dígito puede caer al otro lado — aquí pasa en el caso 6 (`h`, `s`). Cuál de los dos imprime la calculadora **no está medido**: si baila la última cifra, no es la instalación.

## Casos

| # | Sust | Entrada | T | P | v | u | h | s | x | Región |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3 R-134a | `P=0.2 · x=1` | -10.08 C | 0.2 | 0.09988 | 372.64 | 392.62 | 1.7330 | 1.0000 | VAPOR SATURAT |
| 2 | 3 R-134a | `P=0.2 · x=0` | -10.08 C | 0.2 | 0.000753 | 186.45 | 186.60 | 0.9500 | 0.0000 | LIQUID SATURAT |
| 3 | 3 R-134a | `P=0.14 · T=20` | 20.00 C | 0.14 | 0.16544 | 396.37 | 419.53 | 1.8580 | -- | VAPOR SOBREESCALFAT |
| 4 | 1 R-718 (Aigua) | `P=3 · T=350` | 350.00 C | 3 | 0.090556 | 2844.39 | 3116.06 | 6.7449 | -- | VAPOR SOBREESCALFAT |
| 5 | 1 R-718 (Aigua) | `P=0.075 · s=6.7449` | 91.76 C | 0.075 | 1.96466 | 2255.66 | 2403.01 | 6.7449 | 0.8861 | BIFASIC |
| 6 | 1 R-718 (Aigua) | `P=1.3 · T=375` | 375.00 C | 1.3 | 0.226911 | 2912.74 | 3205.93 | 7.2605 | -- | VAPOR SOBREESCALFAT |
| 7 | 1 R-718 (Aigua) | `P=1 · h=500` | 118.95 C | 1 | 0.00105892 | 498.94 | 500.00 | 1.5144 | -- | LIQUID COMPRIMIT |
| 8 | 1 R-718 (Aigua) | `P=0.15 · T=115` | 115.00 C | 0.15 | 1.23895 | 2525.04 | 2700.74 | 7.2542 | -- | VAPOR SOBREESCALFAT |
| 9 | 2 R-717 (Amoníac) | `P=0.2 · h=1200` | -18.85 C | 0.2 | 0.423529 | 1115.29 | 1200.00 | 4.8543 | 0.7115 | BIFASIC |

## Fuera de rango — debe dar pantalla roja de ERROR, nunca un número

| # | Sust | Entrada | Qué prueba |
|---|---|---|---|
| 10 | 1 R-718 (Aigua) | `P=1 · T=2000` | T por encima de lo tabulado |
| 11 | 1 R-718 (Aigua) | `P=1 · h=99999` | h imposible a esa presión |

## Qué mira cada caso

1. vapor saturado: x=1 debe dar exactamente h_g
2. líquido saturado: x=0 debe dar exactamente h_f
3. isóbara tabulada: sobre un nodo debe devolver el valor de la tabla
4. nodo exacto; la tabla publicada da h=3116,1
5. **inversa** por entropía, cae dentro de la campana
6. **doble interpolación** (entre las isóbaras de 1,2 y 1,4 MPa)
7. **líquido comprimido** con datos reales del PDF, sin aproximar
8. **fase cruzada**: la isóbara de 0,2 MPa da líquido a esa T → aviso — **debe salir el aviso naranja**
9. bifásico por entalpía en otra sustancia

## Los dos encadenados

Los casos 4 y 5 son el mismo problema: una turbina isentrópica de 3 MPa y 350 °C hasta 75 kPa. Del 4 sacas s = 6.7449, lo metes como segunda dato del 5, y el trabajo es la resta de las dos entalpías:

```
w = h1 - h2 = 3116.06 - 2403.01 = 713.05 kJ/kg
```

Si te salen esos dos, la búsqueda inversa funciona, que es la ruta más larga del motor.

## Métodos generalizados

Desde el menú, botón **2** (`GAS REAL`) y botón **3** (`PROCES REAL`). Las constantes del fluido se ponen una vez con `View` → *Constants del fluid* y se recuerdan; la cabecera de cada pantalla las repite, que es lo que evita arrastrar una Tc del problema anterior.

**Botón 2 — un estado.** Tc, Pc y ω en *Constants*, luego T y P.

| # | Constants | Entrada | Z⁰ | Z¹ | Z | (h−h\*)/RTc | (s−s\*)/R |
|---|---|---|---|---|---|---|---|
| G1 | `Tc=305.3 Pc=4.87 w=0.099` | `T=793.78 · P=14.61` | 1.0137 | 0.1706 | 1.0305 | -0.3846 | -0.1682 |
| G2 | `Tc=300 Pc=5 w=0.089` | `T=300 · P=5` | 0.2918 | -0.0789 | 0.2848 | -2.7859 | -2.3731 |
| G3 | `Tc=190 Pc=46 w=0` | `T=209 · P=69` | 0.4580 | 0.1630 | 0.4580 | -2.2027 | -1.5570 |

> El signo es el que dice la pantalla: **h−h\***, real menos ideal, negativo. Si el apunte tabula (h\*−h)/RTc, es el mismo número cambiado de signo.

**Botón 3 — el proceso 1→2.** Añade `cp*` a las constantes.

| # | Constants | Entrada | dh [J/mol] | ds [J/molK] | du [J/mol] |
|---|---|---|---|---|---|
| D1 | `Tc=190 Pc=46 w=0 cp*=34` | `T1=209 P1=69 · T2=228 P2=92` | 841.9 | 2.6403 | 575.2 |
| D2 | `Tc=280 Pc=5 w=0.09 cp*=0` | `T1=308 P1=10 · T2=308 P2=5` | 4430.1 | 17.3861 | 3686.0 |
| D3 | `Tc=300 Pc=5 w=0.089 cp*=43` | `T1=300 P1=5 · T2=390 P2=25` | 3536.3 | 3.8586 | 1835.8 |

Los tres son preguntas de examen: **D1** es la 9 del 14/04/2023 (85 mol · du = 49 kJ oficiales), **D2** la 7 del 02/11/2021 (10 mol · ds = 173,9 J/K oficiales) y **D3** la 2 del 09/04/2025 (difusor, 174,1 m/s oficiales).

**El depósito rígido.** Si en vez de la presión conoces el volumen molar, escríbelo en `v` y deja la `P` como esté: con `v>0` la presión pasa a ser el resultado y sale en verde. Es la pregunta 1 del 28/10/2025:

| # | Constants | Entrada | P1 [MPa] | P2 [MPa] | dP [MPa] |
|---|---|---|---|---|---|
| R1 | `Tc=300 Pc=7.5 w=0 cp*=37.4` | `T1=345 T2=315 · v1=v2=8.31601e-05` | 16.1373 | 10.3608 | -5.776 |

La oficial es **−6 MPa**, que es la opción *a)*; el número exacto sale a -5.78 porque la solución se leyó del gráfico.

## Los generalizados fuera de rango

Con `Tc=300 Pc=5 w=0`, botón 2 y `T=270 · v=7.4826e-5` — un volumen que cae **dentro de la campana** — la pantalla debe decir **Sense solucio**, nunca un número: ahí la ecuación de Lee-Kesler da presión negativa y no hay estado. Es el mismo criterio que las tablas, donde fuera de rango sale error visible en vez de una extrapolación silenciosa.

> Por `(T, P)` este fallo no existe, porque Z = Pr·Vr/Tr sale positivo siempre. Sólo aparece dando el volumen.

## Y en el PC

Estos casos comprueban que la calculadora hace lo mismo que el motor de referencia. Que el motor **acierte** lo decide `tests/test_aceptacion.py` para las tablas y `tests/test_lk_examenes.py` para los generalizados: los dos rehacen problemas ya resueltos de la asignatura contra su solución oficial.
