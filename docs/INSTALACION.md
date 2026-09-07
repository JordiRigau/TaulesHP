# Instalar en la calculadora

Hay **dos montajes**, y cuál quieres depende de para qué:

| | Comando | Qué sale | Para |
|---|---|---|---|
| **1 elemento** | `build_hp.py --tot` | `TAULES.hpappdir` (740 KB) | **repartir** |
| **3 elementos** | `build_hp.py` | `TDAT` + `TERMOLIB` + `TAULES.hpappdir` | **desarrollar** |

El de 1 elemento mete los datos y el motor **dentro de la app**: se arrastra
un solo fichero y desaparece el fallo de instalación más fácil de cometer, que
es el orden. El de 3 deja el motor en un programa del catálogo, donde **otra
app puede llamarlo** (ver [`API.md`](API.md)) y donde el programa de la app
sigue siendo lo bastante pequeño para abrirlo en la calculadora.

Nada más cambia: son el mismo código y dan los mismos números.

---

## Para repartir: 1 elemento

```bash
python tools/gen_merged.py --all     # fuentes PPL
python tools/build_hp.py --tot       # el único fichero que se arrastra
```

1. Instala el **HP Connectivity Kit** — <https://hpcalcs.com/download/>
2. Conecta la calculadora (o abre el Virtual Calculator) y ábrelo. Aparece en
   el árbol de la izquierda; si sale en gris, doble clic.
3. **Arrastra `ppl/build/estudiants/TAULES.hpappdir` —la carpeta entera— SOBRE la
   calculadora** en la ventana del CK.
4. `[Apps]` → icono `TAULES`.

No hay ningún orden que vigilar: dentro va todo.

## Para desarrollar: 3 elementos

```bash
python tools/gen_merged.py --all
python tools/build_hp.py             # los 3 ficheros que se arrastran
```

| Fichero | KB | Qué es |
|---|---|---|
| `TDAT.hpprgm` | 619 | las 14 sustancias |
| `TERMOLIB.hpprgm` | 38 | motor de tablas |
| `TAULES.hpappdir` | 86 | la app: menú + interfaz + generalizados + icono |

Se arrastran los tres en **este orden**: `TDAT` → `TERMOLIB` → `TAULES`. Un
programa sólo ve las funciones de otro si se compiló después; al revés, la app
se abre pero no calcula.

Los **métodos generalizados van dentro de la app** en los dos montajes. No
llevan datos —salen de la ecuación de Lee-Kesler— y no los tiene que llamar
ningún otro programa, así que no ganan nada viviendo fuera.

## En cualquiera de los dos

