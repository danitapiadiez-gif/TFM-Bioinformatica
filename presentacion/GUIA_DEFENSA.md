# Guía de estudio · Defensa TFM · data.lung
**Daniel Tapia Díez · UAX · Máster Bioinformática**

Este documento tiene **dos partes**:

1. **Parte A · Conceptos clave** — explicación llana de todo lo que puede aparecer en preguntas del tribunal.
2. **Parte B · Guion diapositiva por diapositiva** — lo que dices en cada una, con timing y transiciones.

> Consejo: léelo dos veces enteras antes del día D. La víspera, sólo la parte B.

---

# PARTE A · Conceptos clave (glosario razonado)

## 1. Transcriptómica y expresión génica

- **ADN**: es el libro de instrucciones de la célula. Todas las células de tu cuerpo tienen el mismo ADN.
- **Genes**: son "frases" concretas dentro del libro. Un gen codifica una proteína (o una función reguladora).
- **Expresión génica**: no todos los genes se "leen" al mismo tiempo. Una célula del pulmón lee genes distintos que una del hígado. La expresión es *cuánto* se está leyendo cada gen.
- **Transcriptoma**: el conjunto completo de genes activos en una muestra en un momento dado. Cuando decimos "medir la expresión", medimos el transcriptoma.
- **¿Por qué importa en cáncer?** Un tumor tiene un patrón de expresión distinto del tejido sano y, dentro de los tumores, adenocarcinoma y escamoso tienen patrones distintos. Esa **firma de expresión** puede usarse para diagnóstico o pronóstico.

## 2. Cómo se mide la expresión: microarrays y RNA-Seq

- **Microarray**: un chip de vidrio con miles de sondas de ADN pegadas. Vuelcas ARN de tu muestra, se une a las sondas complementarias y se mide la intensidad de fluorescencia. Es la tecnología antigua (2000-2015), barata y muy usada en estudios GEO clásicos.
- **RNA-Seq**: se secuencia directamente todo el ARN de la muestra. Tecnología moderna (2015 en adelante), más precisa y cuantitativa, y estándar en TCGA.
- **Por qué importa a este TFM**: el framework se entrenó en **microarrays** (11 cohortes GEO). Para validar externamente, se comprobó que el panel también funciona en **RNA-Seq** (TCGA). Que un panel entrenado en microarray funcione en RNA-Seq demuestra que la señal es real, no un artefacto tecnológico.

## 3. GEO (Gene Expression Omnibus) y cohortes

- **GEO**: repositorio público del NCBI (Estados Unidos) con más de 200.000 estudios de expresión génica. Cualquier grupo científico puede depositar sus datos allí.
- **Cohorte / estudio / dataset**: usados como sinónimos. Cada uno tiene un identificador tipo `GSE10245`, `GSE31210`, etc.
- **Metadatos**: son las descripciones de cada muestra (edad del paciente, si es tumor o sano, subtipo, estadio, etc.). En GEO están en **texto libre**, sin ninguna estructura. Por eso el paso 3 del pipeline necesita un LLM: convertir texto no estructurado en etiquetas canónicas.

## 4. Adenocarcinoma vs Carcinoma escamoso

- Son los dos subtipos más frecuentes de cáncer de pulmón no microcítico (que a su vez es el 85% de los cánceres de pulmón).
- **ADC (adenocarcinoma)**: se origina en las células glandulares (que producen mucosidad). Suele aparecer en la periferia del pulmón. Marcadores clásicos: TTF-1, napsina A.
- **SQC (carcinoma escamoso)**: se origina en las células que recubren las vías respiratorias. Suele aparecer más central. Marcadores clásicos: p40, CK5/6, DSG3.
- **Por qué es crítico distinguirlos**: el tratamiento cambia. **Pemetrexed** (quimio) y **bevacizumab** (antiangiogénico) están **contraindicados en escamoso** por riesgo de hemorragia mortal. Un diagnóstico erróneo puede matar al paciente.

## 5. Inmunohistoquímica (IHC) y panel OMS

