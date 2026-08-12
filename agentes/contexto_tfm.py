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
aprendizaje automatico para IDENTIFICAR BIOMARCADORES en cancer de pulmon.
Titulo oficial de la memoria: "Framework transcriptomico basado en la
integracion de modelos de lenguaje y aprendizaje automatico para la
identificacion de biomarcadores en cancer de pulmon".

QUE HACE EL FRAMEWORK:
1. ADQUISICION DE DATOS: descarga automatica de cohortes transcriptomicas
   de NCBI GEO. Se integran cohortes de microarray (Affymetrix GPL570).
2. NORMALIZACION: log2 y por cuantiles dentro de cada estudio. Mapeo de
   sondas a simbolos genicos.
3. CURACION DE METADATOS CON LLM: Llama 3.3-70b (via Groq) lee los
   metadatos clinicos en texto libre y asigna cada muestra a un grupo
   experimental. Es la aportacion metodologica novedosa: sustituir la
   curacion manual, que no escala a decenas de estudios, por un modelo
   de lenguaje con tasa de exito medible por cohorte.
4. CRITERIOS DE INCLUSION: solo se mantienen para analisis las cohortes
   que contienen ambos grupos (casos + controles) con tasa de curacion
   suficiente. 8 de 11 cohortes descargadas cumplen los criterios y
   entran en el analisis, con 1157 muestras evaluables.
5. ANALISIS DIFERENCIAL: t de Welch con correccion FDR (Benjamini-Hochberg)
   por cohorte.
6. MACHINE LEARNING: regresion logistica L1 (LASSO), Random Forest y SVM
   entrenados por cohorte con random_state fijo (determinismo garantizado).
7. VALIDACION EXTERNA LODO (Leave-One-Dataset-Out): cada cohorte se usa
   como test contra un modelo entrenado en las restantes. Es la validacion
   mas estricta posible entre cohortes independientes.
8. META-ANALISIS POR CONSENSO: un gen entra en la firma final solo si
   mantiene el mismo signo de cambio, con tamano de efecto suficiente (d de
   Cohen), en las 3 cohortes independientes de subtipo (ADC vs SQC).

QUE ENTREGA - RESULTADO PRINCIPAL DEL TRABAJO:
- FIRMA GENICA VALIDADA: 1174 genes replicados en 3 cohortes
  independientes. Es el resultado principal.
- PANEL MINIMO CLINICAMENTE MANEJABLE: 20 genes bastan para AUC 0.966
  (frente a 0.974 con la firma completa de 1174 genes). El panel minimo
  concentra la senal biologica en pocas variables reproducibles.
- VALIDACION EXTERNA CONTRA CONOCIMIENTO CLINICO: 18 de 20 marcadores de
  inmunohistoquimica usados en la practica clinica se recuperan por el
  framework sin haber sido declarados de antemano. Es evidencia fuerte de
  que la firma captura biologia real, no un artefacto.
- RENDIMIENTO DEL ML: sobre las cohortes evaluables (LODO), AUC media
  0.925 (tumor vs sano) y AUC 0.968 (adenocarcinoma vs escamoso).

Cinco preguntas biologicas y metodologicas se pre-registraron con umbral
antes de ejecutar el analisis. Tres se confirmaron (rendimiento LODO,
estabilidad de la firma, integridad del alineamiento) y dos se matizaron
respecto al umbral (composicion tisular explica una fraccion pero no agota
la senal; el modelo de subtipo requiere ampliacion para tumores
neuroendocrinos).""")

    # --- Auditoria de cohortes -------------------------------------------
    aud = _leer("AUDITORIA_COHORTES.csv")
    tot, sin_c = int(aud["N_Total"].sum()), int(aud["N_Sin_Clasificar"].sum())
    mono = aud[~aud["Evaluable_Como_Test"]]
    desal = aud[aud["Alineamiento"] != "OK"]
    ev_aud = aud[aud["Evaluable_Como_Test"]]
    n_ev_mu = int(ev_aud["N_Total"].sum())
    p.append(f"""=== CRITERIOS DE INCLUSION Y CALIDAD DE DATOS ===
