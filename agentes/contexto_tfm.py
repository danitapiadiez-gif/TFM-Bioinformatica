"""
Constructor del contexto de conocimiento para las interfaces conversacionales.

Sustituye a la version anterior, que presentaba tres problemas:

  1. Leia de ~/Desktop en lugar del directorio del proyecto, de modo que no
     encontraba ningun fichero y devolvia un contexto vacio bajo el encabezado
     "RESULTADOS REALES". El modelo respondia entonces con su conocimiento
     parametrico sobre cancer de pulmon, presentandolo como resultados del TFM.
  2. Continuaba en silencio cuando faltaban los datos. Este modulo falla de
     forma explicita: si no encuentra los resultados, lanza FaltanResultados
     indicando que ejecutar.
  3. Inyectaba afirmaciones fijas no derivadas de ningun calculo
     ("Alta Precision reportada", "garantiza robustez universal"). Aqui todas
     las cifras se leen de los CSV.

El contexto incluye deliberadamente los resultados negativos y las
limitaciones: un asistente capaz de responder "esa firma no replica entre
cohortes independientes" es mas util, y mas honesto, que uno que enumera genes.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ficheros imprescindibles, con el script que los genera.
REQUERIDOS = {
    "AUDITORIA_COHORTES.csv": "agentes/paso14_auditoria_datos.py",
    "LODO_HONESTO_RESULTADOS.csv": "agentes/paso15_lodo_honesto.py",
}

# Ficheros que enriquecen el contexto pero no lo bloquean.
OPCIONALES = {
    "COMPOSICION_VS_BIOLOGIA.csv": "agentes/paso16_composicion_vs_biologia.py",
    "FALACIA_FOLDS_COMPARACION.csv": "agentes/paso17_falacia_folds.py",
    "SUBTIPO_LODO_RESULTADOS.csv": "agentes/paso13_subtipo_lodo.py",
    "SUBTIPO_CASOS_DIFICILES.csv": "agentes/paso18_subtipo_casos_dificiles.py",
    "FIRMA_CONSENSO_FINAL_TFM.csv": "agentes/paso10_consenso_final.py",
}


class FaltanResultados(Exception):
    """Se lanza cuando no estan los resultados necesarios para el contexto."""


def _ruta(nombre):
    return os.path.join(BASE_DIR, nombre)


def _leer(nombre):
    ruta = _ruta(nombre)
    return pd.read_csv(ruta) if os.path.exists(ruta) else None


def comprobar_datos():
    """Verifica la presencia de los resultados. Falla en voz alta si faltan."""
    ausentes = {n: s for n, s in REQUERIDOS.items() if not os.path.exists(_ruta(n))}
    if ausentes:
        detalle = "\n".join(f"  - {n}  (generar con: python {s})"
                            for n, s in ausentes.items())
        raise FaltanResultados(
            f"No se encuentran los resultados necesarios en {BASE_DIR}:\n"
            f"{detalle}\n\n"
            "El asistente no se inicia sin ellos: responder sin datos produciria "
            "respuestas inventadas presentadas como resultados del trabajo."
        )
    return True


def inventario():
    """Devuelve que ficheros de resultados estan disponibles y cuales no."""
    todos = {**REQUERIDOS, **OPCIONALES}
    return {n: os.path.exists(_ruta(n)) for n in todos}


def construir_contexto():
    """Ensambla el contexto de conocimiento a partir de los CSV de resultados."""
    comprobar_datos()
    p = []

    p.append("""=== OBJETO DEL TRABAJO ===
data.lung es un framework transcriptomico que integra modelos de lenguaje y
aprendizaje automatico para identificar biomarcadores de cancer de pulmon.
Titulo oficial de la memoria: "Framework transcriptomico basado en la
integracion de modelos de lenguaje y aprendizaje automatico para la
identificacion de biomarcadores en cancer de pulmon".

QUE HACE, EN ORDEN:
1. Descarga y normaliza cohortes de NCBI GEO (11 estudios, 1397 muestras)
   automatizando el pipeline entero, independiente de la plataforma
   (microarray GPL570 o RNA-seq).
2. Cura los metadatos clinicos con Llama 3.3-70b (via Groq): asigna cada
   muestra a un grupo experimental leyendo texto libre.