- **IHC**: técnica del laboratorio de anatomía patológica. Se usan anticuerpos con un marcador fluorescente o cromogénico que se unen a proteínas específicas. Es lo que hace el patólogo cuando mira al microscopio tras teñir.
- **Panel OMS 2015** (Travis et al.): la Organización Mundial de la Salud recomienda un conjunto pequeño de marcadores para el diagnóstico rutinario de cáncer de pulmón. En este TFM, ese panel se toma como **verdad clínica**.
- **Marcadores del panel** que aparecen en la memoria:
  - **Escamoso**: KRT5, KRT6A, KRT6B, KRT13, KRT14, KRT15, KRT16, KRT17, CDH3, DSG3, PKP1, TP63.
  - **Adenocarcinoma**: NKX2-1 (TTF-1), NAPSA (napsina A), SFTPB, SFTPC, SFTPA1, SFTPA2, MUC1, CEACAM5, CEACAM6, KRT7.
- **La validación del TFM**: la firma de 20 genes seleccionada por LASSO **recupera 18 de los 20 marcadores del panel OMS** sin que se le dijera nada del panel. Eso es un aval biológico fortísimo.

## 6. Modelos de lenguaje (LLM), Llama y Groq

- **LLM**: modelo estadístico entrenado con enormes cantidades de texto que aprende a generar y clasificar lenguaje natural. GPT-4, Claude, Gemini, Llama, etc.
- **Llama 3.3-70b**: LLM de código abierto publicado por Meta. Los "70b" son 70.000 millones de parámetros. Es el modelo usado para curar los metadatos de GEO.
- **Groq**: empresa que ofrece infraestructura de inferencia ultrarrápida (hardware LPU en vez de GPU). Sirve modelos abiertos como Llama con latencias de decenas de milisegundos, lo que hace viable procesar miles de muestras.
- **¿Por qué un LLM en bioinformática?** Los metadatos GEO están en texto libre, escritos por humanos, con abreviaturas, faltas de ortografía y sinónimos. Codificar reglas de expresión regular para todos los casos es imposible. Un LLM entiende el contexto: le pasas "*primary lung tumor, LUSC, stage III*" y devuelve la etiqueta canónica `LUSC`.

## 7. Batch effect y por qué integrar cohortes es difícil

- **Efecto lote (batch effect)**: cuando integras muestras de laboratorios distintos, la mayor parte de la varianza no viene de la biología, viene de la técnica: el chip usado, el reactivo, el operador, el año.
- **ComBat**: algoritmo clásico (Johnson et al., 2007) que "corrige" el efecto lote normalizando cohortes. Problema: si el efecto lote está confundido con la variable de interés (por ejemplo, un centro sólo tiene muestras tumorales y otro sólo sanas), ComBat borra también la señal biológica real.
- **En este TFM**: no se aplica ComBat. En su lugar, se usa un enfoque de **meta-análisis por consenso** (siguiente punto).

## 8. Meta-análisis por consenso

- Cada cohorte se analiza **por separado**.
- Para cada gen y cada cohorte, se calcula el **tamaño de efecto d de Cohen** (diferencia estandarizada entre grupos):

  d = (media_tumor − media_sano) / desviación_típica_conjunta

  |d| > 0,5 se considera efecto moderado; |d| > 0,8 grande.
- Un gen entra en la firma sólo si mantiene **el mismo signo** y **|d| > 0,5** en al menos las cohortes exigidas por el criterio (en el TFM: 3 cohortes independientes).
- Ventaja frente a ComBat: es más conservador y no fuerza normalizaciones. Sólo sobreviven señales robustas.

## 9. LODO — Leave-One-Dataset-Out

- Es una variante muy estricta de validación cruzada.
- Si tienes N cohortes, entrenas con N-1 y evalúas con la que dejas fuera. Repites N veces, cada vez dejando fuera una cohorte distinta.
- **Contraste con validación cruzada estándar**: la CV normal (k-fold) mezcla muestras de todas las cohortes. Como dos muestras de la misma cohorte comparten sesgos técnicos, si entrenas y evalúas con muestras de la misma cohorte estás *inflando* el rendimiento. LODO lo evita.
- **En este TFM**: LODO es el criterio de rendimiento principal. Un AUC = 0,925 en LODO es **más creíble** que un AUC = 0,95 en CV k-fold.

## 10. Aprendizaje automático usado

### LASSO (regresión logística con regularización L1)

- Es un modelo lineal con una penalización que fuerza a que muchos coeficientes se hagan exactamente cero. Resultado: selecciona *sólo* los genes útiles y descarta el resto.
- **Ventajas**: (i) panel pequeño e interpretable (puedes leer los coeficientes por gen); (ii) determinista con un `random_state` fijo (reproducibilidad); (iii) un solo hiperparámetro (C, la inversa de la fuerza de regularización).
- **Es el método principal del TFM**.