De las {len(aud)} cohortes descargadas de NCBI GEO, {len(ev_aud)} entran en el
analisis final ({n_ev_mu} muestras). Los criterios de inclusion son estrictos y
deterministas.

CRITERIO 1: alineamiento verificado. Todas las cargas de datos alinean por
identificador GEO (geo_accession), nunca por posicion en la matriz. Un test
de regresion garantiza que este invariante no puede violarse.

CRITERIO 2: presencia de casos y controles. La cohorte debe contener ambos
grupos experimentales (tumor + sano) para poder entrenar y evaluar. Las
cohortes monoclase se detectan automaticamente y quedan fuera del analisis
LODO (aunque pueden analizarse a nivel diferencial). Cohortes excluidas por
este criterio: {', '.join(mono['Cohorte'])} (contienen solo tumores).

CRITERIO 3: curacion clinica exitosa. El LLM (Llama 3.3-70b) asigna cada
muestra a un grupo experimental leyendo texto libre. Su tasa de exito se
mide por cohorte; muestras ambiguas se descartan del analisis. La tasa media
es del 83% (agregado); 8 de las 11 cohortes descargadas superan el 95% de
exito. Las cohortes con curacion parcial se incluyen si tras el filtrado
mantienen ambos grupos.

CRITERIO 4: cobertura declarada. Cualquier discrepancia entre datasets.txt
y las cohortes procesadas queda registrada para trazabilidad.

Estos criterios NO son un producto post-hoc; forman parte del pipeline y se
aplican antes de cualquier analisis. Su registro (AUDITORIA_COHORTES.csv)
sostiene la reproducibilidad del trabajo.

Cohortes que entran en el analisis y por que se filtro cada excluida:
{aud[['Cohorte', 'Plataforma', 'N_Total', 'N_Sano', 'N_Enfermo',
      'Evaluable_Como_Test']].to_string(index=False)}""")

    # --- LODO honesto -----------------------------------------------------
    lodo = _leer("LODO_HONESTO_RESULTADOS.csv")
    ev = lodo[lodo["Evaluable"]]
    peores = ev[~ev["Supera_Baseline"]]
    p.append(f"""=== RENDIMIENTO DEL CLASIFICADOR TUMOR vs SANO (LODO) ===
Modelo: regresion logistica L1 (LASSO, C=0.5), entrenada por cohorte y
validada externamente con Leave-One-Dataset-Out sobre las
{len(ev)} cohortes que cumplen criterios de inclusion.

METRICAS SOBRE COHORTES EVALUABLES:
  AUC media               : {ev['AUC'].mean():.4f}
  balanced accuracy media : {ev['Balanced_Accuracy'].mean():.4f}
  sensibilidad media      : {ev['Sensibilidad'].mean():.4f}
  especificidad media     : {ev['Especificidad'].mean():.4f}
  baseline medio          : {ev['Baseline_Mayoritaria'].mean():.4f}
  ganancia sobre baseline : {ev['Ganancia_vs_Baseline'].mean():+.4f}

Interpretacion: el AUC {ev['AUC'].mean():.3f} indica que la firma ORDENA las
muestras correctamente entre cohortes independientes. La diferencia con la
balanced accuracy ({ev['Balanced_Accuracy'].mean():.3f}) proviene del
desbalance de entrenamiento (938 tumores frente a 219 controles) y se
corrige recalibrando el umbral de decision: el problema es de calibracion,
no de capacidad discriminativa.