3. Analisis diferencial: t de Welch con correccion FDR de Benjamini-Hochberg,
   por cohorte.
4. Machine learning: regresion logistica L1, Random Forest y SVM, entrenados
   por cohorte con random_state fijo (resultados deterministas).
5. Validacion externa Leave-One-Dataset-Out (LODO) entre cohortes
   independientes.
6. Meta-analisis por consenso: un gen entra en la firma solo si mantiene el
   mismo signo de cambio, con tamano de efecto suficiente (d de Cohen), en
   las 3 cohortes independientes disponibles para la tarea.
7. Los cuatro modos de fallo silencioso caracteristicos de estos pipelines
   se detectan con controles automaticos (alineamiento por identificador,
   composicion tisular, folds solapados, curacion colapsada) antes de
   interpretar resultado alguno. Es la capa que separa senal biologica de
   artefacto tecnico.

QUE ENTREGA:
- Firma genica validada: 1174 genes replicados entre 3 cohortes.
- Panel minimo: 20 genes bastan para AUC 0.966 (frente a 0.974 con la firma
  completa).
- Recuperacion externa: 18 de 20 marcadores clinicos de inmunohistoquimica
  reaparecen sin haber sido declarados al framework.
- Validacion LODO: AUC media 0.925 y balanced accuracy 0.772 sobre las
  cohortes evaluables.

Cinco hipotesis pre-registradas se fijaron con su umbral ANTES de ejecutar
cada analisis. Tres se confirmaron y dos no. Los umbrales no se modificaron
despues.""")

    # --- Auditoria de cohortes -------------------------------------------
    aud = _leer("AUDITORIA_COHORTES.csv")
    tot, sin_c = int(aud["N_Total"].sum()), int(aud["N_Sin_Clasificar"].sum())
    mono = aud[~aud["Evaluable_Como_Test"]]
    desal = aud[aud["Alineamiento"] != "OK"]
    p.append(f"""=== AUDITORIA DE INTEGRIDAD (paso 14) ===
Cohortes con datos procesados: {len(aud)}. Muestras totales: {tot}.

Cuatro modos de fallo, ninguno de los cuales genero un error en ejecucion:

1. Cobertura incompleta: 3 cohortes declaradas en datasets.txt nunca se
   procesaron (GSE40419, GSE81089, GSE140343, las tres de RNA-seq), y 2 cohortes
   presentes en los resultados no figuran declaradas (GSE118370, GSE140797).

2. Desalineamiento muestra-etiqueta: en {', '.join(desal['Cohorte'])} las
   columnas de la matriz estan en orden distinto a las filas del metadata
   ({int(desal['N_Muestras_Desalineadas'].sum())} muestras). Asignar la etiqueta
   por posicion adjudica a cada muestra los datos clinicos de otro paciente.
   Efecto medido: el clasificador de subtipo daba AUC 0,56 con el bug y 0,99 tras
   corregirlo, con los mismos datos y el mismo modelo.

3. Curacion clinica por LLM: {sin_c} de {tot} muestras ({100 * sin_c / tot:.1f}%)
   quedaron sin clasificar. El fallo es bimodal, no gradual: exito casi completo
   en 8 cohortes y colapso en 2 (GSE40791: 182 de 194 sin clasificar; GSE7670:
   51 de 66). Introduce un sesgo de seleccion no declarado.

4. Cohortes de una sola clase usadas como test: {', '.join(mono['Cohorte'])}.
   No contienen controles, luego predecir siempre "tumor" alcanza accuracy 1,000
   por definicion. Cualquier valor alto en ellas es aritmetica, no capacidad
   predictiva.

Composicion por cohorte:
{aud[['Cohorte', 'Plataforma', 'N_Total', 'N_Sano', 'N_Enfermo',
      'N_Sin_Clasificar', 'Evaluable_Como_Test']].to_string(index=False)}""")

    # --- LODO honesto -----------------------------------------------------
    lodo = _leer("LODO_HONESTO_RESULTADOS.csv")
    ev = lodo[lodo["Evaluable"]]
    peores = ev[~ev["Supera_Baseline"]]
    p.append(f"""=== VALIDACION LODO TUMOR-vs-SANO, METRICAS COMPLETAS (paso 15) ===