> **La carpeta `Documentos\HP Connectivity Kit\Calculators\` no es un buzón.**
> Es un **espejo** que el CK escribe *desde* la calculadora: dejar ahí un
> fichero no instala nada, y al conectar se sobrescribe. Hay que arrastrar
> sobre la calculadora en la ventana del CK.

> **Si el arrastre sale con el cursor de prohibido**, no es el fichero: mira
> la pestaña *Compatibilidad* del CK (del acceso directo **y** del `.exe`).
> Con «ejecutar como administrador» activado, Windows prohíbe soltar ficheros
> de un proceso no elevado a uno elevado. Está contado en
> [`deploy.md` del kit](https://github.com/JordiRigau/hp-prime-kit/blob/main/docs/reference/deploy.md).

## Qué hace falta

`build_hp.py` necesita **[hp-prime-kit](https://github.com/JordiRigau/hp-prime-kit)**,
que es quien sabe escribir el contenedor `.hpprgm`:

```bash
git clone https://github.com/JordiRigau/hp-prime-kit.git ~/.claude/skills/hp-prime
```

o `HP_PRIME_KIT` apuntando a donde lo tengas. Si no está, `build_hp.py` se
salta con instrucciones y queda [la ruta de pegar](#si-no-quieres-instalar-el-kit),
que es la de siempre.

Antes de escribir nada, `build_hp.py` pasa el **linter** sobre los tres
ficheros a la vez y aborta si hay error: mejor no tener el binario que tener
uno que la calculadora rechace en el examen. Con `--set` mira además los
nombres exportados de los tres juntos, que es donde chocarían: por eso los
generalizados llevan todos el prefijo `TG` y el menú el prefijo `TM`.

### Por qué antes había que pegar

`.hpprgm` es un contenedor binario (cabecera `7C 61 8A B2`, registros
anidados, fuente en UTF-16LE) y la suposición era que sólo el Connectivity Kit
sabía escribirlo. **No es así**: el fuente va dentro *verbatim*, y el escritor
del kit genera el contenedor desde el PC. Su salida se ha cargado, compilado y
ejecutado en una **G2 real** (`SELFTEST`, en la documentación del kit).

### Y por qué `TDAT` tampoco necesita pegarse

Un programa de datos lleva delante del fuente un **bloque compilado**: los
números ya en el formato interno de la calculadora, que es lo que hace que
abra al instante. El kit no sabe generarlo, y durante un tiempo eso pareció
motivo para seguir pegando `TDAT` a mano.

**No lo es: ese bloque es una caché que la calculadora rehace.** Medido en una
G2 en dos pasos —se cambió un número dentro del bloque de un programa
instalado, dejando el fuente intacto, y la calculadora respondió con el valor
del **fuente** y devolvió el bloque **reconstruido**—. Un programa con datos
se genera como cualquier otro:
[`examples/datagen/`](https://github.com/JordiRigau/hp-prime-kit/tree/main/examples/datagen)
del kit tiene el experimento entero para repetirlo.

Tampoco hace falta compilar nada a mano después de arrastrar: medido en una G2
con media docena de programas transferidos y ejecutados sin compilarlos.

**Lo que sigue sin medirse es el coste, no la posibilidad.** El bloque existe
para ahorrar una compilación al llegar, y un fichero generado no lo trae, así
que la calculadora compila los 43.796 números al recibirlos. Con dos matrices
pequeñas es instantáneo; **con 619 KB no lo ha cronometrado nadie**, y en la
variante de 1 elemento son 740 KB dentro del programa de la app. Y hay un
aviso de segunda mano —contado, no medido— de que un programa muy grande puede
necesitar compilarse explícitamente: si no responde nada más llegar, la acción
de compilar está en el **catálogo de programas**.

> **Esto importa más al repartir.** Si el primer arranque tarda, quien instala
> la app no sabe si es normal o si ha hecho algo mal. Cronometra una vez el
> montaje de 1 elemento en una G2 antes de darlo, y si tarda, dilo en el
> correo que lo acompañe.

Los ficheros de este proyecto **no se han arrastrado todavía a una G2**: en el
PC se ha verificado que cada uno se relee idéntico y que la app coincide con lo
que un build produce, y eso es todo lo que el PC puede decir.

## Comprobar que ha quedado bien

Dos cálculos de [`PRUEBAS_CALCULADORA.md`](PRUEBAS_CALCULADORA.md). Por
ejemplo agua a `P=3`, `T=350`, que debe dar **h = 3116.06** y **s = 6.7449**.

Y sin tocar la calculadora, el mismo cálculo sobre el fichero que vas a
instalar. El de 1 elemento:

```bash
python ~/.claude/skills/hp-prime/hpprime.py run ppl/compacte/TAULES_APP_TOT.txt --call "TLOAD(1)" --call "TPT(3,350)"
```

y el de 3:

```bash
python ~/.claude/skills/hp-prime/hpprime.py run ppl/compacte/TDAT.txt ppl/compacte/TERMOLIB.txt --call "TLOAD(1)" --call "TPT(3,350)"
```

`tests/test_ppl_gener.py` ya hace esa comprobación sobre el fichero de 1
elemento en cada ejecución.

## Las tres variantes

`gen_merged.py` deja cinco ficheros en `ppl/compacte/`, que arman tres
montajes distintos:

| Variante | Fuente | Comando | Cuándo |
|---|---|---|---|
| **1** | `TAULES_APP_TOT` | `--tot` | repartir: un fichero, ningún orden |
| **2** | `TDAT` + `TAULES_APP` | `--dos` | motor dentro de la app, datos fuera |
| **3** | `TDAT` + `TERMOLIB` + `TAULES_APP_LIB` | *(por defecto)* | desarrollar |

La de **3** es la que deja el motor reutilizable: lo exportado desde el
programa de una app queda ligado a esa app, mientras que lo exportado desde un
programa del catálogo es global sin discusión. Si vas a escribir otra app que
llame al motor, es la única que sirve — ver [`API.md`](API.md).

La de **1** no gana nada técnico. Al revés: el programa de la app pasa de
36 KB a 361 KB de fuente y editarlo en la calculadora deja de ser cómodo. Lo
que gana es que **se arrastra un fichero y ya está**, que es lo que hace falta
cuando la instala alguien que no ha visto nunca el Connectivity Kit.

`TAULES_APP_TOT.txt` lleva los datos dentro, así que **no se versiona**, igual
que `TDAT.txt`: se regenera con `gen_merged.py --all`.

En `ppl/` está además la versión por sustancia (`TDAT_AIGUA.txt`,
`TDAT_R134A.txt`…), por si quieres cargar sólo algunas:
`python tools/gen_ppl.py --list` las enumera.

Si cambias de variante, **borra antes de la calculadora lo de la anterior**:
dejarlo daría nombres globales duplicados. El caso que más se va a dar es
pasar del montaje de 1 al de 3 —o al revés— en la misma calculadora: el
`TAULES` de 1 elemento ya lleva dentro todo lo que `TDAT` y `TERMOLIB` traen
por su cuenta.

Cada variante tiene su carpeta —`ppl/build/estudiants/`, `ppl/build/dev/`,
`ppl/build/dos/`— y un build **vacía la suya antes de escribir**, para que no
queden ahí los ficheros del montaje anterior y se arrastren por error. Las de
las otras variantes se quedan donde estaban, así que puedes tener a mano la de
los estudiantes y la de desarrollo a la vez.

## Si no quieres instalar el kit

La ruta manual sigue siendo válida y no necesita nada más que el CK:

1. `python tools/gen_merged.py --all`
2. `[Apps]` → tecla **(Save)** → *Base App*: **None** → nombre **`TAULES`** →
   OK. Selecciónala, pulsa `[Shift][1]` y `[▲]` para llegar a su programa, y
   pega `ppl/compacte/TAULES_APP_TOT.txt`. Es un solo pegado, pero son 361 KB
   de texto.
3. Para la variante de 3, en vez de eso: clic derecho sobre *Program* →
   **Nuevo**, nombre exacto `TDAT`, y pegar `ppl/compacte/TDAT.txt`; igual con
   `TERMOLIB`; y en el programa de la app, `TAULES_APP_LIB.txt`.

Mismo resultado; son unos 5 minutos en vez de un arrastre.

---

## Pasarlo a otra calculadora

Los ficheros de `ppl/build/` valen para cualquier calculadora: se arrastran
igual. Y hay dos atajos más:

- Dentro del CK se puede **arrastrar de una calculadora a otra**.
- La Prime admite transferencia **directa entre calculadoras por USB OTG**
  (opción *Send* de los catálogos), sin PC de por medio.

Una vez instalada, el CK tendrá en
`Documentos\HP Connectivity Kit\Calculators\<tu calculadora>\` una copia de lo
que hay en la calculadora — incluido `TDAT` **ya con su bloque compilado**, que
es el que abre al instante. Ése es el que conviene copiar y guardar para
reinstalar rápido, aunque sale de la calculadora y no del PC.

Para comparar lo instalado con el repositorio, sin fiarse de la memoria:

```bash
python ~/.claude/skills/hp-prime/hpprime.py read ".../Calculators/HP Prime/TERMOLIB.hpprgm" -o instalado.txt
diff instalado.txt ppl/compacte/TERMOLIB.txt
```

---

## Copia de seguridad

`ppl/` y `data/master.json` en el PC y en la nube. Si la calculadora se
resetea:

- con el repositorio a mano: **dos comandos y tres arrastres**, menos de un
  minuto;
- si se pierde el PC: basta el PDF y este repositorio —
  `python tools/extract_pdf.py` reconstruye `master.json` byte a byte.

---

## Dónde está probado

**HP Prime G2, firmware 2.4 revisión 15515 (2025-09-15)**, tanto en la
calculadora física como en el Virtual Calculator, **instalada pegando el
texto**. Las notas de esa versión no tocan la sintaxis de PPL, así que debería
funcionar igual en revisiones cercanas.

En **G1 no está probado**: el hardware es más lento y tiene menos memoria,
aunque el firmware es el mismo.