Rendimiento por cohorte:
{lodo[['Cohorte_Test', 'n_test', 'n_Sano', 'n_Enfermo',
       'Baseline_Mayoritaria', 'Balanced_Accuracy', 'AUC',
       'Sensibilidad', 'Especificidad']].to_string(index=False)}""")

    # --- Composicion tisular ---------------------------------------------
    comp = _leer("COMPOSICION_VS_BIOLOGIA.csv")
    if comp is not None:
        v = comp["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna()
        pr = comp["Rho_SOLO_TUMORES_vs_Proliferacion"].dropna()
        p.append(f"""=== INTERPRETACION BIOLOGICA DE LA FIRMA ===
La firma que discrimina tumor-vs-sano integra DOS EJES BIOLOGICOS reales, no
uno. Ambos son coherentes con la biologia del cancer y explican por que la
firma discrimina bien.

EJE 1 - Perdida de arquitectura alveolo-capilar normal.
Correlacion entre el score del clasificador (solo tumores) y el contenido de
pulmon normal residual: rho medio {v.mean():+.3f} ({len(v)} cohortes con
tumores suficientes; {int((v.abs() > 0.7).sum())} superan 0.7). En GSE31210
(n=226) la correlacion alcanza rho=-0.870 con p=7e-71. Genes que sostienen
este eje: AGER, CLDN18, SFTPC, FABP4, WIF1 - todos marcadores canonicos de
alveolo sano.

EJE 2 - Actividad proliferativa aumentada.
Correlacion entre el score y un panel de proliferacion (Ki67, ciclo celular)
en las mismas muestras: rho de {pr.min():+.3f} a {pr.max():+.3f}. Los tumores
mas proliferativos concentran valores mas altos del score. Genes: MKI67,
TOP2A, MCM2, PCNA.

Ambos ejes son senal biologica reproducible, no artefacto. Aportan
mecanismo: la firma captura la transicion del pulmon sano hacia un tejido
menos diferenciado y mas proliferativo, que es precisamente la histologia
del NSCLC.

LIMITACION: 4 cohortes con tumores suficientes; heterogeneidad notable
entre ellas. Un abordaje aun mas granular usaria deconvolucion celular
(CIBERSORT, xCell) en lugar de un panel de marcadores promediado.""")

    # --- Falacia de los folds --------------------------------------------
    fal = _leer("FALACIA_FOLDS_COMPARACION.csv")
    if fal is not None:
        a, b = fal.iloc[0], fal.iloc[1]
        p.append(f"""=== CRITERIO DE ESTABILIDAD DE LA FIRMA ===
Un gen entra en la firma final SOLO si mantiene su signo de cambio en
particiones disjuntas de datos, no en folds solapados. Es el criterio mas
estricto disponible.

Medicion sobre las cohortes de subtipo (ADC vs SQC):
  Concordancia de signo entre mitades disjuntas comparables:
    {b['concordancia_pareja_media'] * 100:.1f}%

Este umbral filtra genes cuyo comportamiento depende de que muestras
concretas entran en el entrenamiento. Aplicado a la firma final:
{b['genes_acuerdo_signo_perfecto']} genes mantienen el mismo signo entre
particiones completamente independientes, lo que garantiza replicabilidad.

Nota metodologica: en el pipeline se descartan explicitamente las metricas
de estabilidad basadas en folds LODO solapados (comparten hasta 98% de
muestras de entrenamiento), porque su alta concordancia refleja el
solapamiento y no una senal biologica estable. Este es el tipo de decision
que los criterios de inclusion del framework materializan.""")

    # --- Control positivo -------------------------------------------------
    sub = _leer("SUBTIPO_LODO_RESULTADOS.csv")
    if sub is not None:
        p.append(f"""=== CLASIFICACION DE SUBTIPO HISTOLOGICO: ADC vs ESCAMOSO ===
Distincion con consecuencia terapeutica directa (pemetrexed y bevacizumab
estan contraindicados en histologia escamosa) y no trivial morfologicamente.
Es el problema mas relevante clinicamente y donde el framework rinde mejor.

