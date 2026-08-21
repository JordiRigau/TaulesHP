# Prompt para agente: diseño de una app de propiedades termodinámicas para HP Prime G2

Actúa como un ingeniero con experiencia real construyendo apps para la HP Prime (no solo programas sueltos) y como arquitecto de pipelines de extracción de datos con LLMs. No me des una respuesta superficial ni genérica tipo "esto se puede hacer de varias formas": quiero que investigues, decidas y justifiques una ruta concreta, señalando explícitamente los trade-offs que descartas y por qué. Si algo depende de información que puede haber cambiado (versiones de firmware, del Connectivity Kit, de la API de Gemini), búscalo en vez de asumir de memoria.

## Contexto

- Calculadora: HP Prime **G2**, firmware con build **20250915**.
- **Puedo usar mis propias apps en el examen sin restricciones** (no se aplica Exam Mode ni reset previo). Por tanto el diseño se optimiza para **velocidad de uso bajo presión de examen**, no para claridad pedagógica.
- Las tablas están en un PDF y se van a extraer con la API de Gemini (crédito de ~10 €, así que el uso del modelo debe ser eficiente en coste).
- Quiero iterar rápido en desarrollo sin pasar el archivo a la calculadora física cada vez.

### Naturaleza real de los datos (leer con atención: condiciona toda la arquitectura)

El PDF contiene **dos tipos estructuralmente distintos de tabla**:

1. **Tablas de saturación** (zona de equilibrio líquido + vapor). Son unidimensionales: indexadas por T o por P, dando los valores de líquido saturado y vapor saturado (v_f, v_g, u_f, u_g, h_f, h_g, s_f, s_g, y posiblemente los "fg"). Nota que la tabla por T y la tabla por P describen **la misma curva de saturación** — son redundantes entre sí, y eso tiene implicaciones de memoria y de consistencia que debes analizar.
2. **Tablas isobaras** (zona de vapor sobrecalentado). Cada tabla está a P fija, con filas en T dando v, u, h, s. Interpolar aquí requiere **doble interpolación**: primero en T dentro de cada isobara, luego entre isobaras adyacentes en P.

Las propiedades manejadas son al menos **u, h, s** (y presumiblemente v). Verifica en el PDF cuáles hay exactamente.

Además, la asignatura usa mucho el **título x** (calidad del vapor), que **no aparece tabulado** pero sí debe existir en la app como variable de primera clase. Esto implica:
- Cálculo directo: `y = y_f + x·(y_g − y_f)` para cualquier propiedad y en la zona bifásica.
- Cálculo inverso: dado h (o s, o v) y P (o T), obtener `x = (y − y_f)/(y_g − y_f)`.

**La búsqueda inversa es imprescindible**, no opcional: dado h o s, encontrar T (o x). Es lo que se usa constantemente en procesos isentrópicos.

## Lo que debes investigar y decidir

### 1. Cómo aprender la sintaxis de HP PPL de forma eficiente (la doc oficial es rara)
- El manual oficial (HP Prime User Guide / HP Prime Programming Reference Guide) existe, pero está organizado de forma poco práctica para aprender: mezcla referencia de comandos matemáticos con sintaxis de programación, y a menudo no explica bien el comportamiento real (errores, casos límite). Úsalo como referencia puntual, no como fuente principal de aprendizaje.
- Complementa con fuentes de comunidad que suelen explicar mejor con ejemplos reales y funcionando: el foro de HP Museum (hpmuseum.org/forum, subforo HP Prime), en.hpprime.club (tutoriales de Edward Shore / Hans Klaver), Eddie's Math and Calculator Blog, y el archivo de programas de hpcalc.org. Prioriza fuentes con código completo y comentado por encima de listados sueltos de comandos.
- **Busca si ya existe una app/programa de tablas de vapor para HP Prime** en hpcalc.org o en el foro de HP Museum. Aunque no la use tal cual, ver cómo otro resolvió el problema de almacenar tablas irregulares en PPL vale más que cualquier tutorial genérico.
- Si en algún momento durante el proyecto genero código PPL que compile y funcione correctamente (aunque sea solo un fragmento pequeño y probado en el emulador), trátalo como referencia de estilo válida para el resto del desarrollo.
- Propón validar la sintaxis de forma empírica: escribir fragmentos pequeños en el editor del Virtual Calculator y usar los errores del compilador como retroalimentación rápida, en lugar de intentar interiorizar toda la sintaxis leyendo el manual de golpe.
- Salida de esta fase: un mini **cheat sheet** de sintaxis PPL relevante para este proyecto (tipos de datos, estructuras de control, manejo de listas/matrices anidadas, comandos de UI).

### 2. El problema central: determinación de región y enrutado
Esta es la parte difícil del proyecto, y el plan debe atacarla antes que la interpolación.