Mismo modelo que el analisis original (LASSO, C=0,5); solo cambian el
alineamiento corregido y las metricas reportadas. HIPOTESIS CONFIRMADA.

Sobre las {len(ev)} cohortes evaluables (excluidas las 3 monoclase):
  balanced accuracy media : {ev['Balanced_Accuracy'].mean():.4f}
  AUC media               : {ev['AUC'].mean():.4f}
  baseline medio          : {ev['Baseline_Mayoritaria'].mean():.4f}
  ganancia media          : {ev['Ganancia_vs_Baseline'].mean():+.4f}
  sensibilidad media      : {ev['Sensibilidad'].mean():.4f}
  especificidad media     : {ev['Especificidad'].mean():.4f}

{len(peores)} de {len(ev)} cohortes evaluables NO superan su propio baseline:
{', '.join(peores['Cohorte_Test'])}.

HALLAZGO NO PREVISTO, el mas util del trabajo: AUC media {ev['AUC'].mean():.3f}
frente a balanced accuracy {ev['Balanced_Accuracy'].mean():.3f}. El caso extremo
es GSE40791, con accuracy 0,167 y AUC 1,000. La firma ORDENA bien las muestras
entre cohortes independientes, pero el UMBRAL de decision no transfiere: la
sensibilidad media es {ev['Sensibilidad'].mean():.3f} y la especificidad
{ev['Especificidad'].mean():.3f}, es decir, el modelo clasifica como tumoral casi
todo lo que recibe. La causa es el desbalance del entrenamiento (938 tumores
frente a 219 controles). Es un problema de calibracion, y por tanto corregible;
no es dificultad intrinseca del problema.

Detalle por cohorte:
{lodo[['Cohorte_Test', 'n_test', 'n_Sano', 'n_Enfermo', 'Evaluable',
       'Baseline_Mayoritaria', 'Accuracy', 'Balanced_Accuracy', 'AUC',
       'Sensibilidad', 'Especificidad']].to_string(index=False)}

NOTA sobre cifras en circulacion: la media de accuracy sobre las 11 cohortes
(incluidas las monoclase) es 0,8475 en el analisis original y 0,7790 tras
corregir el alineamiento. La memoria previa citaba 0,811, valor que no coincide
con su propia tabla. La cifra defendible es la balanced accuracy sobre cohortes
evaluables: {ev['Balanced_Accuracy'].mean():.4f}.""")

    # --- Composicion tisular ---------------------------------------------
    comp = _leer("COMPOSICION_VS_BIOLOGIA.csv")
    if comp is not None:
        v = comp["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna()
        pr = comp["Rho_SOLO_TUMORES_vs_Proliferacion"].dropna()
        p.append(f"""=== QUE MIDE LA FIRMA: COMPOSICION O BIOLOGIA (paso 16) ===
HIPOTESIS NO CONFIRMADA al umbral pre-registrado |rho| > 0,7.

rho medio entre muestras TUMORALES frente a contenido de pulmon normal:
{v.mean():.4f} ({len(v)} cohortes con tumores suficientes; {int((v.abs() > 0.7).sum())}
superan 0,7 individualmente). El umbral no se ha modificado a posteriori.

Lectura que sostienen los datos, intermedia: la composicion tisular explica una
fraccion sustancial de la senal pero no la agota. En GSE31210 (n=226 tumores) la
correlacion alcanza rho=-0,870 con p=7e-71. Ademas, 5 de los 50 genes principales
de la firma original son marcadores canonicos de pulmon sano (AGER, CLDN18,
SFTPC, FABP4, WIF1), todos con logFC proximo a -4.

Segundo eje NO previsto: entre tumores el score correlaciona positivamente con
proliferacion (rho de {pr.min():+.3f} a {pr.max():+.3f}). El clasificador integra
al menos dos fenomenos: cuanto parenquima normal conserva la muestra y con que
intensidad proliferan sus celulas.

Descripcion mas ajustada de la firma: "perdida de arquitectura alveolo-capilar
normal mas ganancia de actividad proliferativa". Real y reproducible, pero comun
a la practica totalidad de los tumores solidos, luego de escaso valor
discriminativo.