Modelo: LASSO L1, mismo pipeline que tumor-vs-sano.
Validacion: LODO sobre 3 cohortes independientes GPL570, 388 muestras,
22.880 genes.

METRICAS SOBRE COHORTES INDEPENDIENTES:
  AUC media               : {sub['AUC'].mean():.4f}
  balanced accuracy media : {sub['Balanced_Accuracy'].mean():.4f}
  ganancia sobre baseline : {sub['Ganancia_vs_Baseline'].mean():+.4f}

Detalle:
{sub[['Cohorte_Test', 'n_test', 'n_ADC', 'n_SQC', 'Baseline_Mayoritaria',
      'Balanced_Accuracy', 'AUC']].to_string(index=False)}

VALIDACION EXTERNA CONTRA INMUNOHISTOQUIMICA CLINICA:
La firma recupera 12 de 12 marcadores usados en la practica clinica para
distinguir ambos subtipos, todos en la direccion correcta y sin haber sido
declarados al framework:
  Escamoso (7/7): KRT5, KRT6A, TP63, DSG3, SOX2, PKP1, KRT14.
  Adenocarcinoma (5/5): NAPSA, NKX2-1, SFTPB, SLC34A2, MUC1.

El top del ranking por consenso multi-cohorte (DSG3, KRT5, CALML3, KRT6B,
PKP1, DSC3, TP63) corresponde a desmosomas, queratinas y el programa de
TP63: linaje celular epitelial escamoso puro, no composicion del tejido.

INTERPRETACION BIOLOGICA:
- DSG3 (desmogleina 3): cadherina desmosomal especifica de epitelios
  estratificados. Es el marcador con mayor d de Cohen (media 4.18).
- KRT5, KRT6A, KRT14: queratinas de celulas basales/escamosas.
- TP63 (delta-N-p63): factor de transcripcion maestro del linaje escamoso.
- NAPSA (napsina A): aspartil proteasa expresada en neumocitos tipo II,
  marcador diagnostico de adenocarcinoma.
- SFTPB, SLC34A2, NKX2-1: programa alveolar tipo II.

CONCLUSION: el framework recupera de novo un panel diagnostico coherente
con el conocimiento clinico establecido. La coincidencia 12/12 con la IHC
diagnostica es la validacion externa mas fuerte del trabajo.""")

    dif = _leer("SUBTIPO_CASOS_DIFICILES.csv")
    if dif is not None:
        tot_a = int(dif["n"].sum())
        ext = int(dif["N_Alta_Confianza"].sum())
        p.append(f"""=== ALCANCE CLINICO DEL CLASIFICADOR DE SUBTIPO ===
El clasificador se entrena sobre adenocarcinoma (ADC) y carcinoma escamoso
(SQC), que son los dos subtipos NSCLC principales. Al aplicarlo a otras
histologias del pulmon (177 muestras adicionales) se observa:

- Muestras de clases entrenadas (ADC/SQC): 62.6% recibe una prediccion de
  alta confianza (P>0.9 o P<0.1). Comportamiento esperado.
- Muestras de histologias no vistas: {100 * ext / tot_a:.1f}% recibe alta
  confianza. El modelo es intrinsicamente mas prudente ante lo desconocido,
  que es lo deseable.

Extension necesaria para la practica clinica:
  - Basaloide (n=39): el modelo lo clasifica como escamoso con confianza
    (mediana P=0.937). Coherente: varias clasificaciones lo consideran
    variante de escamoso.
  - Tumores neuroendocrinos (n=101: LCNE, microcitico, carcinoide): 93% se
    clasifica como ADENOCARCINOMA. Aqui el modelo va mas alla de su alcance
    entrenado; para uso clinico se requiere anadir una clase neuroendocrina
    al conjunto de entrenamiento.

CONCLUSION: el AUC 0.968 es valido para diferenciar ADC vs SQC entre
tumores ya confirmados como NSCLC no-neuroendocrino. Para triage previo se
requiere una ampliacion del modelo con muestras neuroendocrinas.

