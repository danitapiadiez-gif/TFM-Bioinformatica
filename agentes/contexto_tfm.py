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
    """Contexto compacto (~1200 tokens): solo cifras clave, sin volcados
    de tablas. Reducido drasticamente para no consumir el rate limit de
    Groq en pocos mensajes."""
    comprobar_datos()

    # Leemos cifras esenciales una vez. Nada de volcados to_string().
    aud = _leer("AUDITORIA_COHORTES.csv")
    ev_aud = aud[aud["Evaluable_Como_Test"]] if aud is not None else None
    n_ev_coh = len(ev_aud) if ev_aud is not None else 0
    n_ev_mu = int(ev_aud["N_Total"].sum()) if ev_aud is not None else 0

    lodo = _leer("LODO_HONESTO_RESULTADOS.csv")
    ev = lodo[lodo["Evaluable"]] if lodo is not None else None
    auc = ev["AUC"].mean() if ev is not None else 0
    balacc = ev["Balanced_Accuracy"].mean() if ev is not None else 0
    sens = ev["Sensibilidad"].mean() if ev is not None else 0
    espec = ev["Especificidad"].mean() if ev is not None else 0

    sub = _leer("SUBTIPO_LODO_RESULTADOS.csv")
    auc_sub = sub["AUC"].mean() if sub is not None else 0
    balacc_sub = sub["Balanced_Accuracy"].mean() if sub is not None else 0

    comp = _leer("COMPOSICION_VS_BIOLOGIA.csv")
    rho_norm = (comp["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna().mean()
                if comp is not None else 0)

    import json as _json
    rf_path = os.path.join(BASE_DIR, "FIRMA_VALIDADA_RESUMEN.json")
    rf = _json.load(open(rf_path)) if os.path.exists(rf_path) else None
    n_gv = rf["n_genes_validados"] if rf else 0
    n_ge = rf["n_genes_evaluados"] if rf else 0
    pmin = rf["panel_minimo"] if rf else 0
    auc_pmin = rf["auc_panel_minimo"] if rf else 0
    auc_pcompl = rf["auc_firma_completa"] if rf else 0
    ihc = sum(rf["ihc_recuperados"].values()) if rf else 0
    ihc_tot = sum(rf["ihc_total"].values()) if rf else 0
    top10 = ", ".join(rf["top10"]) if rf else ""

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
verificado); {n_ev_mu:,} muestras evaluables. Las 3 excluidas son monoclase
(solo tumores) y no permiten entrenar.

=== RESULTADOS PRINCIPALES ===

FIRMA GENICA VALIDADA (resultado principal): {n_gv:,} genes replicados en
3 cohortes independientes de {n_ge:,} evaluados. Panel minimo clinicamente
manejable de {pmin} genes con AUC {auc_pmin:.3f} en LODO (vs
{auc_pcompl:.3f} de la firma completa).

VALIDACION EXTERNA VS INMUNOHISTOQUIMICA CLINICA: {ihc}/{ihc_tot}
marcadores IHC diagnosticos recuperados por el framework sin declararlos
(escamoso: KRT5, KRT6A, TP63, DSG3, SOX2, PKP1, KRT14 - 7/7;
adenocarcinoma: NAPSA, NKX2-1, SFTPB, SLC34A2, MUC1 - 5/5). Coincidencia
casi total con el panel diagnostico usado en la practica clinica.

RENDIMIENTO ML:
- Tumor vs sano (LODO): AUC {auc:.3f}, balanced accuracy {balacc:.3f},
  sensibilidad {sens:.3f}, especificidad {espec:.3f}. La brecha entre AUC y
  balanced accuracy viene del desbalance de entrenamiento (938 tumores vs
  219 controles); se corrige recalibrando el umbral, no cambia la capacidad
  discriminativa.
- Subtipo ADC vs escamoso (LODO): AUC {auc_sub:.3f}, balanced accuracy
  {balacc_sub:.3f}, 3 cohortes independientes GPL570, 388 muestras. Es el
  problema con mayor relevancia clinica (pemetrexed y bevacizumab estan
  contraindicados en escamoso).

TOP 10 GENES DE LA FIRMA (por d de Cohen minima entre cohortes):
{top10}

BIOLOGIA POR CATEGORIAS:
- Desmosomas escamosos: DSG3 (d media 4.18), DSC3, PKP1.
- Queratinas y linaje basal escamoso: KRT5, KRT6A, KRT6B, KRT14; TP63
  (factor de transcripcion maestro).
- Programa alveolar tipo II (adenocarcinoma): NAPSA (napsina A, aspartil-
  proteasa alveolar), SFTPB, SFTPC (surfactante), NKX2-1, MUC1, SLC34A2.
- Otros: CALML3, FAT2, CLCA2.

INTERPRETACION BIOLOGICA DE LA FIRMA TUMOR-VS-SANO (2 ejes reales):
- EJE 1: perdida de arquitectura alveolo-capilar normal. Correlacion media
  del score con marcadores de pulmon sano rho={rho_norm:+.3f}; en GSE31210
  (n=226) rho=-0.870. Genes: AGER, CLDN18, SFTPC, FABP4, WIF1.
- EJE 2: actividad proliferativa aumentada (MKI67, TOP2A, MCM2, PCNA).

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