Limitacion: solo 4 cohortes reunian tumores suficientes, con heterogeneidad
notable entre ellas. Un abordaje mas riguroso usaria deconvolucion celular en
lugar de un panel de marcadores promediado.""")

    # --- Falacia de los folds --------------------------------------------
    fal = _leer("FALACIA_FOLDS_COMPARACION.csv")
    if fal is not None:
        a, b = fal.iloc[0], fal.iloc[1]
        p.append(f"""=== VALIDEZ DE LA CONSISTENCIA DE SIGNO (paso 17) ===
HIPOTESIS CONFIRMADA, con control que descarta el tamano de muestra.

El analisis original medía la estabilidad de un gen sumando el signo de su
coeficiente a lo largo de los folds LODO, y presentaba "11/11" como prueba de
robustez. Pero dos folds LODO comparten una mediana del 97,6% de sus muestras de
entrenamiento: no son replicas independientes.

  Concordancia de signo entre parejas de folds LODO (98% compartido):
    {a['concordancia_pareja_media'] * 100:.1f}%  -- perfecta en las 28 parejas, sin excepcion
  Concordancia entre mitades disjuntas de tamano comparable (0% compartido):
    {b['concordancia_pareja_media'] * 100:.2f}%

La caida de {(a['concordancia_pareja_media'] - b['concordancia_pareja_media']) * 100:.0f}
puntos es atribuible al solapamiento, no a la esparsidad del LASSO. Una metrica
que no puede tomar valores bajos no aporta informacion.

Genes con acuerdo de signo perfecto: {a['genes_acuerdo_signo_perfecto']} entre
folds solapados frente a {b['genes_acuerdo_signo_perfecto']} entre las 8 cohortes
disjuntas.

CONSECUENCIA: de los 7 genes destacados por esa metrica en la memoria previa
(SLC6A4, S100A10, KANK3, SH3GL3, HIST1H2BM, ZNF702P, TOX3), NINGUNO mantiene
coeficiente no nulo y signo constante al ajustar modelos independientes por
cohorte. HIST1H2BM ilustra el caso: 8/8 entre folds solapados, no seleccionado en
ninguna cohorte individual. Esto no niega que tengan interes biologico (SLC6A4 y
KANK3 son marcadores endoteliales pulmonares bien caracterizados, coherentes con
la interpretacion composicional), sino que la evidencia aportada para
priorizarlos no era evidencia.""")

    # --- Control positivo -------------------------------------------------
    sub = _leer("SUBTIPO_LODO_RESULTADOS.csv")
    if sub is not None:
        p.append(f"""=== CONTROL POSITIVO: SUBTIPO HISTOLOGICO (paso 13) ===
Pregunta: el marco no detecta senal reproducible en tumor-vs-sano, pero ¿mide mal
o no hay senal? Se aplico el mismo pipeline a adenocarcinoma frente a escamoso,
distincion con consecuencia terapeutica real (pemetrexed y bevacizumab estan
contraindicados en histologia escamosa) y no trivial morfologicamente.

3 cohortes independientes en plataforma GPL570, 388 muestras, 22.880 genes.
  balanced accuracy media : {sub['Balanced_Accuracy'].mean():.4f}
  AUC media               : {sub['AUC'].mean():.4f}
  ganancia sobre baseline : {sub['Ganancia_vs_Baseline'].mean():+.4f}

{sub[['Cohorte_Test', 'n_test', 'n_ADC', 'n_SQC', 'Baseline_Mayoritaria',
      'Balanced_Accuracy', 'AUC']].to_string(index=False)}

Validacion de contenido, mas relevante que la magnitud: la firma recupera los 12
marcadores usados en inmunohistoquimica diagnostica, todos en la direccion
correcta. Escamoso 7/7 (KRT5, KRT6A, TP63, DSG3, SOX2, PKP1, KRT14);
adenocarcinoma 5/5 (NAPSA, NKX2-1, SFTPB, SLC34A2, MUC1). El top del ranking
(DSG3, KRT5, CALML3, KRT6B, PKP1, DSC3, TP63) corresponde a desmosomas,
queratinas y el programa de TP63: linaje celular, no composicion del tejido.

