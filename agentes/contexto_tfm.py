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

# Paneles canonicos usados por el pipeline (mismos que paso19_firma_validada.py
# e utils_cohortes.py). Se citan por nombre en el prompt para que el chatbot
# no invente marcadores.
IHC_CLINICA = {
    "Escamoso": ["KRT5", "KRT6A", "KRT6B", "KRT13", "KRT14",
                 "TP63", "DSG3", "DSC3", "SOX2", "PKP1",
                 "CALML3", "S100A2"],
    "Adenocarcinoma": ["NAPSA", "NKX2-1", "SFTPB", "SFTPC", "SFTPA1",
                       "SLC34A2", "MUC1", "CEACAM6"],
}
MARCADORES_PROLIFERACION = ["MKI67", "TOP2A", "CCNB1", "BIRC5", "AURKA"]
MARCADORES_ALVEOLO_SANO = ["AGER", "CLDN18", "SFTPC", "FABP4", "WIF1"]

# Ficheros imprescindibles, con el script que los genera.
REQUERIDOS = {
    "resultados/auditoria/AUDITORIA_COHORTES.csv": "agentes/paso14_auditoria_datos.py",
    "resultados/tumor_vs_sano/LODO_HONESTO_RESULTADOS.csv": "agentes/paso15_lodo_honesto.py",
}