- Dado un par de propiedades conocidas, la app debe **primero decidir en qué región está el estado** (líquido comprimido / mezcla bifásica / vapor sobrecalentado) y solo entonces elegir tabla y algoritmo. Diseña esa lógica de decisión explícitamente.
- Ejemplo del caso típico: dado (P, h), comparar h contra h_f(P) y h_g(P) de la tabla de saturación → si h < h_f es líquido, si h_f ≤ h ≤ h_g es mezcla (y entonces x sale de la interpolación), si h > h_g es sobrecalentado (y hay que ir a las isobaras).
- Enumera **qué pares de entrada debo poder introducir** y cuáles son realistas en mi asignatura: (T,P), (P,x), (T,x), (P,h), (P,s), (T,s), (P,v)… Para cada par, di qué región puede resultar y qué ruta de cálculo sigue. Si algún par es ambiguo o mal condicionado, dilo.
- Decide si la app cubre **líquido comprimido** o si se aproxima por líquido saturado a la T dada (que es lo que se suele hacer en cursos de grado). Si el PDF no trae tabla de líquido comprimido, esa aproximación debe estar implementada y **señalizada en pantalla** para que yo sepa que es una aproximación.

### 3. Estructura de datos: el problema de la rejilla irregular
- Las tablas de sobrecalentado **no forman una matriz rectangular limpia**: cada isobara empieza a una T distinta (su T_sat) y tiene un número distinto de filas. Es una rejilla dentada (*ragged*). Propón cómo almacenarla en PPL (listas de listas, matriz con relleno de valores centinela, strings serializados…) y justifica la elección por memoria y por velocidad de acceso.
- Consecuencia crítica que debes resolver: al interpolar entre dos isobaras a una T dada, **puede que una de las dos isobaras no tenga datos a esa T** (porque a esa presión el estado aún es saturado). Define qué hace la app en ese caso — no lo dejes implícito.
- Analiza la redundancia entre la tabla de saturación por T y por P: ¿guardar ambas, o guardar una y obtener la otra por interpolación inversa? Ten en cuenta que **P_sat(T) es fuertemente no lineal** (exponencial, tipo Clausius-Clapeyron), así que interpolar linealmente entre puntos espaciados introduce error real. Cuantifícalo antes de decidir.
- Límites de memoria/almacenamiento de la G2 para el volumen de datos que esto supone (estima el número total de valores numéricos y el peso resultante), y a partir de qué punto el compilado se vuelve lento.

### 4. Interpolación y precisión
- El método es **lineal** — porque es el que se usa en la asignatura. Esto no es negociable aunque existan métodos más precisos.
- Punto importante que debe guiar todas las decisiones de precisión: **el objetivo es reproducir el valor que da la solución oficial del profesor, no el valor físicamente más exacto**. Si un método más sofisticado se aleja de lo que sale al interpolar linealmente a mano, es el método equivocado para este proyecto. Aplícalo especialmente al caso de P_sat(T) del punto anterior.
- Para sobrecalentado, implementa la **doble interpolación** en el mismo orden que se hace a mano en clase (normalmente T primero dentro de cada isobara, luego P), para que los resultados coincidan con los de la solución esperada.
- **Comportamiento fuera de rango**: si introduzco una T o P fuera del rango tabulado, la app debe avisar de forma explícita y visible, nunca extrapolar en silencio. Un número plausible pero inventado en un examen es peor que un error claro.
- **Precisión de display**: las tablas traen 4–5 cifras significativas. Define el formato de salida para que no aparezcan decimales de falsa precisión.
- **Búsqueda inversa**: diseña el algoritmo. En la zona bifásica es despeje directo de x. En sobrecalentado, dado (P, s) hallar T requiere buscar el intervalo dentro de la isobara e interpolar inversamente. Ten en cuenta que las columnas deben ser monótonas para que la inversa sea única — verifica esa monotonía en los datos y decide qué hacer si se rompe.

### 5. Diseño de la app y UX
- Explica la diferencia real entre una **Application** (App Library, icono propio, vistas Symb/Plot/Num/Setup, variables persistentes, hooks `App.Start()`, `App.View()`) y un **Program** (`.ppl` suelto en el Program Catalog), y recomienda cuál encaja aquí.
- La decisión de UI central es **cómo indico qué dos propiedades conozco**. Diseña ese flujo: ¿un menú `CHOOSE` de pares predefinidos? ¿un formulario con campos vacíos donde relleno dos y dejo el resto en blanco? Evalúa ambas y elige.
- Criterio de diseño medible: el **número de pulsaciones desde encender la calculadora hasta tener el valor en pantalla**. Cuenta ese número explícitamente para cada alternativa. Bajo presión de examen, 5 pulsaciones baten a 12 aunque las 12 sean más elegantes. Optimiza el caso más frecuente.
- La salida debe mostrar **todas las propiedades del estado a la vez** (T, P, v, u, h, s, x y la región identificada), no solo la que pedí — en un problema de examen normalmente necesito varias del mismo estado, y volver a entrar cuesta pulsaciones.
- Considera si conviene poder **guardar dos o tres estados** (típico: estado 1 y estado 2 de un proceso) para no perderlos al calcular el siguiente.