### Random Forest (RF)

- Un "bosque" de árboles de decisión. Cada árbol se entrena con una submuestra aleatoria de los datos y una selección aleatoria de variables. Se vota entre árboles.
- No hace selección de variables tan agresiva como LASSO, pero da un **ranking de importancia** útil como complemento.
- En el TFM: AUC 0,933 (ligeramente mejor que LASSO), pero se descartó como principal porque no da un panel interpretable.

### SVM (Support Vector Machine)

- Encuentra el hiperplano óptimo que separa dos clases en un espacio de alta dimensión. Puede usar kernels (RBF) para separaciones no lineales.
- En el TFM: AUC 0,957 (el mejor absoluto), pero los pesos son difíciles de interpretar como "importancia de gen".

### ¿Por qué LASSO si SVM da más AUC?

Interpretabilidad clínica. Diferencia de 3 puntos de AUC no compensa perder un panel que un clínico puede leer.

## 11. Métricas de rendimiento

- **AUC (Area Under the ROC Curve)**: probabilidad de que el modelo ordene una muestra positiva por encima de una negativa. Va de 0,5 (azar) a 1,0 (perfecto). Independiente del umbral.
- **Sensibilidad** (recall / true positive rate): de todos los positivos reales, cuántos detecto. Si tengo 100 tumores y detecto 95, sensibilidad = 0,95.
- **Especificidad**: de todos los negativos reales, cuántos descarto correctamente.
- **Balanced Accuracy (BalAcc)**: media de sensibilidad y especificidad. Útil cuando las clases están desbalanceadas.
- **PPV / VPP**: valor predictivo positivo. De los que predije positivos, cuántos lo son de verdad. Depende de la prevalencia.
- **Regla mnemotécnica**: sensibilidad = "no se me escape ninguno enfermo"; especificidad = "no marque como enfermo a alguien sano".

## 12. Calibración (isotónica y Platt)

- Un modelo puede tener buen AUC pero puntuaciones **descalibradas** entre cohortes. Ejemplo: predice 0,8 y en realidad la probabilidad es 0,5.
- **Calibración**: transforma la puntuación cruda del modelo en una probabilidad bien calibrada usando datos de validación.
  - **Platt scaling**: una regresión logística sobre las puntuaciones.
  - **Isotónica**: una función monótona no paramétrica; más flexible.
- **En el TFM**: la calibración isotónica sube BalAcc de 0,772 → 0,810 y AUC de 0,925 → 0,953. Es especialmente importante en tumor-vs-sano porque el umbral óptimo cambia entre cohortes.

## 13. Bootstrap y intervalos de confianza

- **Bootstrap**: técnica de remuestreo. Del conjunto de muestras tomas N con reemplazo, recalculas la métrica, y repites (p. ej. 1000 veces). La distribución de esas 1000 métricas te da la incertidumbre.
- **IC 95% bootstrap**: los percentiles 2,5 y 97,5 de esa distribución.
- **Ejemplo del TFM**: AUC TCGA = 0,857, IC 95% = [0,812; 0,899]. Significa que si repitiéramos el experimento muchas veces, en el 95% de las repeticiones el AUC caería entre esos dos valores.

## 14. TCGA y cBioPortal

- **TCGA (The Cancer Genome Atlas)**: gran consorcio del NIH americano que caracterizó molecularmente miles de tumores humanos. Para pulmón hay dos proyectos: **TCGA-LUAD** (adenocarcinoma, ≈500 pacientes) y **TCGA-LUSC** (escamoso, ≈500 pacientes).
- **cBioPortal**: portal web y API pública (`www.cbioportal.org`) que permite descargar los datos de TCGA de forma limpia. En el TFM se usó su REST API.
- **Papel en el TFM**: validación externa RNA-Seq. Se aplica el panel LASSO ya entrenado en microarray a TCGA (n=408) y sale AUC = 0,857. Es prueba de que la firma es transferible entre plataformas.

## 15. Correlación de Spearman (ρ)