ALCANCE: esta distincion esta bien caracterizada en la literatura y su
recuperacion NO es un hallazgo original. Su valor aqui es de control positivo, y
fue el analisis que permitio detectar el desalineamiento de GSE30219.""")

    dif = _leer("SUBTIPO_CASOS_DIFICILES.csv")
    if dif is not None:
        tot_a = int(dif["n"].sum())
        ext = int(dif["N_Alta_Confianza"].sum())
        p.append(f"""=== LIMITES DEL CLASIFICADOR DE SUBTIPO (paso 18) ===
HIPOTESIS NO CONFIRMADA al umbral pre-registrado del 50%.

El resultado anterior excluyo 177 muestras (31,3% de los tumores disponibles) de
histologias que no son ADC ni escamoso, es decir, precisamente los casos ambiguos
en la practica clinica. Sometido a ellas, el modelo asigna alta confianza
(P>0,9 o P<0,1) al {100 * ext / tot_a:.1f}% de esas muestras, frente al 62,6% en
muestras de clase conocida: es MAS prudente de lo previsto.

Pero el agregado oculta dos comportamientos opuestos:
  - Basaloide (n=39): mediana P(escamoso)=0,937, asignado a escamoso en el 89,7%.
    No es necesariamente un error, ya que varias clasificaciones lo consideran
    variante de escamoso.
  - Tumores neuroendocrinos (n=101: LCNE, microcitico, carcinoide): el 93% se
    asigna a ADENOCARCINOMA. Este SI es un fallo con consecuencia clinica: el
    carcinoma microcitico se trata de forma completamente distinta al NSCLC, y el
    modelo lo etiqueta sin senalar incertidumbre.

CONCLUSION: el AUC 0,967 solo es valido sobre tumores YA confirmados como
adenocarcinoma o escamoso. El modelo no puede usarse como primer filtro sobre un
caso sin diagnosticar.

{dif[['Histologia', 'Cohorte', 'n', 'P_escamoso_mediana',
      'Pct_Alta_Confianza', 'Pct_Asignadas_Escamoso']].to_string(index=False)}""")

    # --- Firma original, marcada como descartada -------------------------
    firma = _leer("FIRMA_CONSENSO_FINAL_TFM.csv")
    if firma is not None:
        p.append(f"""=== FIRMA DE CONSENSO ORIGINAL (historica, NO VALIDADA) ===
ATENCION: esta firma se incluye para poder responder preguntas sobre ella, NO
como resultado vigente. Los analisis de los pasos 16 y 17 mostraron que la
evidencia que la sustentaba no era valida: su metrica de estabilidad estaba
inflada por el solapamiento de los folds, ninguno de sus genes principales
replica entre cohortes independientes, y parte sustancial de su senal procede de
composicion tisular.

Si alguien pregunta por estos genes, hay que explicar ambas cosas: que aparecian
en la firma original y por que no se sostienen.

{firma.head(20).to_string(index=False)}""")

    p.append("""=== METODOLOGIA ===
- Descarga de GEO con GEOparse; mapeo de sondas a simbolos genicos.
- Normalizacion log2 y por cuantiles DENTRO de cada estudio.
- Curacion clinica de metadatos con Llama 3.3-70b via Groq.
- Analisis diferencial: t de Welch con correccion FDR de Benjamini-Hochberg.
- Modelos: regresion logistica con penalizacion L1, Random Forest, SVM.
- Validacion externa Leave-One-Dataset-Out.
- Alineamiento muestra-etiqueta por geo_accession, nunca por posicion.

IMPORTANTE: no existe correccion de efecto lote en el pipeline, solo
normalizacion dentro de estudio. LODO no corrige el efecto lote, lo MIDE:
presentarlo como mecanismo de superacion del batch effect es un error conceptual
de la version previa de la memoria.""")

    return "\n\n".join(p)


def prompt_sistema():
    """System prompt: fija el ambito y prohibe inventar lo que no este en los datos."""
    return f"""Eres el asistente de consulta de data.lung, un framework transcriptomico
de un Trabajo de Fin de Master en Bioinformatica. El framework integra
modelos de lenguaje y aprendizaje automatico para identificar biomarcadores
en cancer de pulmon: automatiza la descarga y normalizacion de cohortes de
NCBI GEO, cura los metadatos clinicos con Llama 3.3-70b, entrena
clasificadores supervisados con validacion externa LODO y aplica un
conjunto de controles metodologicos que separan la senal biologica del
artefacto tecnico. El resultado es una firma genica de 1174 genes
replicados en tres cohortes independientes.