### 6. Emulador para iterar sin cable
- Confirma y documenta cómo usar el **HP Prime Virtual Calculator** junto al **HP Connectivity Kit** en PC para desarrollar y probar sin transferir constantemente a la calculadora física. (Dato ya verificado: la versión 2.4.15515 del Virtual Calculator/Connectivity Kit está fechada 2025-09-15, coincidiendo con la build de firmware 20250915 — parte de ahí, pero confirma que sigue vigente y es compatible con G2.)
- Explica el flujo recomendado: ¿editar el `.hpprgm`/`.hpappdir` en el PC y recargarlo, o copiar/pegar en el editor del emulador? ¿Cómo se sincroniza con la calculadora física solo cuando ya está validado?
- **Backup y recuperación**: define cómo restaurar la app rápido si la calculadora se resetea (copia del `.hpappdir` en PC y en la nube, procedimiento cronometrado). Quiero saber en cuántos minutos vuelvo a tenerla funcionando.

### 7. Extracción de las tablas del PDF con la API de Gemini
- Diseña el schema de extracción teniendo en cuenta que **hay dos estructuras distintas de tabla** (saturación 1D e isobaras dentadas). Probablemente necesites dos schemas, no uno.
- El schema debe capturar explícitamente la **presión de cada isobara** y las **unidades** de cada columna, no solo los números sueltos.
- Recomienda usar **structured output / response schema** de la API en lugar de texto libre, para minimizar alucinaciones y parseo manual.
- Presupuesto ~10 €: recomienda el modelo Gemini más barato que dé fiabilidad aceptable en tablas numéricas, y cómo trocear el PDF (por tabla, por página) para no gastar de más ni partir una tabla por la mitad. Estima el coste total.
- **Verifica primero si el PDF es texto o escaneado**: cambia por completo la fiabilidad esperada y el enfoque.
- Verificación de la extracción: monotonía de columnas, coherencia física (v_g > v_f, h_g > h_f, s_g > s_f), continuidad entre la última fila de saturación y la primera de cada isobara, y muestreo manual contra el PDF.
- **Fuente única de verdad**: el JSON maestro en el PC es la única versión editable. El bloque de datos PPL debe **generarse por script** (Python), nunca editarse a mano. Si detecto un valor mal extraído lo corrijo en el maestro y regenero. Incluye ese generador en el plan.

### 8. Estrategia de pruebas — datos vs. app
- **Pruebas de los datos extraídos**: validar antes de subirlos, comparando contra referencia externa (NIST WebBook para agua) o contra valores verificables a mano.
- **Pruebas de la app**: monta un arnés de test en PPL (la Prime no tiene framework de testing) que recorra casos conocidos e imprima PASS/FAIL.
- Trampa metodológica a evitar: implementar el mismo algoritmo dos veces (PPL y Python) y comparar **solo detecta errores de transcripción, no de lógica** — si el algoritmo está mal concebido, ambas implementaciones coinciden en el mismo error. Los valores esperados deben venir de fuente independiente: valores leídos directamente del PDF (donde la interpolación debe devolver exactamente el valor tabulado), o ejercicios resueltos de clase con solución conocida.
- La batería debe cubrir específicamente:
  - Punto exactamente tabulado (debe devolver el valor exacto).
  - Estado justo en la frontera: x = 0 y x = 1 (la app debe coincidir con h_f y h_g).
  - Estado bifásico intermedio con x conocido.
  - Estado sobrecalentado que requiera doble interpolación.
  - Estado a una T donde una de las dos isobaras vecinas no tenga datos.
  - Búsqueda inversa en ambas regiones.
  - Entrada fuera de rango (debe fallar visiblemente).
- **Test de aceptación final**: coge 3–5 problemas ya resueltos de la asignatura y compruébalos de principio a fin con la app. Si no reproduce las soluciones oficiales, la app no sirve por muy bien que pasen los tests unitarios.

## Entregable esperado

Quiero de vuelta:
1. El cheat sheet de sintaxis PPL, con las fuentes usadas.
2. El **diseño de la lógica de determinación de región y enrutado**, con la tabla de pares de entrada admitidos y su ruta de cálculo. Esta es la pieza central.
3. La estructura de datos elegida para las tablas dentadas, justificada, con estimación de memoria.
4. El diseño de la app: app vs. programa, flujo de UI, conteo de pulsaciones, formato de salida.
5. El pipeline de extracción con Gemini (schemas, chunking, coste estimado) y el generador de código de datos.
6. El plan de pruebas, separado en datos y app, con los casos límite enumerados arriba.
7. Riesgos y cuellos de botella (memoria, rejilla dentada cerca de la línea de saturación, no linealidad de P_sat, fiabilidad de la extracción) y cómo los mitigarías.

No implementes nada todavía — primero quiero el plan razonado y las decisiones de arquitectura. Si detectas que alguna suposición mía sobre la estructura de los datos es incorrecta o incompleta, dímelo antes de construir sobre ella.
