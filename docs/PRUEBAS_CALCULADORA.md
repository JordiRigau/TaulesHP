# Batería de pruebas en la calculadora

Generado por `tools/gen_pruebas.py` desde el motor de referencia.
**No editar a mano**: si cambian el motor o los datos, se regenera.

Que compile no significa que calcule bien. Estos casos cubren **todas las rutas del motor**: cada región, la interpolación doble, la búsqueda inversa, la regla de la palanca, el caso de fase cruzada y el fallo fuera de rango.

> **Antes de empezar**: ten la app instalada y comprueba que la sustancia del caso aparece en el desplegable. El montaje está en el README.

En cada caso: ejecuta `TERMO()`, elige la sustancia, pon las dos magnitudes en los desplegables `Dada 1` / `Dada 2` y teclea sus valores. Los campos de valor son numéricos: el número se escribe directamente, sin comillas. El orden de las dos no importa.

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

## Después

Calcula el caso 4 y después el 5 (se guardan solos, sin pulsar nada) y ejecuta `TDELTA()`. Debe dar:

```
dh = -713.05 kJ/kg
du = -588.73 kJ/kg
ds = 0.0000 kJ/kgK
dv = 1.874099 m3/kg
dT = -258.24 C
dP = -2.92500 MPa
```

Es el trabajo de una turbina isentrópica de 3 MPa y 350 °C hasta 75 kPa: **w = −Δh = 713.05 kJ/kg**.

## Lo que aún falta

**La prueba de aceptación de verdad**: 3-5 problemas ya resueltos de la asignatura, de principio a fin. Si no reproduce las soluciones oficiales, la app no sirve por muy verdes que estén estas pruebas.