- Medida de asociación entre dos variables ordinales.
- ρ = 1: monotónica positiva perfecta; ρ = -1: monotónica negativa perfecta; ρ ≈ 0: no hay asociación.
- **En el TFM**: la firma correlaciona negativamente con la composición alvéolo-capilar (ρ = -0,626 media, hasta ρ = -0,858 en GSE31210). Se interpreta biológicamente: cuanto más tumor, menos alvéolos.

## 16. Streamlit y la interfaz data.lung

- **Streamlit**: framework Python para crear apps web interactivas sin escribir HTML/JS. Cada script Python es una página.
- **data.lung**: la app multipágina del TFM. Tiene: portada, framework, resultados (con buscador de gen), cohortes individuales, y un asistente conversacional Llama que sólo responde con los resultados del trabajo.
- **Reproducibilidad**: todas las cifras se leen de los CSV generados por el pipeline. Ningún número está "hardcodeado". Si mañana rehiciera el pipeline con más cohortes, la app se actualiza sola.

## 17. Ejes biológicos reales (interpretación)

La firma no es una caja negra: al analizarla, aparecen dos ejes claros.

- **Eje 1 · Pérdida alvéolo-capilar**: genes como SFTPC, SFTPB, AGER, CLDN18 (típicos de neumocitos y capilares). Cuanto más tumor, menos estos genes. Es lógico: el tumor sustituye al parénquima normal.
- **Eje 2 · Actividad proliferativa**: genes como MKI67 (marcador clásico Ki-67 usado en clínica), TOP2A, CCNB1, BIRC5, AURKA. Cuanto más agresivo el tumor, más proliferación. Coincide con la biología clásica del cáncer.

Ambos ejes se recuperan **sin haberlos declarado**: el pipeline los descubre por estadística.

## 18. NanoString y RT-qPCR (transferibilidad clínica)

- **NanoString nCounter**: tecnología que mide expresión de un panel pequeño de genes (docenas a cientos) directamente sobre tejido fijado en formalina (FFPE). Perfecta para clínica.
- **RT-qPCR (PCR cuantitativa)**: mide expresión gen a gen. Estándar en clínica para paneles muy pequeños.
- **Relevancia del TFM**: los 20 genes del panel mínimo son *medibles con NanoString o RT-qPCR*. Eso significa que el panel podría trasladarse a un test clínico. Diferencia clave respecto a firmas genómicas que requieren microarray/RNA-Seq (caro y lento).

## 19. Reproducibilidad

- **Definición fuerte**: cualquier persona con acceso al código y a los datos originales puede regenerar todas las cifras y figuras.
- **En este TFM**: pipeline con `random_state=42` en todos los pasos aleatorizados. Los CSV intermedios se almacenan y la app los lee. Todo el código está en GitHub.

## 20. Objetivo del TFM (una frase)

*"Framework transcriptómico reproducible que integra cohortes GEO de cáncer de pulmón mediante curación con LLM, meta-análisis por consenso y clasificación LASSO validada en LODO, con una firma génica interpretable que recupera el panel diagnóstico OMS y se transfiere a RNA-Seq (TCGA)."*

Si te preguntan "en una frase, ¿qué has hecho?", esa es tu respuesta.

---

# PARTE B · Guion diapositiva por diapositiva

**Formato de cada slide**:
- ⏱ Timing objetivo
- 🗣 Lo que dices (aprender la intención, no memorizar palabra por palabra)
- 💡 Puntos que enfatizar
- 🔗 Transición al siguiente

---

## SLIDE 1 · Portada (30 segundos)

⏱ **30 s**

🗣 **Guion**:
> "Buenos días. Muchas gracias por estar aquí. Mi nombre es Daniel Tapia Díez y presento hoy mi Trabajo Fin de Máster, titulado **Framework transcriptómico basado en la integración de modelos de lenguaje y aprendizaje automático para la identificación de biomarcadores en cáncer de pulmón**, tutorizado por Leonardo Dulcetti. El trabajo se materializa en un framework al que hemos llamado **data.lung**, construido sobre software libre —Python, scikit-learn, Streamlit, Llama sobre Groq y GitHub— y datos públicos de NCBI GEO y del portal cBioPortal para TCGA."

💡 Enfatizar:
- Tu nombre y el nombre del framework (data.lung).
- "Software libre y datos públicos" = reproducibilidad.

🔗 Transición: *"Empecemos por el porqué del trabajo."*

---

## SLIDE 2 · Problema y objetivo (45 segundos)

