import pandas as pd
import os
import re


def generar_dashboard(gse_id):
    """
    PASO 6: Genera un dashboard HTML moderno y legible (tema claro).
    """
    print(f"\n--- 🧾 PASO 6: GENERANDO DASHBOARD ({gse_id}) ---")
    base_path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    
    # ================== INFORME BIOLÓGICO ==================
    try:
        with open(os.path.join(base_path, "informe_biologico.txt"), "r", encoding="utf-8") as f:
            informe = f.read()
    except Exception:
        informe = "Informe automático no disponible. Modo exploratorio o sin IA."
    
    # Limpieza / formateo sencillo del informe
    informe_limpio = informe.replace("**", "").replace("__", "")
    informe_limpio = re.sub(r'^[\*\-]\s+', '', informe_limpio, flags=re.MULTILINE)
    informe_limpio = re.sub(r'=+', '', informe_limpio)

    lineas = informe_limpio.splitlines()
    lineas_fmt = []
    for linea in lineas:
        linea_stripped = linea.strip()
        if not linea_stripped:
            lineas_fmt.append("")
            continue
        
        es_titulo = False
        if linea_stripped.endswith(":"):
            es_titulo = True
        elif len(linea_stripped) > 3 and linea_stripped.isupper():
            es_titulo = True
        
        if es_titulo:
            lineas_fmt.append(
                f'<div style="font-size:1.05rem; font-weight:700; margin-top:8px; margin-bottom:4px;">{linea_stripped}</div>'
            )
        else:
            lineas_fmt.append(linea_stripped)
    
    informe_html = "<br>".join(lineas_fmt)
    
    # ================== RESULTADOS DIFERENCIAL ==================
    try:
        resultados = pd.read_csv(os.path.join(base_path, "resultados_completos.csv"))
        tiene_adj = 'adj_pvalue' in resultados.columns and len(resultados) > 0
    except Exception as e:
        print(f"⚠️ No se pudo cargar resultados_completos.csv: {e}")
        resultados = pd.DataFrame()
        tiene_adj = False
    
    def formato_p(x):
        try:
            x = float(x)
        except Exception:
            return x
        if x == 0:
            return "0.0"
        if x < 1e-4:
            return f"{x:.2e}"
        return f"{x:.4f}"
    
    if tiene_adj:
        tabla_titulo = "Genes significativos (FDR < 0.05)"
        top_sig = resultados[resultados['adj_pvalue'] < 0.05].sort_values('adj_pvalue').head(20).copy()
        
        if "pvalue" in top_sig.columns:
            top_sig["pvalue"] = top_sig["pvalue"].apply(formato_p)
        if "adj_pvalue" in top_sig.columns:
            top_sig["adj_pvalue"] = top_sig["adj_pvalue"].apply(formato_p)
        if "LogFC" in top_sig.columns:
            top_sig["LogFC"] = top_sig["LogFC"].round(4)
        
        tabla_html = top_sig[['GENE_SYMBOL', 'LogFC', 'pvalue', 'adj_pvalue']].to_html(
            index=False, classes='table table-striped table-hover table-sm',
            escape=False, justify='left')
    else:
        tabla_titulo = "Vista exploratoria de genes"
        if not resultados.empty and 'GENE_SYMBOL' in resultados.columns:
            top_sig = resultados.head(20).copy()
            cols = [c for c in ['GENE_SYMBOL', 'LogFC', 'pvalue'] if c in resultados.columns]
            if cols:
                if "LogFC" in cols:
                    top_sig["LogFC"] = top_sig["LogFC"].round(4)
                if "pvalue" in cols:
                    top_sig["pvalue"] = top_sig["pvalue"].apply(formato_p)
                tabla_html = top_sig[cols].to_html(
                    index=False, classes='table table-striped table-hover table-sm',
                    escape=False, justify='left')
            else:
                tabla_html = "<p>No hay columnas estándar para mostrar.</p>"
        else:
            tabla_html = "<p>No hay resultados de genes disponibles.</p>"
    
    modo_texto = "Análisis diferencial completo" if tiene_adj else "Análisis exploratorio (sin diseño estadístico válido)"
    
    # ================== CONTEXTO (MUESTRAS / GENES) ==================
    try:
        df_norm = pd.read_csv(os.path.join(base_path, "matriz_normalizada.csv"), index_col=0)
        n_genes, n_muestras = df_norm.shape
    except Exception:
        df_norm = None
        n_genes, n_muestras = None, None

    try:
        meta = pd.read_csv(os.path.join(base_path, "metadata_procesada.csv"), index_col=0)
        if "grupo_analisis" in meta.columns:
            grupos_dict = meta["grupo_analisis"].value_counts().to_dict()
        else:
            grupos_dict = {}
    except Exception:
        meta = None
        grupos_dict = {}

    grupos_texto = ", ".join([f"{g}: {n}" for g, n in grupos_dict.items()]) if grupos_dict else "No disponible"
    if n_genes is not None and n_muestras is not None:
        contexto_texto = (
            f"Este dataset incluye {n_muestras} muestras y {n_genes} genes expresados tras filtrado y normalización. "
            f"Los grupos de análisis definidos son: {grupos_texto}."
        )
    else:
        contexto_texto = "No se ha podido recuperar la información básica de número de muestras y genes."
    
    if gse_id.upper() == "GSE19188":
        contexto_texto += " Este estudio se centra en carcinomas de pulmón no microcíticos (NSCLC) en estadios iniciales."
    if gse_id.upper() == "GSE32863":
        contexto_texto += " Este estudio compara tejido tumoral de pulmón con tejido pulmonar normal pareado."
    
    # ================== ML: MÉTRICAS ==================
    ruta_ml = os.path.join(base_path, "resultados_ml.csv")
    if os.path.exists(ruta_ml):
        try:
            df_ml = pd.read_csv(ruta_ml)
            tabla_ml_html = df_ml.round(3).to_html(
                index=False, classes='table table-striped table-hover table-sm',
                escape=False, justify='left')
        except Exception as e:
            print(f"⚠️ No se pudo cargar resultados_ml.csv: {e}")
            tabla_ml_html = "<p>No se pudieron cargar las métricas de ML.</p>"
    else:
        tabla_ml_html = "<p>No hay resultados de ML disponibles para este GSE.</p>"
    
    # ================== ML: TOP 20 GENES ==================
    ruta_top20 = os.path.join(base_path, f"top20_genes_ml_{gse_id}.csv")
    tabla_top20_html = ""
    if os.path.exists(ruta_top20):
        try:
            df_top20 = pd.read_csv(ruta_top20)
            cols = [c for c in ["gen", "coef_logreg", "importancia_rf"] if c in df_top20.columns]
            if cols:
                df_top20 = df_top20[cols].copy()
                
                def formato_coef(x):
                    try:
                        x = float(x)
                    except Exception:
                        return x
                    if x == 0:
                        return "0.0"
                    return f"{x:.2e}"
                
                if "coef_logreg" in df_top20.columns:
                    df_top20["coef_logreg"] = df_top20["coef_logreg"].apply(formato_coef)
                if "importancia_rf" in df_top20.columns:
                    df_top20["importancia_rf"] = df_top20["importancia_rf"].apply(formato_coef)
                
                tabla_top20_html = df_top20.to_html(
                    index=False, classes='table table-striped table-hover table-sm',
                    escape=False, justify='left')
            else:
                tabla_top20_html = "<p>El fichero de top 20 de ML no tiene las columnas esperadas.</p>"
        except Exception as e:
            print(f"⚠️ No se pudo cargar top20_genes_ml_{gse_id}.csv: {e}")
            tabla_top20_html = "<p>No se pudieron cargar los genes importantes de ML.</p>"
    else:
        tabla_top20_html = "<p>No hay información de genes importantes de ML para este GSE.</p>"
    
    # ================== HTML ==================
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TFM - Dashboard {gse_id}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 32px 16px;
            background: #f5f5f7;
            font-family: "Georgia", "Times New Roman", serif;
            color: #1f2933;
        }}
        .shell {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .hero {{
            background: #ffffff;
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: 0 8px 24px rgba(15,23,42,0.12);
            border: 1px solid #e5e7eb;
        }}
        .hero-title {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            font-size: 1.8rem;
            font-weight: 650;
            margin-bottom: 4px;
            color: #111827;
            text-align: center;
        }}
        .hero-subtitle {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            font-size: 0.95rem;
            color: #4b5563;
            margin-bottom: 2px;
            text-align: center;
        }}
        .hero-subtitle code {{
            font-family: "Fira Code", "Consolas", monospace;
            font-size: 0.85rem;
        }}
        .card-glass {{
            background: #ffffff;
            border-radius: 14px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 16px rgba(15,23,42,0.06);
        }}
        .card-header-glass {{
            border-radius: 14px 14px 0 0;
            border-bottom: 1px solid #e5e7eb;
            padding: 12px 18px;
            background: #f9fafb;
        }}
        .section-label {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #9ca3af;
            margin-bottom: 2px;
        }}
        .section-title-main {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            font-size: 1.02rem;
            font-weight: 600;
            color: #111827;
            border-bottom: 2px solid #2563eb;
            display: inline-block;
            padding-bottom: 2px;
        }}
        img.figure-img {{
            width: 100%;
            max-height: 380px;
            object-fit: contain;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
            background-color: #ffffff;
        }}
        .info-text {{
            white-space: pre-wrap;
            font-size: 0.97rem;
            line-height: 1.6;
            color: #111827;
        }}
        .info-text b {{
            color: #111827;
            font-weight: 600;
        }}
        code {{
            font-family: "Fira Code", "Consolas", monospace;
            font-size: 0.86rem;
            color: #111827;
            background-color: #f3f4f6;
            padding: 1px 4px;
            border-radius: 3px;
        }}
        .table {{
            color: #111827;
            font-size: 0.9rem;
        }}
        .table-striped > tbody > tr:nth-of-type(odd) {{
            background-color: #f9fafb;
        }}
        .table-hover tbody tr:hover {{
            background-color: #e5edf9;
        }}
        .table th, .table td {{
            text-align: left;
        }}
        .alert-footer {{
            background: #ffffff;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            font-size: 0.88rem;
            color: #374151;
            box-shadow: 0 4px 12px rgba(15,23,42,0.06);
        }}
        p {{
            color: #111827;
        }}
    </style>
