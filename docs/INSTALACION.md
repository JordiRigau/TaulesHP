# Instalar en la calculadora

Son **3 elementos**. Se pegan una sola vez; a partir de ahí todo se hace
arrastrando ficheros.

> **Por qué hay que pegar la primera vez.** `.hpprgm` es un formato binario
> (cabecera `7C 61 8A B2`, tabla de símbolos, fuente en UTF-16LE). Lo que
> genera este repositorio es texto, y el Connectivity Kit lo rechaza si lo
> arrastras. El binario lo tiene que escribir él, y sólo lo hace al guardar un
> programa.

## Pasos

1. Instala el **HP Connectivity Kit** — <https://hpcalcs.com/download/>
2. Conecta la calculadora (o abre el Virtual Calculator) y ábrelo. Aparece en
   el árbol de la izquierda; si sale en gris, doble clic.
3. Genera los ficheros:

   ```bash
   python tools/gen_merged.py --all
   ```

4. Crea cada programa con **clic derecho → Nuevo** sobre *Program*, con el
   nombre exacto, y pega dentro el contenido del `.txt`:

   | Nombre | Pegar | KB | Qué es |
   |---|---|---|---|
   | `TDAT` | `ppl/compacte/TDAT.txt` | 309 | las 14 sustancias |
   | `TERMOLIB` | `ppl/compacte/TERMOLIB.txt` | 18 | motor de cálculo |

5. Crea la app: `[Apps]` → tecla **(Save)** → *Base App*: **None** → nombre
   **`TAULES`** → OK. Selecciónala, pulsa `[Shift][1]` y `[▲]` para llegar a su
   programa, y pega `ppl/compacte/TAULES_APP_LIB.txt` (12 KB).
6. `[Apps]` → icono `TAULES`.

**El orden importa**: un programa sólo ve las funciones de otro si se compiló
después. `TDAT` → `TERMOLIB` → la app.

## Comprobar que ha quedado bien

Dos cálculos de [`PRUEBAS_CALCULADORA.md`](PRUEBAS_CALCULADORA.md). Por
ejemplo agua a `P=3`, `T=350`, que debe dar **h = 3116.06** y **s = 6.7449**.

## Variantes

`gen_merged.py` deja cuatro ficheros en `ppl/compacte/`:

- **3 elementos** (recomendada): `TDAT` + `TERMOLIB` + `TAULES_APP_LIB`. El
  motor vive en un programa del catálogo, así que **otra app puede llamarlo**
  (ver [`API.md`](API.md)).
- **2 elementos**: `TDAT` + `TAULES_APP` (motor dentro de la app). Un elemento
  menos, pero lo exportado desde el programa de una app queda ligado a esa app
  y deja de ser reutilizable.

Y en `ppl/txt/` está la versión por sustancia (un fichero cada una), por si
quieres cargar sólo algunas: `python tools/gen_ppl.py --list` las enumera.

Si cambias de variante, **borra antes los programas de la anterior**: dejarlos
daría nombres globales duplicados.

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

---

## Copia de seguridad

`ppl/` y `data/master.json` en el PC y en la nube. Si la calculadora se
resetea:

- con los binarios del Connectivity Kit a mano: **arrastrar los 3 ficheros**,
  menos de un minuto;
- desde cero: 3 pegados, unos 5 minutos;
- si se pierde el PC: basta el PDF y este repositorio —
  `python tools/extract_pdf.py` reconstruye `master.json` byte a byte.

---

## Dónde está probado

**HP Prime G2, firmware 2.4 revisión 15515 (2025-09-15)**, tanto en la
calculadora física como en el Virtual Calculator. Las notas de esa versión no
tocan la sintaxis de PPL, así que debería funcionar igual en revisiones
cercanas.

En **G1 no está probado**: el hardware es más lento y tiene menos memoria,
aunque el firmware es el mismo.