⏱ **45 s**

🗣 **Guion**:
> "El cáncer de pulmón sigue siendo la principal causa de muerte por cáncer en el mundo: **2,48 millones de casos anuales** y una supervivencia a 5 años **inferior al 20%**. Dentro del cáncer de pulmón no microcítico, distinguir adenocarcinoma de carcinoma escamoso es crítico, porque tratamientos como pemetrexed o bevacizumab están **contraindicados en escamoso** por riesgo de hemorragia mortal.
>
> Existen cientos de estudios de expresión génica públicos en GEO, pero integrarlos es difícil: plataformas heterogéneas, metadatos en texto libre, y firmas génicas publicadas que muchas veces **no replican** en cohortes independientes. Nuestro objetivo ha sido construir un framework reproducible que combine tres piezas: curación de metadatos con LLM, validación externa Leave-One-Dataset-Out y una firma consenso interpretable."

💡 Enfatizar:
- La cifra clínica (2,48 M y <20%) para dimensionar el problema.
- La palabra **contraindicados** — muestra que entiendes las consecuencias clínicas de un error.
- La palabra **no replican** — sitúa tu trabajo en el hueco real de la literatura.

🔗 Transición: *"Veamos cómo se ha construido el pipeline."*

---

## SLIDE 3 · Pipeline (90 segundos)

⏱ **1 min 30 s** — es una de las diapositivas densas, pero el diagrama vertical guía la explicación.

🗣 **Guion**:
> "El pipeline tiene nueve pasos que van del **dataset crudo** hasta la **firma interpretable**. Los pasos 1 y 2 hacen la ingesta y la limpieza técnica desde GEO. El paso 3 es el primero clave: usamos **Llama 3.3 de 70.000 millones de parámetros, servido con Groq**, para curar los metadatos clínicos. GEO tiene los metadatos en texto libre y las expresiones regulares se quedan cortas; el LLM entiende contexto. Alcanzamos **una tasa de éxito del 85,9%** en la asignación automática de etiquetas.
>
> Los pasos 4 a 6 son análisis diferencial cohorte a cohorte, calculando **d de Cohen** para cada gen. El paso 7 es la **validación externa LODO**: cada cohorte se retira una vez del entrenamiento y se usa como test independiente. Esto es más conservador que la validación cruzada estándar porque respeta la agrupación por cohorte.
>
> El paso 8 es el **consenso multi-cohorte**: un gen entra en la firma sólo si mantiene el mismo signo y una magnitud mínima en las tres cohortes. Y el paso 9 entrega la firma final y el panel mínimo.
>
> Un detalle metodológico importante: no aplicamos ComBat para corregir efecto lote. LODO no lo corrige, **lo mide**."

💡 Enfatizar:
- "Los pasos 1 y 2 hacen X"; "el paso 3 es el primero clave" — estructura el discurso.
- **85,9% de éxito LLM**: es una cifra citable.
- "LODO no corrige el efecto lote, lo mide" — frase muy potente, memorízala.

🔗 Transición: *"Con este pipeline, estos son los resultados."*

---

## SLIDE 4 · Firma y panel mínimo (60 segundos)

⏱ **1 min**

🗣 **Guion**:
> "Partimos de **11 cohortes GEO**. Ocho de ellas cumplieron los criterios de tamaño mínimo y balance de clases, sumando **1.157 muestras** curadas por el LLM. El análisis de consenso deja **1.174 genes validados** en las tres cohortes independientes.
>
> A partir de ese panel amplio, aplicamos LASSO para obtener un **panel mínimo de 20 genes**. Y aquí una cifra que me gusta destacar: el panel de 20 genes obtiene un AUC de **0,966**, prácticamente indistinguible del 0,970 de la firma completa de 1.174 genes. Se pierde muy poca información y se gana muchísima aplicabilidad clínica.
>
> En el top 5 del panel aparecen **DSG3, KRT5, CALML3, KRT6B y PKP1** — todos genes relacionados con desmosomas y queratinización, la biología del epitelio escamoso."

💡 Enfatizar:
- Los tres bignums (11, 8/11, 1.157) — decirlos despacio para que el tribunal los procese.
- 20 genes ≈ firma completa: **cheap and cheerful**, es la clave clínica.

🔗 Transición: *"¿Y estos genes son biológicamente creíbles? Miremos la validación externa."*

