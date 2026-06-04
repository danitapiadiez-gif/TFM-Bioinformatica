# Genomic Intelligence Framework (TFM) 

> **Pipeline Automatizado para el Análisis y Síntesis de Datos Genómicos: Aplicación en la Identificación de Biomarcadores en Cáncer de Pulmón**

Este repositorio contiene un framework bioinformático integral diseñado para automatizar el descubrimiento de firmas moleculares robustas. El sistema descarga, procesa, clasifica y analiza múltiples estudios transcriptómicos de forma autónoma, culminando en un meta-análisis respaldado por Inteligencia Artificial y métricas de consenso deterministas.

---

## 🎯 Objetivo del Proyecto

En la investigación oncológica actual, la heterogeneidad de los datos y el "efecto por lotes" (batch effect) dificultan la identificación de biomarcadores universales. Este proyecto resuelve ese problema mediante:
1.  **Automatización:** Procesamiento masivo de cohortes de la base de datos NCBI GEO.
2.  **Clasificación Inteligente:** Uso de LLMs (Llama 3) para interpretar metadatos clínicos complejos y mapear muestras (Ej: Tumor vs. Sano).
3.  **Consenso Estadístico:** Identificación de genes que mantienen una consistencia direccional estricta (LogFC) a través de múltiples estudios independientes.

---

## 🏗️ Arquitectura del Pipeline

El orquestador principal (`paso7_orquestador.py`) ejecuta un flujo de trabajo lineal y modular para cada dataset especificado en `datasets.txt`:

*   **Paso 1: Descarga y Mapeo:** Extracción de matrices de expresión (`.soft.gz`) vía `GEOparse`.
*   **Paso 1.5: Traducción Genómica:** Conversión automática de IDs de sondas (probes) a símbolos de genes oficiales.
*   **Paso 2: Curación Clínica (IA):** Análisis de metadatos mediante *Groq API* para asignar grupos experimentales (Sano vs Enfermo), filtrando estudios no comparativos.
*   **Paso 3: Análisis Diferencial:** Cálculo de T-Test de Welch y corrección FDR (Benjamini-Hochberg) para identificar genes diferencialmente expresados (DEGs).
*   **Paso 4 & 5: Visualización Base:** Generación automática de PCA, Volcano Plots y Heatmaps jerárquicos por estudio.
*   **Paso 6: Machine Learning:** Entrenamiento automatizado de modelos predictivos (Random Forest, SVM, Regresión Logística) para evaluar la capacidad diagnóstica de la firma.

---

## 🔬 Módulo de Meta-Análisis y Síntesis

Una vez procesados los estudios individuales, el framework ejecuta la síntesis final:

### Paso 8: Meta-Análisis Estadístico (`paso8_meta_analisis.py`)
Extrae los resultados de todos los estudios exitosos y calcula una **Matriz de Consistencia Direccional**. Se descartan los genes contradictorios y se seleccionan aquellos con la mayor Magnitud de Impacto (Average LogFC) compartida entre cohortes.

### Paso 9: The Genomic Intelligence Dashboard (`paso9_mega_dashboard.py`)
Genera un informe interactivo (HTML/Tailwind/Chart.js) de nivel profesional que incluye:
-   **Gráficos de Magnitud:** Visualización del TOP 50 de biomarcadores según la fuerza de su señal biológica.
-   **Matriz de LogFC:** Heatmap determinista de la expresión génica cruzada por estudio.
-   **Síntesis Biológica:** Fichas técnicas redactadas por IA que explican el rol biológico, relevancia clínica y potencial terapéutico de los genes ganadores.

---

## 🚀 Guía de Uso

### 1. Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configuración (API Keys)
El sistema utiliza Groq (Llama 3.3-70b) para la curación de metadatos y la síntesis final. Debes crear un archivo `.env` en la raíz del proyecto:
```env
GROQ_API_KEY=tu_clave_api_aqui
```

### 3. Ejecución
Para lanzar el pipeline completo sobre la lista de estudios definida en `datasets.txt`:
```bash
python agentes/paso7_orquestador.py
```
Para generar el Dashboard final tras el procesamiento:
```bash
python agentes/paso8_meta_analisis.py
python agentes/paso9_mega_dashboard.py
```

---

## 📊 Resultados Generados
*   **`TFM_GSE*/`**: Carpetas individuales por estudio con métricas, gráficos y un dashboard específico.
*   **`BIOMARCADORES_UNIVERSALES_CANCER_PULMON.csv`**: El dataset crudo con los resultados del meta-análisis.
*   **`MEGA_DASHBOARD_CONSENSO_PULMON.html`**: El informe final interactivo y visual.

---
*Trabajo de Fin de Máster (TFM)*