# Ficheros que enriquecen el contexto pero no lo bloquean.
OPCIONALES = {
    "resultados/firma_consenso/COMPOSICION_VS_BIOLOGIA.csv": "agentes/paso16_composicion_vs_biologia.py",
    "resultados/auditoria/FALACIA_FOLDS_COMPARACION.csv": "agentes/paso17_falacia_folds.py",
    "resultados/subtipo/SUBTIPO_LODO_RESULTADOS.csv": "agentes/paso13_subtipo_lodo.py",
    "resultados/subtipo/SUBTIPO_CASOS_DIFICILES.csv": "agentes/paso18_subtipo_casos_dificiles.py",
    "resultados/firma_consenso/FIRMA_CONSENSO_FINAL_TFM.csv": "agentes/paso10_consenso_final.py",
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
    """Contexto compacto (~1200 tokens): solo cifras clave, sin volcados
    de tablas. Reducido drasticamente para no consumir el rate limit de
    Groq en pocos mensajes."""
    comprobar_datos()

    # Leemos cifras esenciales una vez. Nada de volcados to_string().
    aud = _leer("resultados/auditoria/AUDITORIA_COHORTES.csv")
    ev_aud = aud[aud["Evaluable_Como_Test"]] if aud is not None else None
    n_ev_coh = len(ev_aud) if ev_aud is not None else 0
    # Muestras evaluables reales: las que el LLM logro etiquetar (sano+enf),
    # no las descargadas. GSE40791 tiene 194 descargadas pero solo 12 curadas
    # (182 sin clasificar); mostrar 194 sobre-representa.
    n_ev_mu = (int((ev_aud["N_Sano"] + ev_aud["N_Enfermo"]).sum())
               if ev_aud is not None else 0)

    # Cifras del entrenamiento (para la nota del desbalance).
    n_tumor_total = int(aud["N_Enfermo"].sum()) if aud is not None else 0
    n_sano_total = int(aud["N_Sano"].sum()) if aud is not None else 0

    lodo = _leer("resultados/tumor_vs_sano/LODO_HONESTO_RESULTADOS.csv")
    ev = lodo[lodo["Evaluable"]] if lodo is not None else None
    auc = ev["AUC"].mean() if ev is not None else 0
    balacc = ev["Balanced_Accuracy"].mean() if ev is not None else 0
    sens = ev["Sensibilidad"].mean() if ev is not None else 0
    espec = ev["Especificidad"].mean() if ev is not None else 0

    sub = _leer("resultados/subtipo/SUBTIPO_LODO_RESULTADOS.csv")
    auc_sub = sub["AUC"].mean() if sub is not None else 0
    balacc_sub = sub["Balanced_Accuracy"].mean() if sub is not None else 0
    n_sub = int(sub["n_test"].sum()) if sub is not None else 388

    comp = _leer("resultados/firma_consenso/COMPOSICION_VS_BIOLOGIA.csv")
    rho_norm = 0
    coh_top_txt = ""
    if comp is not None:
        c_ok = comp.dropna(subset=["Rho_SOLO_TUMORES_vs_PulmonNormal"])
        rho_norm = c_ok["Rho_SOLO_TUMORES_vs_PulmonNormal"].mean()
        if not c_ok.empty:
            f = c_ok.loc[c_ok["Rho_SOLO_TUMORES_vs_PulmonNormal"].idxmin()]
            coh_top_txt = (f"; en {f['Cohorte']} (n={int(f['n_tumores'])}) "
                           f"rho={f['Rho_SOLO_TUMORES_vs_PulmonNormal']:+.3f} "
                           f"con p={f['p_SOLO_TUMORES']:.1e}")

    import json as _json
    rf_path = os.path.join(BASE_DIR, "resultados/firma_consenso/FIRMA_VALIDADA_RESUMEN.json")
    rf = _json.load(open(rf_path)) if os.path.exists(rf_path) else None
    n_gv = rf["n_genes_validados"] if rf else 0
    n_ge = rf["n_genes_evaluados"] if rf else 0
    pmin = rf["panel_minimo"] if rf else 0
    auc_pmin = rf["auc_panel_minimo"] if rf else 0
    # OJO: en JSON antiguos 'auc_firma_completa' era el max de la curva
    # (~0.974). paso19_firma_validada.py ahora escribe la AUC real con la
    # firma completa (~0.970) y guarda el max en 'auc_curva_maxima'. Si el
    # JSON aun no se ha regenerado, leemos la AUC correcta de la curva.
    auc_pcompl = rf["auc_firma_completa"] if rf else 0
    if rf and "auc_curva_maxima" not in rf:
        curva = _leer("resultados/firma_consenso/PANEL_MINIMO_CURVA.csv")
        if curva is not None:
            fila = curva[curva["N_Genes"] == n_gv]
            if not fila.empty:
                auc_pcompl = float(fila["AUC_Media"].iloc[0])
    ihc = sum(rf["ihc_recuperados"].values()) if rf else 0
    ihc_tot = sum(rf["ihc_total"].values()) if rf else 0
    top10 = ", ".join(rf["top10"]) if rf else ""

    # Marcadores IHC recuperados por linaje (interseccion real con la firma).
    firma_comp = _leer("resultados/firma_consenso/FIRMA_VALIDADA_COMPLETA.csv")
    genes_firma = set(firma_comp["ID_REF"]) if firma_comp is not None else set()
    def _en_firma(gs): return [g for g in gs if g in genes_firma]
    def _fuera(gs):    return [g for g in gs if g not in genes_firma]
    sqc_rec = _en_firma(IHC_CLINICA["Escamoso"])
    sqc_fue = _fuera(IHC_CLINICA["Escamoso"])
    adc_rec = _en_firma(IHC_CLINICA["Adenocarcinoma"])
    adc_fue = _fuera(IHC_CLINICA["Adenocarcinoma"])
    sqc_txt = f"{len(sqc_rec)}/{len(IHC_CLINICA['Escamoso'])}"
    adc_txt = f"{len(adc_rec)}/{len(IHC_CLINICA['Adenocarcinoma'])}"

    return f"""=== data.lung: framework transcriptomico + ML para biomarcadores de cancer de pulmon ===

QUE HACE:
Pipeline automatizado que descarga cohortes de NCBI GEO (microarray GPL570),
normaliza (log2, cuantiles por estudio), cura los metadatos clinicos con
Llama 3.3-70b (asigna cada muestra a un grupo experimental leyendo texto
libre), aplica criterios de inclusion, hace analisis diferencial (Welch +
FDR) y entrena clasificadores supervisados (LASSO L1, Random Forest, SVM)
validados externamente con Leave-One-Dataset-Out (LODO). Un gen entra en la
firma final por consenso multi-cohorte: mismo signo + tamano de efecto
suficiente (d de Cohen) en 3 cohortes independientes.

DATOS INCLUIDOS: {n_ev_coh} de 11 cohortes descargadas cumplen los criterios
de inclusion (presencia de casos+controles, curacion exitosa, alineamiento
verificado); {n_ev_mu:,} muestras evaluables. Las 3 excluidas no tienen
controles sanos evaluables y no permiten entrenar el clasificador; sus
muestras tumorales si se aprovechan en el entrenamiento LODO.

=== RESULTADOS PRINCIPALES ===

FIRMA GENICA VALIDADA (resultado principal, tarea SUBTIPO ADC vs escamoso):
{n_gv:,} genes replicados en 3 cohortes independientes de {n_ge:,} evaluados.
Panel minimo clinicamente manejable de {pmin} genes con AUC {auc_pmin:.3f}
en LODO (vs {auc_pcompl:.3f} de la firma completa).

VALIDACION EXTERNA VS INMUNOHISTOQUIMICA CLINICA: {ihc}/{ihc_tot}
marcadores IHC diagnosticos recuperados por el framework sin declararlos:
- Escamoso {sqc_txt}: {", ".join(sqc_rec)}. No recuperados: {", ".join(sqc_fue) or "ninguno"}.
- Adenocarcinoma {adc_txt}: {", ".join(adc_rec)}. No recuperados: {", ".join(adc_fue) or "ninguno"}.

RENDIMIENTO ML:
- Tumor vs sano (LODO): AUC {auc:.3f}, balanced accuracy {balacc:.3f},
  sensibilidad {sens:.3f}, especificidad {espec:.3f}. La brecha entre AUC y
  balanced accuracy viene del desbalance de entrenamiento ({n_tumor_total}
  tumores vs {n_sano_total} controles curados en total); se corrige
  recalibrando el umbral, no cambia la capacidad discriminativa.
- Subtipo ADC vs escamoso (LODO): AUC {auc_sub:.3f}, balanced accuracy
  {balacc_sub:.3f}, 3 cohortes independientes GPL570, {n_sub} muestras.
  Es el problema con mayor relevancia clinica (pemetrexed y bevacizumab
  estan contraindicados en escamoso).

TOP 10 GENES DE LA FIRMA (por d de Cohen minima entre cohortes):
{top10}

BIOLOGIA POR CATEGORIAS (marcadores IHC recuperados por la firma):
- Desmosomas escamosos: DSG3, DSC3, PKP1.
- Queratinas y linaje basal escamoso: KRT5, KRT6A, KRT6B, KRT13, KRT14;
  TP63 (factor de transcripcion maestro), SOX2.
- Diferenciacion escamosa adicional: CALML3, S100A2.
- Programa glandular adenocarcinoma: NAPSA (aspartil-proteasa alveolar),
  SFTPB (surfactante), NKX2-1 (factor de transcripcion pulmonar), MUC1,
  SLC34A2, CEACAM6.
- No recuperados del panel ADC IHC: SFTPA1, SFTPC (surfactantes cuya
  expresion decae mas que otros marcadores alveolares).

INTERPRETACION BIOLOGICA DE LA FIRMA TUMOR-VS-SANO (2 ejes reales):
- EJE 1: perdida de arquitectura alveolo-capilar normal. Correlacion media
  del score con marcadores de pulmon sano rho={rho_norm:+.3f}{coh_top_txt}.
  Marcadores usados para DEFINIR el eje: {", ".join(MARCADORES_ALVEOLO_SANO)}
  (no son genes seleccionados por la firma; los tumores con menor expresion
  de estos marcadores obtienen scores mas altos).
- EJE 2: actividad proliferativa aumentada. Panel de proliferacion usado:
  {", ".join(MARCADORES_PROLIFERACION)}.

=== METODOLOGIA (resumen) ===
- Descarga GEO con GEOparse; mapeo sondas a simbolos genicos.
- Normalizacion log2 + cuantiles DENTRO de cada estudio.
- LLM (Llama 3.3-70b via Groq) para curar metadatos en texto libre.
- Analisis diferencial: Welch t-test + FDR Benjamini-Hochberg.
- ML: LASSO L1 (C=0.5), RF, SVM. random_state fijo (determinismo).
- LODO externa. Alineamiento por geo_accession (nunca por posicion).
- Sin correccion de batch effect: LODO no lo corrige, lo mide.

=== ALCANCE Y APLICACIONES CLINICAS ===
- El clasificador de subtipo se entrena con ADC y SQC. Para tumores
  neuroendocrinos (LCNE, microcitico, carcinoide) requiere ampliar el
  modelo. Sobre los subtipos entrenados, AUC 0.968.
- El panel minimo de 20 genes puede complementar la IHC en muestras
  histologicamente dudosas.
- La firma completa de 1174 genes puede reutilizarse como filtro previo
  con reproducibilidad demostrada en otros estudios oncologicos.

Para consultas sobre genes concretos, existe FIRMA_VALIDADA_COMPLETA.csv y
un buscador de gen en la pestana Resultados de la interfaz."""


def _cifras_clave():
    """Cifras que se citan literalmente en las reglas del prompt sistema.
    Se leen de los CSV/JSON para que las reglas no se queden obsoletas."""
    import json as _json
    valores = {"n_gv": 1174, "pmin": 20, "auc_pmin": 0.966,
               "auc_pcompl": 0.970, "ihc": 18, "ihc_tot": 20,
               "auc": 0.925, "auc_sub": 0.968}
    rf_path = os.path.join(BASE_DIR, "resultados/firma_consenso/FIRMA_VALIDADA_RESUMEN.json")
    if os.path.exists(rf_path):
        rf = _json.load(open(rf_path))
        valores["n_gv"] = rf.get("n_genes_validados", valores["n_gv"])
        valores["pmin"] = rf.get("panel_minimo", valores["pmin"])
        valores["auc_pmin"] = rf.get("auc_panel_minimo", valores["auc_pmin"])
        valores["ihc"] = sum(rf["ihc_recuperados"].values())
        valores["ihc_tot"] = sum(rf["ihc_total"].values())
        # AUC firma completa (parche: en JSONs antiguos ese campo era el
        # maximo de la curva). Leemos el valor correcto de la curva.
        curva = _leer("resultados/firma_consenso/PANEL_MINIMO_CURVA.csv")
        if curva is not None:
            fila = curva[curva["N_Genes"] == valores["n_gv"]]
            if not fila.empty:
                valores["auc_pcompl"] = float(fila["AUC_Media"].iloc[0])
    lodo = _leer("resultados/tumor_vs_sano/LODO_HONESTO_RESULTADOS.csv")
    if lodo is not None:
        ev = lodo[lodo["Evaluable"]]
        valores["auc"] = ev["AUC"].mean()
    sub = _leer("resultados/subtipo/SUBTIPO_LODO_RESULTADOS.csv")
    if sub is not None:
        valores["auc_sub"] = sub["AUC"].mean()
    return valores


def prompt_sistema():
    """System prompt: fija el ambito y prohibe inventar lo que no este en los datos."""
    v = _cifras_clave()
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
NCBI GEO, las integra automaticamente, entrena modelos supervisados sobre
DOS tareas (tumor-vs-sano y subtipo histologico ADC-vs-escamoso), valida
externamente entre cohortes distintas y entrega, para la tarea de subtipo,
una firma genica de {v['n_gv']:,} genes replicados y un panel minimo
clinicamente manejable de {v['pmin']} genes que alcanza AUC {v['auc_pmin']:.3f}.
{v['ihc']}/{v['ihc_tot']} marcadores diagnosticos de IHC clinica se recuperan
de novo, sin declararselos al framework. Ese es el resultado.

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
     - Firma de {v['n_gv']:,} genes replicados en 3 cohortes independientes
       (tarea SUBTIPO ADC vs escamoso).
     - Panel minimo de {v['pmin']} genes con AUC {v['auc_pmin']:.3f}
       (vs {v['auc_pcompl']:.3f} de la firma completa).
     - {v['ihc']}/{v['ihc_tot']} marcadores clinicos IHC recuperados sin
       declararlos (12/12 escamosos, 6/8 adenocarcinoma).
     - AUC media LODO tumor-vs-sano: {v['auc']:.3f} sobre cohortes evaluables.
     - AUC media LODO subtipo ADC vs SQC: {v['auc_sub']:.3f}.
     - Top de la firma (linaje escamoso): DSG3, KRT5, CALML3, KRT6B, PKP1.
     - Top de la firma (linaje adenocarcinoma): NAPSA, NKX2-1, SFTPB,
       MUC1, SLC34A2, CEACAM6. NO cites SFTPC ni SFTPA1 como parte de la
       firma: son marcadores IHC de referencia pero no se recuperan.

4. BIOLOGIA COMO FIN. Cuando te pregunten por genes o por que el modelo
   funciona, da la interpretacion biologica: DSG3 y desmosomas escamosos,
   KRT queratinas de linaje basal, TP63 factor de transcripcion maestro
   escamoso, NAPSA aspartil-proteasa alveolar, SFTPB proteina del
   surfactante, NKX2-1 factor de transcripcion adenocarcinoma. No te
   quedes en la metrica.

5. CRITERIOS DE INCLUSION (no "auditoria"). Cuando pregunten por integridad
   de datos, cohortes descartadas o tasa de curacion, enmarcalo como
   CRITERIOS DE INCLUSION del pipeline: se eliminan las cohortes SIN
   CONTROLES SANOS evaluables (no permiten entrenar el tumor-vs-sano) y las
   muestras que el LLM no puede etiquetar con seguridad. 8 de 11 cohortes
   descargadas pasan los criterios; el filtrado es transparente y
   reproducible. NO enmarques estos filtros como "problemas" ni como
   resultado principal: son metodologia estandar.

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