---

## SLIDE 5 · IHC y biología (90 segundos)

⏱ **1 min 30 s** — es probablemente la diapositiva más importante.

🗣 **Guion**:
> "La OMS publica desde 2015 un panel de marcadores inmunohistoquímicos para el diagnóstico rutinario de cáncer de pulmón: 12 marcadores de escamoso y 8 de adenocarcinoma. La firma que hemos obtenido, seleccionada de forma **puramente estadística sin conocer ese panel**, recupera **12 de los 12 marcadores escamosos y 6 de los 8 adenocarcinomatosos: 18 de 20 en total, un 90%**. Esa coincidencia entre selección estadística y práctica clínica es una validación externa muy fuerte.
>
> Además, analizando la estructura interna de la firma emergen dos ejes biológicos claros. El **primer eje** captura la pérdida alvéolo-capilar: la firma correlaciona negativamente con marcadores alveolares y capilares con **ρ media de -0,626**, llegando a **ρ = -0,858 en GSE31210, con p-valor del orden de 10 a la -66**. El **segundo eje** captura la actividad proliferativa: MKI67, TOP2A, CCNB1, BIRC5, AURKA — todos marcadores clásicos de proliferación tumoral.
>
> Es decir, la firma no es una caja negra. Captura la transición biológica del pulmón sano al tejido tumoral en dos ejes que un patólogo reconoce."

💡 Enfatizar:
- **18/20 sin haberlo declarado** — es tu argumento más fuerte.
- **ρ = -0,858, p ≈ 10⁻⁶⁶** — cifras impresionantes.
- Los ejes son **biológicamente correctos**, no artefactos.

🔗 Transición: *"En cuanto a rendimiento, hemos ido más allá del AUC básico."*

---

## SLIDE 6 · Rendimiento, recalibración y TCGA (90 segundos)

⏱ **1 min 30 s**

🗣 **Guion**:
> "En la tarea **tumor vs sano**, el LODO base da un AUC de 0,925 y una BalAcc de 0,772. Al aplicar **recalibración isotónica** —una técnica que ajusta las probabilidades por cohorte usando datos de validación—, el AUC sube a **0,953** y la BalAcc a **0,810**. La especificidad mejora especialmente, de 0,561 a 0,632, reduciendo falsos positivos.
>
> Comparamos también con Random Forest y SVM: LASSO obtiene AUC 0,925, Random Forest 0,933 y SVM 0,957. SVM gana ligeramente, pero elegimos LASSO como método principal por interpretabilidad — un panel de 20 genes con coeficientes explícitos por gen es mucho más útil clínicamente que un hiperplano de SVM.
>
> Finalmente, la validación en **RNA-Seq**: aplicamos el panel LASSO entrenado en microarray a **TCGA-LUAD y TCGA-LUSC**, 408 muestras en total. Ninguna muestra TCGA participó en la selección de genes ni en la calibración. El AUC resultante es **0,857, con intervalo de confianza bootstrap del 95% entre 0,812 y 0,899**. La firma se transfiere a una plataforma tecnológica distinta, lo que refuerza que la señal es biológica y no un artefacto de microarray."

💡 Enfatizar:
- **Recalibración**: BalAcc 0,772 → 0,810. La palabra "recalibración" impresiona.
- **AUC 0,857 en TCGA**: muéstralo como el sello de garantía externa.
- **"Ninguna muestra TCGA participó"** — evita cualquier duda sobre data leakage.

🔗 Transición: *"Y ahora, la parte más divertida. Voy a enseñaros la herramienta."*

---

## SLIDE 7 · data.lung · DEMO EN VIVO (2 minutos)

⏱ **2 min** — la parte más larga. Sal del PDF y muestra la app en el navegador.

🗣 **Guion antes de cambiar al navegador**:
> "Todo lo que os he contado se recoge en una herramienta interactiva multipágina que hemos llamado **data.lung**, hecha en Streamlit. Un buscador de gen en tiempo real, vistas por cohorte, y un asistente conversacional basado en Llama acotado a los resultados del trabajo — no responde nada que no esté en los datos.
>
> Voy a enseñároslo un momento."

**Cambia a la app** (Cmd+Tab).

🗣 **Durante la demo** (secuencia recomendada):

