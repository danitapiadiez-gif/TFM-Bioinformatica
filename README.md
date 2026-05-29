# Genomic Intelligence Framework (TFM) 🧬🔬

Este framework automatiza el análisis transcriptómico de estudios de cáncer de pulmón (GEO/NCBI) utilizando Agentes de Inteligencia Artificial para la síntesis de resultados.

## 🚀 Características Principales
- **Descarga Automatizada:** Conexión directa con la base de datos GEOparse.
- **Clasificación Inteligente (IA):** Uso de Llama 3 (Groq API) para la curación de metadatos clínicos.
- **Traducción Genómica:** Mapeo automático de sondas (probes) a símbolos oficiales.
- **Meta-Análisis de Consenso:** Identificación de biomarcadores universales en múltiples cohortes.
- **Dashboard Interactivo:** Generación de informes dinámicos en HTML/TailwindCSS.

## 🛠️ Instalación
```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/nombre-del-repo.git

# Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Configuración
Crea un archivo `.env` en la raíz y añade tu clave:
```env
GROQ_API_KEY=tu_clave_aqui
```

## 📊 Ejecución
```bash
python agentes/paso7_orquestador.py
```