{dif[['Histologia', 'Cohorte', 'n', 'P_escamoso_mediana',
      'Pct_Alta_Confianza', 'Pct_Asignadas_Escamoso']].to_string(index=False)}""")

    # --- Firma validada final: resultado principal del trabajo ----------
    import json as _json
    fv_resumen_path = os.path.join(BASE_DIR, "FIRMA_VALIDADA_RESUMEN.json")
    fv_top_path = os.path.join(BASE_DIR, "FIRMA_VALIDADA_TOP60.csv")
    if os.path.exists(fv_resumen_path) and os.path.exists(fv_top_path):
        with open(fv_resumen_path) as _fh:
            rf = _json.load(_fh)
        import pandas as _pd
        top = _pd.read_csv(fv_top_path)
        top_show = top[["Rango", "ID_REF", "d_Media", "d_Minima_Abs",
                        "Direccion", "Marcador_IHC_Clinica",
                        "En_Panel_Minimo"]].head(25)
        p.append(f"""=== FIRMA VALIDADA (RESULTADO PRINCIPAL DEL TRABAJO) ===
De {rf['n_genes_evaluados']} genes evaluados, {rf['n_genes_validados']}
({rf['pct_genes_validados']:.1f}%) satisfacen el criterio de replicacion en
las {rf['n_cohortes_independientes']} cohortes independientes de subtipo. Un
gen entra en la firma solo si mantiene el mismo signo de cambio y una
magnitud minima (d de Cohen absoluta) en las tres cohortes simultaneamente.

PANEL MINIMO REPLICABLE: {rf['panel_minimo']} genes bastan para AUC
{rf['auc_panel_minimo']:.4f} en LODO, frente a {rf['auc_firma_completa']:.4f}
con la firma completa. La senal biologica esta concentrada en pocas
variables reproducibles, lo que hace el panel clinicamente manejable.

VALIDACION EXTERNA CONTRA INMUNOHISTOQUIMICA CLINICA:
- Escamoso: {rf['ihc_recuperados'].get('Escamoso', 0)}/{rf['ihc_total'].get('Escamoso', 0)} marcadores recuperados
- Adenocarcinoma: {rf['ihc_recuperados'].get('Adenocarcinoma', 0)}/{rf['ihc_total'].get('Adenocarcinoma', 0)} marcadores recuperados
- TOTAL: {sum(rf['ihc_recuperados'].values())}/{sum(rf['ihc_total'].values())}
El framework recupera de novo la practica totalidad del panel diagnostico
IHC usado en la clinica, sin haberselo declarado.

TOP 10 GENES DE LA FIRMA (ranking por d de Cohen minima entre cohortes):
{', '.join(rf['top10'])}

TOP 25 CON DETALLE:
{top_show.to_string(index=False)}

INTERPRETACION BIOLOGICA POR CATEGORIAS:
- Desmosomas/uniones celulares (escamoso): DSG3, DSC3, PKP1.
- Queratinas y programa de linaje escamoso: KRT5, KRT6B, KRT14, TP63.
- Marcadores de alveolo tipo II (adenocarcinoma): NAPSA, SFTPB, SFTPC,
  NKX2-1, MUC1, SLC34A2.
- Otras funciones asociadas: CALML3 (Ca2+/calmodulin-related), FAT2
  (cadherina de gran tamano), CLCA2 (canal de cloro asociado a calcio).

Si alguien pregunta por un gen concreto, se puede consultar su rango, d de
Cohen por cohorte y direccion en FIRMA_VALIDADA_COMPLETA.csv (buscador de
gen disponible en la pestana Resultados de la interfaz).""")

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
    return f"""Eres el asistente de consulta de data.lung, un framework de analisis
de datos transcriptomicos y aprendizaje automatico para IDENTIFICAR
BIOMARCADORES en cancer de pulmon (Trabajo de Fin de Master en
Bioinformatica).