1. **Portada** (10 s): *"Esta es la portada."*
2. **Framework** (15 s): *"Aquí las cifras del framework. Todo se lee de CSV, ninguna cifra está en el código."*
3. **Resultados → Buscador de gen** (45 s):
   - Escribe `DSG3`. *"DSG3 aparece: es uno de los cinco genes principales del panel escamoso."*
   - Escribe `SFTPC`. *"SFTPC no aparece en el panel mínimo, aunque sí en la firma completa. Es un ejemplo de cómo LASSO reduce redundancia: hay otros marcadores alveolares que ya cubren esa señal."*
4. **Asistente** (30 s):
   - Pregunta: *"¿qué biomarcadores identifica el framework?"*
   - Espera respuesta y comenta: *"Fijaos que responde con los datos concretos del trabajo, y si le pregunto algo que no está en los resultados, me lo dice explícitamente."*

**Cambia de vuelta al PDF** (Cmd+Tab). *"Volvemos al PDF."*

💡 Enfatizar:
- **Reproducibilidad**: "todo se lee de CSV, nada hardcoded".
- **Rigor**: "el asistente sólo responde con datos del trabajo".

⚠️ **Antes de empezar la defensa**, tener corriendo:
```bash
streamlit run agentes/paso12_web_chatbot.py
```
Y la app abierta en el navegador, minimizada. Cmd+Tab para saltar.

🔗 Transición: *"Recapitulemos las conclusiones."*

---

## SLIDE 8 · Conclusiones (45 segundos)

⏱ **45 s** — lee los bullets, no los repitas literales.

🗣 **Guion**:
> "En resumen: un LLM cura los metadatos GEO con **85,9% de éxito**, escalando la integración multi-cohorte sin intervención manual. El consenso multi-cohorte más LODO produce una firma robusta de **1.174 genes con AUC 0,968** en subtipo. El panel mínimo de **20 genes es prácticamente equivalente** a la firma completa. La firma **recupera 18 de 20 marcadores IHC clínicos sin declararlos**. La recalibración isotónica mejora significativamente el rendimiento tumor-vs-sano. Y la firma **se transfiere a RNA-Seq** con AUC 0,857 en TCGA. Todo el framework es reproducible extremo a extremo, con interfaz web pública y asistente conversacional acotado."

💡 Enfatizar:
- Es la última oportunidad de meter las cifras clave. Dilas.

🔗 Transición: *"Y de aquí, ¿por dónde continuaría el trabajo?"*

---

## SLIDE 9 · Trabajo futuro y stack (45 segundos)

⏱ **45 s**

🗣 **Guion**:
> "El siguiente paso natural es una **validación clínica prospectiva** sobre biopsias frescas con NanoString o RT-qPCR — el panel de 20 genes ya está pensado para ser medible por esas técnicas. Otras líneas: ampliar a subtipos neuroendocrinos, sustituir el LLM externo por un modelo local por privacidad y coste, extender la metodología a otros tumores como mama, colon o hepatocarcinoma, y explorar firmas pronósticas con regresión de Cox sobre TCGA.
>
> Todo el trabajo está construido sobre software libre y datos públicos, y disponible en GitHub."

💡 Enfatizar:
- **Validación prospectiva** = camino hacia clínica.
- **Software libre + datos públicos + GitHub** = ética de investigación abierta.

🔗 Transición: *"Y con esto termino."*

---

## SLIDE 10 · Gracias (15 segundos)

⏱ **15 s**

🗣 **Guion**:
> "Muchas gracias por vuestra atención. Estoy a vuestra disposición para las preguntas que queráis plantearme."

💡 Sonríe, respira, silencio corto. Espera el turno de preguntas.

---

# PARTE C · Preguntas probables del tribunal + respuestas modelo

### Q1: "¿Por qué no ha usado ComBat para corregir efecto lote?"
**R**: "Porque en varias cohortes GEO el efecto lote está confundido con la variable de interés — hay estudios que sólo contienen tumores, o sólo un subtipo. En ese escenario ComBat podría borrar señal biológica genuina. Prefiero un enfoque más conservador: normalizar cada cohorte por separado y exigir consenso en varias cohortes independientes. LODO complementa esto midiendo el rendimiento en la peor situación posible: una cohorte totalmente no vista."

