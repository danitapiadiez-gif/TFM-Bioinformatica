# data.lung

> **Framework transcriptómico basado en la integración de modelos de lenguaje y aprendizaje automático para la identificación de biomarcadores en cáncer de pulmón.**

Trabajo Fin de Máster — Máster Universitario en Bioinformática, Universidad Alfonso X el Sabio (UAX), curso 2025-2026.

**Autor:** Daniel Tapia Díez · **Tutor:** Leonardo Dulcetti · **Convocatoria extraordinaria** (defensa: 3 septiembre 2026).

---

## Qué es esto

Un pipeline reproducible extremo a extremo que descarga cohortes públicas de expresión génica de NCBI GEO, cura sus metadatos clínicos con un modelo de lenguaje grande (Llama 3.3-70b vía Groq), aplica meta-análisis por consenso multi-cohorte, entrena clasificadores supervisados con validación externa Leave-One-Dataset-Out (LODO), y produce una firma génica interpretable validada contra el panel diagnóstico IHC de la OMS.

La aplicación web `data.lung` expone los resultados navegables y un asistente conversacional acotado.

---

## Resultados clave

| Métrica | Valor |
|---|---|
| Cohortes GEO descargadas | 11 (8 evaluables) |
| Muestras curadas por LLM | 1.157 (82,8 % de éxito) |
| Firma génica validada | **1.174 genes** replicados en 3 cohortes independientes |
| Panel mínimo clínicamente traducible | **20 genes** (AUC 0,966 vs 0,974 firma completa) |
| AUC LODO subtipo ADC vs SQC | **0,968** |
| AUC LODO tumor vs sano (con recalibración isotónica) | **0,953** (BalAcc 0,772 → 0,810) |
| AUC transferido a RNA-Seq (TCGA n=408) | **0,857** [IC 95 % 0,812–0,899] |
| Marcadores IHC OMS recuperados sin declararlos | **18 / 20** (12/12 escamoso · 6/8 adenocarcinoma) |

---

## Arquitectura

```
                ┌───────────────────────────────────────────┐
   NCBI GEO ──▶ │  PIPELINE (agentes/paso1…paso23)          │ ──▶  Artefactos CSV/JSON
                │  Ingesta ▸ LLM ▸ Consenso ▸ LODO ▸ Panel  │      (raíz del proyecto)
                └───────────────────────────────────────────┘                    │
                                                                                 ▼
                                                             ┌─────────────────────────────┐
                                                             │  APP web data.lung          │
                                                             │  (Streamlit multipágina)    │
                                                             │  + asistente Llama acotado  │
                                                             └─────────────────────────────┘
```

Los pasos se ejecutan como módulos Python independientes y depositan sus outputs en rutas predecibles. La app y la memoria leen esos artefactos: **ninguna cifra está hard-coded**.

---

## Estructura del repositorio

```
.
├── agentes/                    # 24 pasos del pipeline (paso1..paso24)
├── tfm/                        # Paquete Python con utilidades reutilizables
│   ├── cohortes.py             #   carga y alineamiento por geo_accession
│   ├── tareas.py               #   tareas biológicas definidas en YAML
│   ├── validacion.py           #   una sola implementación de LODO
│   ├── firma.py                #   criterios de replicación y panel mínimo
│   └── comprobaciones.py       #   controles automáticos previos
├── tests/                      # Pytest (~17 tests incluido regresión GSE30219)
├── configuracion/
│   └── tareas.yaml             # Tareas biológicas (subtipo, tumor/sano...)
├── .streamlit/                 # Configuración de la app
├── resultados/                 # Outputs del pipeline (CSV / JSON)
│   ├── auditoria/              #   controles de cohortes y auditoría LLM
│   ├── subtipo/                #   firma y métricas ADC vs SQC
│   ├── tumor_vs_sano/          #   firma y métricas tumor vs sano
│   ├── firma_consenso/         #   firma consenso final + panel IHC
│   ├── recalibracion/          #   recalibración isotónica + IC bootstrap
│   ├── comparativa_ml/         #   LASSO vs RF vs SVM
│   └── tcga/                   #   validación externa TCGA RNA-Seq
├── memoria/                    # Fuente LaTeX de la memoria del TFM
│   ├── main.tex + main.pdf     #   100 páginas, PDF final
│   ├── capitulos/              #   8 capítulos + 7 anexos
│   ├── figuras/                #   diagramas y figuras
│   └── bibliografia.bib
├── presentacion/               # Defensa Beamer + resumen ejecutivo UAX
├── datasets.txt                # Lista de cohortes GEO a descargar
├── requirements.txt            # Dependencias Python
├── pyproject.toml              # Paquete tfm/ instalable
└── README.md                   # Este fichero
```

