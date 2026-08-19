# Resultados del pipeline

Ficheros CSV y JSON producidos por los pasos del pipeline, organizados por tarea biológica:

| Carpeta | Contenido |
|---|---|
| `auditoria/` | Controles de cohortes, auditoría manual del LLM y comparaciones metodológicas |
| `subtipo/` | Firma y métricas de la tarea ADC vs SQC (subtipo histológico) |
| `tumor_vs_sano/` | Firma y métricas de la tarea tumor vs sano |
| `firma_consenso/` | Firma consenso final, panel mínimo y validación IHC |
| `recalibracion/` | Recalibración isotónica y Platt del clasificador tumor vs sano |
| `comparativa_ml/` | Comparativa LASSO / Random Forest / SVM bajo LODO |
| `tcga/` | Validación externa en RNA-Seq TCGA (LUAD + LUSC) |

Todos los ficheros son **regenerables** ejecutando el pipeline
(`python -m tfm ejecutar <tarea>` o los `agentes/paso*.py`
individuales). Se incluyen en el repositorio para reproducibilidad y
auditoría sin necesidad de ejecutar todo el pipeline.