### Q2: "¿Cómo garantiza que no hay data leakage entre el descubrimiento de la firma y la validación TCGA?"
**R**: "Toda la selección de genes y la calibración se hizo exclusivamente sobre cohortes GEO en microarray. Las 408 muestras de TCGA se usaron sólo en la fase final, aplicando el modelo LASSO ya entrenado. Ninguna muestra TCGA participó en el ajuste ni en la selección de hiperparámetros."

### Q3: "El LLM tiene sesgos. ¿No los introduce en los datos?"
**R**: "Sí, es una preocupación real. Por eso el LLM se restringe a una tarea muy delimitada: leer una descripción de muestra y devolver una etiqueta canónica de grupo experimental. No participa en el análisis estadístico ni en la selección de genes. Además, la tasa de éxito del 85,9% se auditó manualmente sobre un subconjunto para descartar sesgos sistemáticos."

### Q4: "¿Por qué LASSO si SVM da un AUC mejor?"
**R**: "Porque un panel de 20 genes con coeficientes explícitos por gen es mucho más útil clínicamente que un hiperplano SVM. La diferencia de 3 puntos de AUC no compensa perder la interpretabilidad, sobre todo cuando el objetivo es un panel medible por NanoString o RT-qPCR."

### Q5: "¿La firma es prognóstica o sólo diagnóstica?"
**R**: "En este trabajo, únicamente diagnóstica: distinguir ADC de SQC y tumor de sano. La firma pronóstica requeriría integrar tiempos de supervivencia y regresión de Cox, y está señalada como línea de trabajo futuro sobre TCGA."

### Q6: "¿Qué pasa si un gen del panel no funciona por RT-qPCR en un laboratorio concreto?"
**R**: "El panel es redundante: dentro de los 20 genes hay grupos de marcadores del mismo linaje (varias queratinas y desmogleinas para escamoso; varios surfactantes para adenocarcinoma). Si uno falla técnicamente, otros del mismo grupo mantienen la señal."

### Q7: "¿Por qué usar cohortes tan antiguas de microarray si RNA-Seq es el estándar hoy?"
**R**: "Porque hay más cohortes de microarray con metadatos ricos para adenocarcinoma vs escamoso, y eso permite el consenso multi-cohorte. RNA-Seq entra como validación externa para confirmar transferibilidad, no como base del descubrimiento."

### Q8: "¿No hay riesgo de que el LLM 'invente' etiquetas?"
**R**: "El prompt está muy acotado: se le dan las descripciones de las muestras y una lista cerrada de etiquetas posibles, con instrucción explícita de devolver 'unknown' si no encaja. La tasa de éxito del 85,9% se calcula sobre auditoría manual, y el 14,1% restante se descarta, no se fuerza."

### Q9: "¿Qué le distingue de firmas comerciales como Pervenio Lung RS u Oncotype DX Lung?"
**R**: "Tres cosas: (i) validación LODO estricta en 3 cohortes totalmente independientes, no partición aleatoria; (ii) verificación cruzada contra el panel diagnóstico OMS, que Pervenio no reporta; (iii) reproducibilidad completa con código y datos públicos. Los ensayos comerciales son cajas negras protegidas por patente."

### Q10: "¿Cómo escalaría data.lung a otros tumores?"
**R**: "El framework es genérico: cambiar la fuente de datos (otras cohortes GEO y su equivalente TCGA), reentrenar la curación del LLM con las etiquetas del nuevo tumor, y ejecutar el mismo pipeline. La lógica de consenso, LODO y selección LASSO no depende del tejido."

---

# PARTE D · Checklist víspera de la defensa

- [ ] Portátil cargado + cargador
- [ ] Adaptador HDMI/USB-C si el aula lo requiere
- [ ] PDF de la presentación en local **y** en pen drive **y** en Drive/Dropbox
- [ ] Streamlit corriendo antes de entrar al aula: `streamlit run agentes/paso12_web_chatbot.py`
- [ ] Navegador con data.lung abierto y minimizado (Cmd+Tab probado)
- [ ] Copia impresa opcional (por si falla todo)
- [ ] Botella de agua
- [ ] Reloj visible (o el móvil en modo avión encima de la mesa)
- [ ] Respirar antes de empezar. 3 segundos de silencio son mucho menos largos de lo que crees.

---

**Suerte, Daniel. La memoria es rigurosa, la app funciona, los datos hablan por sí solos. Cuenta la historia con la tranquilidad de saber que todo está donde tiene que estar.**