</head>
<body>
<div class="shell">

    <!-- CABECERA -->
    <div class="hero">
        <div class="hero-title">
            Análisis transcriptómico de NSCLC
        </div>
        <div class="hero-subtitle">
            Panel de resultados para el estudio GEO <b>{gse_id}</b>
        </div>
        <div class="hero-subtitle">
            Modo de análisis: <b>{modo_texto}</b>
        </div>
        <div class="hero-subtitle mt-2">
            Carpeta de salida: <code>~/Desktop/TFM_{gse_id}</code>
        </div>
    </div>

    <!-- DESCRIPCIÓN DEL DATASET -->
    <div class="card card-glass mb-4">
        <div class="card-header card-header-glass">
            <div class="section-label">Descripción del dataset</div>
            <div class="section-title-main">Contexto del estudio GEO</div>
        </div>
        <div class="card-body">
            <p style="font-size:0.95rem;">
                {contexto_texto}
            </p>
            <p style="font-size:0.95rem;">
                El objetivo principal de este análisis es comparar los perfiles de expresión génica entre tejido
                tumoral y tejido no tumoral de pulmón, identificar genes diferencialmente expresados y evaluar
                hasta qué punto estos patrones permiten clasificar correctamente las muestras mediante modelos
                de aprendizaje automático supervisado.
            </p>
        </div>
    </div>

    <!-- GLOSARIO / AYUDA -->
    <div class="card card-glass mb-4">
        <div class="card-header card-header-glass">
            <div class="section-label">Ayuda para la interpretación</div>
            <div class="section-title-main">Glosario de términos estadísticos y de ML</div>
        </div>
        <div class="card-body">
            <ul style="font-size:0.95rem; padding-left: 1rem;">
                <li><b>Log2FC (Log-fold change).</b> Mide el cambio de expresión de un gen entre dos grupos en escala logarítmica base 2. 
                    Valores positivos indican sobreexpresión en tumor frente a normal; valores negativos, infraexpresión.</li>
                <li><b>p&nbsp;valor.</b> Probabilidad de observar un cambio de expresión igual o más extremo que el obtenido si en realidad 
                    no hubiera ninguna diferencia entre los grupos. Cuanto menor es el p&nbsp;valor, mayor evidencia hay de que el gen 
                    se expresa de forma distinta entre tumor y tejido normal.</li>
                <li><b>p&nbsp;valor ajustado / FDR.</b> Versión corregida del p&nbsp;valor que tiene en cuenta que se están analizando 
                    miles de genes a la vez. Controla la tasa de falsos positivos debidos a comparaciones múltiples. 
                    Valores de FDR bajos indican genes con cambios de expresión robustos.</li>
                <li><b>Exactitud (accuracy).</b> Proporción de muestras correctamente clasificadas por el modelo respecto al total 
                    de muestras analizadas.</li>
                <li><b>Sensibilidad (recall para la clase tumoral).</b> Proporción de muestras tumorales que el modelo identifica 
                    correctamente como tumor. Refleja la capacidad para detectar casos positivos.</li>
                <li><b>Especificidad.</b> Proporción de muestras normales que el modelo clasifica correctamente como normales. 
                    Refleja la capacidad para evitar falsos positivos.</li>
                <li><b>AUC (área bajo la curva ROC).</b> Mide la capacidad global del modelo para separar muestras tumorales 
                    de normales a distintos umbrales de decisión. Valores cercanos a 1 indican una separación muy buena; 
                    valores alrededor de 0.5 indican un comportamiento similar al azar.</li>
                <li><b>Coeficiente de regresión logística.</b> Indica cuánto cambia la probabilidad de que una muestra sea tumoral 
                    cuando aumenta la expresión de un gen. Coeficientes positivos implican que mayores niveles de expresión están 
                    asociados a mayor probabilidad de pertenecer al grupo tumoral.</li>
                <li><b>Importancia en Random Forest.</b> Estima cuánto contribuye cada gen a reducir el error de clasificación 
                    en un bosque aleatorio. Genes con importancia alta son especialmente útiles para distinguir entre tumor y normal.</li>
            </ul>
        </div>
    </div>

    <!-- FILA DE GRÁFICOS -->
    <div class="row g-4 mb-4">
        <div class="col-md-4">
            <div class="card card-glass">
                <div class="card-header card-header-glass">
                    <div class="section-label">Figura 1</div>
                    <div class="section-title-main">Análisis de componentes principales (PCA)</div>
                </div>
                <div class="card-body">
                    <a href="#" data-bs-toggle="modal" data-bs-target="#imageModal" data-bs-img="pca_plot.png" data-bs-title="PCA - {gse_id}">
                        <img src="pca_plot.png" alt="PCA" class="figure-img mb-3">
                    </a>
                    <p style="font-size:0.95rem;">
                        <b>Interpretación.</b> Cada punto representa una muestra, coloreada según su grupo (tumor vs normal).
                        Si las nubes de puntos están bien separadas a lo largo de PC1 o PC2, indica que el perfil global
                        de expresión distingue claramente entre ambos grupos. Si aparece mezcla, sugiere solapamiento
                        biológico o limitaciones en el diseño experimental.
                    </p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card card-glass">
                <div class="card-header card-header-glass">
                    <div class="section-label">Figura 2</div>
                    <div class="section-title-main">Volcano plot</div>
                </div>
                <div class="card-body">
                    <a href="#" data-bs-toggle="modal" data-bs-target="#imageModal" data-bs-img="volcano_plot.png" data-bs-title="Volcano plot - {gse_id}">
                        <img src="volcano_plot.png" alt="Volcano" class="figure-img mb-3">
                    </a>
                    <p style="font-size:0.95rem;">
                        <b>Interpretación.</b> En el eje X se representa el cambio de expresión (Log2FC) y en el eje Y la
                        significación estadística (-log<sub>10</sub> FDR). Los puntos alejados del centro y situados en la parte
                        superior corresponden a genes con cambios grandes y estadísticamente robustos. Una mayor concentración
                        de puntos en los extremos indica una señal biológica más intensa entre tejido tumoral y normal.
                    </p>
                    {"<p class='mt-2 mb-0' style='font-size:0.85rem;'><u>Nota.</u> En modo exploratorio, este gráfico puede no mostrar genes significativos.</p>" if not tiene_adj else ""}
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card card-glass">
                <div class="card-header card-header-glass">
                    <div class="section-label">Figura 3</div>
                    <div class="section-title-main">Heatmap de genes seleccionados</div>
                </div>
                <div class="card-body">
                    <a href="#" data-bs-toggle="modal" data-bs-target="#imageModal" data-bs-img="heatmap_final.png" data-bs-title="Heatmap - {gse_id}">
                        <img src="heatmap_final.png" alt="Heatmap" class="figure-img mb-3">
                    </a>
                    <p style="font-size:0.95rem;">
                        <b>Interpretación.</b> Cada fila corresponde a un gen y cada columna a una muestra. Los colores reflejan
                        niveles relativos de expresión. Bloques de color homogéneo y agrupación de columnas por grupo 
                        (tumor vs normal) indican la presencia de firmas de expresión coherentes entre muestras. La fragmentación
                        de los colores suele señalar heterogeneidad biológica o técnica.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- INTERPRETACIÓN INTEGRADA -->
    <div class="card card-glass mb-4">
      <div class="card-header card-header-glass">
        <div class="section-label">Interpretación integrada</div>
        <div class="section-title-main">Relación entre gráficos, genes y modelos de ML</div>
      </div>
      <div class="card-body">
        <p style="font-size:0.95rem;">
          Los genes que aparecen como significativos (FDR &lt; 0.05) en el análisis diferencial son los principales
          responsables de la separación observada en el PCA y de los puntos extremos del volcano plot. Además, los
          modelos de aprendizaje automático utilizan estos patrones de expresión para clasificar las muestras como
          tumorales o normales, otorgando mayor peso a los genes que mejor discriminan entre grupos.
        </p>
        <p style="font-size:0.95rem;">
          En particular, los genes listados en el <i>Top 20 según modelos de ML</i> representan una posible firma
          molecular de cáncer de pulmón, ya que combinan cambios de expresión relevantes con una alta contribución
          a la capacidad de clasificación del modelo.
        </p>
      </div>
    </div>

    <!-- INFORME BIOLÓGICO -->
    <div class="row g-4 mb-4">
        <div class="col-12">
            <div class="card card-glass">
                <div class="card-header card-header-glass">
                    <div class="section-label">Informe de interpretación</div>
                    <div class="section-title-main">Resumen biológico y discusión</div>
                </div>
                <div class="card-body">
                    <div class="info-text">{informe_html}</div>
                </div>
            </div>
        </div>
    </div>

    <!-- TABLA DE GENES -->
    <div class="row g-4 mb-4">
        <div class="col-12">
            <div class="card card-glass">
                <div class="card-header card-header-glass">
                    <div class="section-label">Genes de interés</div>
                    <div class="section-title-main">{tabla_titulo}</div>
                </div>
                <div class="card-body table-responsive">
                    {tabla_html}
                </div>
            </div>
        </div>
    </div>

    <!-- RESULTADOS DE ML -->
    <div class="row g-4 mb-4">
        <div class="col-12">
            <div class="card card-glass">
                <div class="card-header card-header-glass">
                    <div class="section-label">Modelos de clasificación</div>
                    <div class="section-title-main">Resultados de aprendizaje automático</div>
                </div>
                <div class="card-body table-responsive">
                    <p style="font-size:0.95rem;">
                        Se evaluaron modelos supervisados (regresión logística, Random Forest y SVM lineal) para 
                        clasificar tejido tumoral frente a tejido normal a partir de los perfiles de expresión génica.
                    </p>
                    {tabla_ml_html}
                </div>
            </div>
        </div>
    </div>