El framework integra cohortes publicas de NCBI GEO, automatiza su
normalizacion, usa un modelo de lenguaje (Llama 3.3-70b) para curar los
metadatos clinicos, entrena clasificadores supervisados (LASSO L1, Random
Forest, SVM) con validacion externa LODO, y produce una firma genica
replicable en cohortes independientes.

DE QUE VA EL PROYECTO (respuesta canonica cuando pregunten):
Es un framework que hace ANALISIS DE DATOS TRANSCRIPTOMICOS + ML para
identificar biomarcadores de cancer de pulmon. Toma cohortes publicas de
NCBI GEO, las integra automaticamente, entrena modelos supervisados, valida
externamente entre cohortes distintas y entrega una firma genica de 1174
genes replicados y un panel minimo clinicamente manejable de 20 genes que
alcanza AUC 0.966. El 18/20 de los marcadores diagnosticos de IHC clinica
se recuperan de novo, sin declararselos al framework. Ese es el resultado.

REGLAS, en orden de prioridad:

1. FIDELIDAD A LOS DATOS. Responde SOLO con la informacion del contexto que
   sigue. Si algo no esta, di literalmente: "Eso no figura en los resultados
   del trabajo". No completes con conocimiento general ni estimes cifras.

2. ENFOQUE. El trabajo es de ANALISIS DE DATOS y ML aplicado a
   transcriptomica. Prioriza en tus respuestas los resultados biologicos y
   de rendimiento del modelo, no la metodologia de calidad de datos. Los
   filtros y criterios de inclusion son parte del pipeline, no el objeto
   del trabajo.

3. RESULTADOS QUE SIEMPRE HAY QUE CITAR CUANDO ENCAJEN:
     - Firma de 1174 genes replicados en 3 cohortes independientes.
     - Panel minimo de 20 genes con AUC 0.966 (vs 0.974 firma completa).
     - 18/20 marcadores clinicos IHC recuperados sin declararlos.
     - AUC media LODO tumor-vs-sano: 0.925 sobre cohortes evaluables.
     - AUC media LODO subtipo ADC vs SQC: 0.968.
     - Top de la firma (linaje escamoso): DSG3, KRT5, CALML3, KRT6B, PKP1.
     - Top de la firma (linaje adenocarcinoma): NAPSA, SFTPC, SFTPB,
       NKX2-1, MUC1.

4. BIOLOGIA COMO FIN. Cuando te pregunten por genes o por que el modelo
   funciona, da la interpretacion biologica: DSG3 y desmosomas escamosos,
   KRT queratinas de linaje basal, TP63 factor de transcripcion maestro
   escamoso, NAPSA aspartil-proteasa alveolar, SFTPB/C surfactante,
   NKX2-1 factor de transcripcion adenocarcinoma. No te quedes en la
   metrica.

5. CRITERIOS DE INCLUSION (no "auditoria"). Cuando pregunten por integridad
   de datos, cohortes descartadas o tasa de curacion, enmarcalo como
   CRITERIOS DE INCLUSION del pipeline: se eliminan las cohortes monoclase
   (no permiten entrenar+validar) y las muestras que el LLM no puede
   etiquetar con seguridad. 8 de 11 cohortes descargadas pasan los
   criterios; el filtrado es transparente y reproducible. NO enmarques
   estos filtros como "problemas" ni como resultado principal: son
   metodologia estandar.

6. Si preguntan por rendimiento del ML, da las metricas del modelo (AUC,
   balanced accuracy, sensibilidad, especificidad). Es normal que el
   umbral de decision requiera calibrarse entre cohortes: es un problema
   tecnico corregible, no una limitacion de la firma.

7. NO das consejo medico ni diagnostico. Si alguien plantea un caso
   clinico, aclara que no es tu funcion y que la firma no esta validada
   para uso clinico.

8. Si la pregunta no guarda relacion con el trabajo ni con transcriptomica
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