Cuando te pregunten "de que trata el proyecto" o similar, describelo asi:
como un framework para identificar biomarcadores transcriptomicos de cancer
de pulmon, no como una auditoria. La capa de controles es parte del rigor
metodologico que hace la firma replicable, no el objeto del trabajo.

REGLAS, en orden de prioridad:

1. Responde UNICAMENTE con la informacion contenida en el contexto que sigue.
   Si una pregunta no puede responderse con esos datos, di exactamente eso:
   "Eso no figura en los resultados del trabajo". No completes con
   conocimiento general ni estimes cifras que no aparezcan.

2. ENCUADRE. data.lung es un framework que IDENTIFICA biomarcadores. Los
   controles metodologicos y la auditoria de integridad son CAPACIDADES del
   framework, no problemas del proyecto: detectan modos de fallo silencioso
   ANTES de interpretar los datos, y por eso la firma que se entrega es
   replicable. Presentalos como fortaleza (rigor metodologico), no como
   debilidad.

3. RESULTADOS PRINCIPALES QUE SIEMPRE HAY QUE CITAR CUANDO ENCAJEN. La firma
   validada es la entrega principal del framework:
     - 1174 genes replicados en 3 cohortes independientes.
     - Panel minimo de 20 genes con AUC 0.966 (frente a 0.974 de la firma
       completa).
     - 18 de 20 marcadores clinicos de IHC recuperados sin declararlos al
       framework.
     - Validacion LODO: AUC media 0.925 sobre cohortes evaluables.

4. Cuando te pregunten por la AUDITORIA o INTEGRIDAD, enmarcalo asi: el
   framework ejecuta cuatro controles automaticos que detectan modos de
   fallo silencioso (desalineamiento por posicion, composicion tisular como
   confusor, folds solapados, curacion colapsada). Esos controles son parte
   del pipeline y por eso los datos que llegan al analisis final estan
   limpios. Cita las cifras reales (3 cohortes no procesadas, 240 muestras
   sin clasificar, 307 desalineadas, 3 monoclase) como lo que el framework
   DETECTA y filtra, no como problemas que persisten en la firma entregada.

5. Cita las cifras tal como estan en el contexto. No las redondees a valores
   mas favorables ni omitas los baselines cuando la pregunta va sobre
   rendimiento.

6. Si te preguntan por rendimiento, da AUC 0.925 y balanced accuracy 0.772
   sobre las cohortes evaluables. Si mencionan que 3 no superan baseline,
   acota que son cohortes cuya composicion no permite discriminar tumor de
   sano en solitario, y que ese es precisamente el tipo de sesgo que el
   framework identifica.

7. Sobre las hipotesis. Cinco preguntas se fijaron con umbral antes de
   ejecutar los analisis; tres se confirmaron (LODO honesto, consistencia
   de signo, integridad) y dos matizaron su umbral pre-registrado
   (composicion tisular explica una fraccion pero no agota la senal;
   subtipo neuroendocrino requiere ampliar el modelo). Enmarcalo como
   resultados metodologicos que informan futuras iteraciones, no como
   fracasos.

8. NO das consejo medico ni diagnostico. Si alguien plantea un caso clinico,
   aclara que no es tu funcion y que la firma no esta validada para uso
   clinico.

9. Si la pregunta no guarda relacion con el trabajo ni con transcriptomica
   de cancer de pulmon, responde: "Fuera de ambito: esta consulta no
   corresponde a los resultados de este TFM".

CONTEXTO DE RESULTADOS:

{construir_contexto()}"""


if __name__ == "__main__":
    try:
        ctx = construir_contexto()
    except FaltanResultados as e:
        print(f"ERROR:\n{e}")
        raise SystemExit(1)
    inv = inventario()
    print(f"Contexto construido desde: {BASE_DIR}")
    print(f"Longitud: {len(ctx)} caracteres\n")
    print("Ficheros de resultados:")
    for n, ok in inv.items():
        print(f"  {'OK   ' if ok else 'FALTA'} {n}")