"""

    # TOP 20 GENES ML
    if tabla_top20_html:
        html += f"""
    <div class="row g-4 mb-4">
        <div class="col-12">
            <div class="card card-glass">
                <div class="card-header card-header-glass">
                    <div class="section-label">Importancia por ML</div>
                    <div class="section-title-main">Top 20 genes según modelos de ML</div>
                </div>
                <div class="card-body table-responsive">
                    <p style="font-size:0.95rem;">
                        Genes ordenados por el valor absoluto del coeficiente en la regresión logística. 
                        Valores positivos indican sobreexpresión relativa en muestras tumorales.
                    </p>
                    {tabla_top20_html}
                </div>
            </div>
        </div>
    </div>
"""

    # MODAL PARA IMÁGENES
    html += """
<div class="modal fade" id="imageModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-xl modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header border-0">
        <h5 class="modal-title" id="imageModalLabel">Figura</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
      </div>
      <div class="modal-body text-center">
        <img id="imageModalImg" src="" alt="Figura ampliada" style="max-width: 100%; max-height: 80vh; object-fit: contain; border-radius: 12px;">
      </div>
    </div>
  </div>
</div>

<script>
const imageModal = document.getElementById('imageModal');
if (imageModal) {
  imageModal.addEventListener('show.bs.modal', event => {
    const button = event.relatedTarget;
    const imgSrc = button.getAttribute('data-bs-img');
    const title = button.getAttribute('data-bs-title') || 'Figura';
    const modalImg = imageModal.querySelector('#imageModalImg');
    const modalTitle = imageModal.querySelector('#imageModalLabel');
    modalImg.src = imgSrc;
    modalTitle.textContent = title;
  });
}
</script>
"""

    # FOOTER
    html += f"""
    <div class="alert alert-footer mt-4">
        <b>Archivos generados:</b>
        <code>matriz_normalizada.csv</code>,
        <code>metadata_procesada.csv</code>,
        <code>resultados_completos.csv</code>,
        <code>pca_plot.png</code>,
        <code>volcano_plot.png</code>,
        <code>heatmap_final.png</code>,
        <code>informe_biologico.txt</code>,
        <code>resultados_ml.csv</code>,
        <code>genes_importantes_ml_{gse_id}.csv</code>,
        <code>top20_genes_ml_{gse_id}.csv</code>.
    </div>

</div>
</body>
</html>
    """
    
    out_path = os.path.join(base_path, f"DASHBOARD_{gse_id}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Dashboard generado: {out_path}")