---

## Instalación

Requisitos: **Python 3.12+** y una clave de API de [Groq](https://groq.com) (gratuita para el volumen del TFM).

```bash
git clone https://github.com/danitapiadiez-gif/TFM-Bioinformatica
cd TFM-Bioinformatica

# Entorno virtual + dependencias
python -m venv venv
source venv/bin/activate           # macOS/Linux
# venv\Scripts\activate            # Windows
pip install -r requirements.txt
pip install -e .                   # instala el paquete tfm/

# Configurar clave Groq
echo "GROQ_API_KEY=tu_clave_aqui" > .env
```

---

## Uso

### Pipeline completo

```bash
# Ejecuta los 9 pasos en orden, descargando cohortes GEO y produciendo
# todos los CSV/JSON de resultados en la raíz.
python -m tfm ejecutar subtipo_histologico
python -m tfm ejecutar tumor_vs_sano
```

O paso a paso, para iterar:

```bash
python agentes/paso1_descarga.py           # descarga cohortes GEO
python agentes/paso2b_bulk.py              # normalización log2 + cuantiles
python agentes/paso3_diferencial.py        # curación clínica con LLM
python agentes/paso5_graficos.py           # análisis diferencial (Welch + FDR)
python agentes/paso7_orquestador.py        # LODO externo
python agentes/paso13_subtipo_lodo.py      # clasificador de subtipo
python agentes/paso20_recalibracion.py     # recalibración isotónica
python agentes/paso21_bootstrap_ic.py      # intervalos de confianza
python agentes/paso22_comparativa_ml.py    # comparativa LASSO / RF / SVM
python agentes/paso23_validacion_tcga.py   # transferencia a TCGA RNA-Seq
```

### Interfaz web

```bash
streamlit run agentes/paso12_web_chatbot.py
```

Abre <http://localhost:8501>. Siete capítulos navegables, buscador de gen sobre la firma, vista por cohorte, y asistente conversacional Llama 3.3-70b acotado a los resultados.

### Comprobar tareas y correr los tests

```bash
python -m tfm listar                       # tareas biológicas declaradas
python -m tfm comprobar                    # cuatro controles automáticos
python -m pytest tests -q                  # batería de tests
```

---

## Añadir una tarea biológica sin escribir código

En `configuracion/tareas.yaml`:

```yaml
gen_conductor:
  descripcion: EGFR mutado frente a triple negativo (EGFR/KRAS/ALK).
  relevancia_clinica: Determina la indicación de inhibidores de tirosina quinasa.
  clases: {0: triple_negativo, 1: egfr_mutado}
  modelo: {C: 0.1, class_weight: balanced}
  cohortes:
    - gse: GSE31210
      columna: characteristics_ch1_7_gene_alteration_status
      mapa: {"EGFR mutation +": 1, "EGFR/KRAS/ALK -": 0}
      descartar: ["KRAS mutation +", "ALK-fusion +"]
```

Y después:

```bash
python -m tfm ejecutar gen_conductor
```

El framework aplica solo el alineamiento por `geo_accession`, ejecuta los controles previos, corre LODO con baseline declarado, y produce firma replicada y panel mínimo.

---

## Reproducibilidad

- **Semilla fija** `random_state=42` en todos los pasos aleatorizados.
- **Artefactos versionados**: cada paso escribe CSV/JSON auditables.
- **Datos públicos**: cohortes GEO y TCGA accesibles por cualquiera.
- **Cifras de la memoria** coinciden bit a bit con las de los CSV del pipeline.

Invariantes garantizadas por el paquete `tfm/`:

1. Toda carga alinea por `geo_accession`, no por posición (regresión GSE30219 cubierta por test).
2. Una sola implementación del LODO en `tfm.validacion`.
3. Cohortes de una sola clase se marcan como no evaluables y quedan fuera de las medias.
4. Los cuatro controles automáticos (`tfm.comprobaciones`) se ejecutan antes de cualquier análisis.

---

## Compilar la memoria y la defensa

```bash
# Memoria
cd memoria
latexmk -pdf main.tex           # 100 páginas, ~3 MB

# Presentación de defensa (LaTeX)
cd presentacion
pdflatex defensa.tex

# Resumen ejecutivo (LaTeX horizontal 1 hoja)
pdflatex resumen_uax.tex
```

Los ficheros oficiales para entregar a UAX están en la carpeta `~/Desktop/ENTREGA_TFM/` (fuera de este repo, con formato `2526_TFM_OMBF_NPxxxxx_*`).

---

## Stack tecnológico

- **Lenguaje**: Python 3.12
- **Análisis científico**: `pandas`, `numpy`, `scipy.stats`, `statsmodels`, `scikit-learn`
- **Acceso a datos**: `GEOparse` (NCBI GEO), API REST de cBioPortal (TCGA)
- **LLM**: Llama 3.3-70b servido vía [Groq](https://groq.com) (hardware LPU)
- **Interfaz web**: [Streamlit](https://streamlit.io)
- **Memoria y defensa**: LaTeX (pdflatex, beamer, tikz)
- **Control de versiones**: Git + GitHub Actions

---

## Cómo se estructura el paquete `tfm/`

Antes de refactorizar, el pipeline tenía el bucle LODO reimplementado cinco veces (con divergencias entre versiones) y las cohortes/modelos/umbrales escritos en `.py`. El paquete `tfm/` centralizó esa lógica:

- **`cohortes.py`** — carga y alineamiento por `geo_accession` (nunca por posición).
- **`tareas.py`** — una tarea = etiquetas + mapa, definida en YAML.
- **`validacion.py`** — una sola implementación del LODO honesta.
- **`firma.py`** — criterios de replicación y construcción del panel mínimo.
- **`comprobaciones.py`** — controles automáticos previos al análisis.
- **`cli.py`** — punto de entrada `python -m tfm`.

El refactor no altera ninguna cifra publicada: verificado sobre las diez principales (BalAcc 0,7722, AUC 0,9252, especificidad 0,5615, ρ −0,6257, AUC subtipo 0,9683, 1174 genes validados, panel mínimo 20, etc.).

---

## Referencias esenciales

- Beer et al., *Nat Med* 2002 — primeras firmas génicas de supervivencia en ADC pulmonar.
- Subramanian & Simon, *JNCI* 2010 — revisión de firmas génicas: por qué la mayoría no replica.
- Travis et al., *J Thorac Oncol* 2015 — clasificación OMS 2015 con panel IHC de referencia.
- Johnson et al., *Biostatistics* 2007 — algoritmo ComBat para corrección de efecto lote.

Referencias completas en `memoria/bibliografia.bib`.

---

## Licencia

Código bajo licencia MIT. Datos: NCBI GEO y TCGA son de dominio público. Consultar las condiciones de uso de la [API de Groq](https://groq.com/terms) para el uso del LLM.

---

## Cita

Si utilizas este framework en tu investigación:

```bibtex
@mastersthesis{tapia2026datalung,
  author = {Tapia Díez, Daniel},
  title  = {Framework transcriptómico basado en la integración de modelos de
            lenguaje y aprendizaje automático para la identificación de
            biomarcadores en cáncer de pulmón},
  school = {Universidad Alfonso X el Sabio},
  year   = {2026},
  type   = {Trabajo Fin de Máster},
  url    = {https://github.com/danitapiadiez-gif/TFM-Bioinformatica}
}
```
