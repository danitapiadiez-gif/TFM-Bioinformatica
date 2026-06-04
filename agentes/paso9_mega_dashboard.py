import pandas as pd
import os
import json
from groq import Groq
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_PATH = os.path.expanduser("~/Desktop")

def generar_dashboard_consenso():
    print(f"\n{'='*80}")
    print(f" PASO 9: GENERANDO DASHBOARD DE CONSENSO ESTADÍSTICO (v8.0)")
    print(f"{'='*80}")
    
    ruta_csv = os.path.join(BASE_PATH, "BIOMARCADORES_UNIVERSALES_CANCER_PULMON.csv")
    if not os.path.exists(ruta_csv):
        print(" Error: No se encuentra el archivo de meta-análisis.")
        return
        
    df = pd.read_csv(ruta_csv, index_col=0)
    
    # NUEVA LÓGICA: Ordenar por impacto biológico (LogFC absoluto) para que la gráfica tenga "textura"
    # Tomamos los 50 genes que aparecen en más estudios, y de esos, los ordenamos por magnitud
    df['Abs_LogFC'] = df['LogFC_Medio'].abs()
    genes_grafica = df.sort_values(by=['Num_Estudios', 'Abs_LogFC'], ascending=[False, False]).head(50)
    
    top_genes_ia = df.head(15) 
    
    # Extraer nombres de estudios
    estudios = [c for c in df.columns if c.startswith('GSE')]
    
    print(f" -> Generando interpretaciones funcionales para el TOP 15...")
    lista_genes_str = ", ".join(top_genes_ia.index.tolist())
    
    prompt = f"""
Eres un Bioinformático Clínico. Has identificado estos 15 genes como los biomarcadores más robustos en cáncer de pulmón:
{lista_genes_str}

TU TAREA:
1. Clasifica cada gen en una categoría funcional (Metástasis, Ciclo Celular, Inmunidad, etc.).
2. Explica brevemente por qué su presencia consistente en múltiples estudios es relevante.

RESPONDE SOLO EN JSON:
{{
  "genes": [
    {{"symbol": "GEN", "cat": "Categoría", "desc": "Explicación..."}},
    ...
  ]
}}
"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0, 
            response_format={"type": "json_object"}
        )
        info_ia = json.loads(completion.choices[0].message.content)
    except:
        info_ia = {"genes": [{"symbol": g, "cat": "General", "desc": "Análisis no disponible"} for g in top_genes_ia.index]}

    # --- HTML DETERMINISTA ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Consensus Biomarker Suite</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f1f5f9; }}
            .mono {{ font-family: 'JetBrains Mono', monospace; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .tab-btn.active {{ border-bottom: 2px solid #38bdf8; color: #38bdf8; }}
            .glass {{ background: rgba(30, 41, 59, 0.5); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.05); }}
            .heatmap-cell {{ 
                width: 40px; height: 40px; border-radius: 6px; 
                display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold;
            }}
        </style>
    </head>
    <body class="p-10">
        <div class="max-w-6xl mx-auto">
            <header class="mb-16 border-l-4 border-sky-500 pl-8">
                <h1 class="text-4xl font-black tracking-tighter uppercase">Consensus <span class="text-sky-400">Intelligence</span></h1>
                <p class="text-slate-500 font-medium tracking-widest text-xs mt-2">Módulo de Validación Multi-Cohorte v8.0</p>
            </header>

            <nav class="flex space-x-12 mb-12 border-b border-slate-800">
                <button onclick="openTab('tab-stats')" class="tab-btn active pb-4 font-bold text-xs uppercase tracking-widest transition">01. Magnitud del Impacto</button>
                <button onclick="openTab('tab-matrix')" class="tab-btn pb-4 font-bold text-xs uppercase tracking-widest transition text-slate-500">02. Matriz de LogFC</button>
                <button onclick="openTab('tab-desc')" class="tab-btn pb-4 font-bold text-xs uppercase tracking-widest transition text-slate-500">03. Perfil Funcional</button>
            </nav>

            <!-- TAB 1: GRÁFICOS DE ROBUSTEZ -->
            <div id="tab-stats" class="tab-content active">
                <div class="grid grid-cols-1 gap-8">
                    <div class="glass p-8 rounded-3xl">
                        <div class="flex justify-between items-center mb-8">
                            <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest">Fuerza de la Señal Biológica (TOP 50 Consistentes)</h3>
                            <span class="text-[10px] bg-slate-800 px-3 py-1 rounded-full text-slate-500 font-bold uppercase tracking-tighter">Log2 Fold Change Medio</span>
                        </div>
                        <div style="height: 800px; position: relative;">
                            <canvas id="freqChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 2: MATRIZ DE LOGFC -->
            <div id="tab-matrix" class="tab-content">
                <div class="glass p-10 rounded-3xl overflow-x-auto">
                    <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-8 text-center">Consistencia Direccional de la Firma (TOP 20)</h3>
                    <table class="mx-auto">
                        <thead>
                            <tr>
                                <th class="p-4 text-left text-[10px] text-slate-600">GEN</th>
                                {"".join([f'<th class="p-4 text-center text-[10px] text-slate-600 italic">{e}</th>' for e in estudios])}
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Mostramos los 20 mejores en la matriz para que sea legible
    for gen, row in df.head(20).iterrows():
        html_content += f"""
                            <tr>
                                <td class="p-4 font-bold text-sm border-r border-slate-800">{gen}</td>
        """
        for est in estudios:
            val = row[est]
            if pd.isna(val):
                html_content += '<td class="p-2"><div class="heatmap-cell bg-slate-900/50 text-slate-800">-</div></td>'
            else:
                color = "bg-rose-500/80" if val > 0 else "bg-blue-500/80"
                shadow = "shadow-[0_0_15px_rgba(244,63,94,0.3)]" if val > 0 else "shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                html_content += f'<td class="p-2"><div class="heatmap-cell {color} {shadow} text-white">{val:+.1f}</div></td>'
        html_content += "</tr>"

    html_content += """
                        </tbody>
                    </table>
                    <div class="mt-12 flex justify-center space-x-8 text-[10px] font-bold uppercase tracking-widest">
                        <div class="flex items-center"><div class="w-3 h-3 bg-rose-500 mr-2 rounded"></div> Sobre-expresión (UP)</div>
                        <div class="flex items-center"><div class="w-3 h-3 bg-blue-500 mr-2 rounded"></div> Infra-expresión (DOWN)</div>
                    </div>
                </div>
            </div>

            <!-- TAB 3: PERFILES -->
            <div id="tab-desc" class="tab-content">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    """
    
    for g in info_ia['genes']:
        html_content += f"""
                    <div class="glass p-8 rounded-2xl border-t-2 border-sky-500/30">
                        <div class="flex justify-between items-start mb-6">
                            <span class="text-2xl font-black italic">{g['symbol']}</span>
                            <span class="text-[8px] bg-sky-500/10 text-sky-400 px-2 py-1 rounded font-bold uppercase tracking-widest">{g['cat']}</span>
                        </div>
                        <p class="text-xs text-slate-400 leading-relaxed italic">"{g['desc']}"</p>
                    </div>
        """

    html_content += f"""
                </div>
            </div>

            <footer class="mt-32 pb-12 text-center text-slate-700 text-[9px] font-bold uppercase tracking-[0.5em]">
                TFM • Framework de Validación Determinista • 2024
            </footer>
        </div>

        <script>
            function openTab(tabId) {{
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
                event.currentTarget.classList.add('active');
            }}

            // Gráfico de Magnitud (LogFC Medio)
            const ctxFreq = document.getElementById('freqChart').getContext('2d');
            const dataLabels = {json.dumps(genes_grafica.index.tolist())};
            const dataValues = {json.dumps(genes_grafica['LogFC_Medio'].tolist())};
            
            // Colores dinámicos: Rojo para UP, Azul para DOWN
            const colors = dataValues.map(v => v > 0 ? 'rgba(244, 63, 94, 0.8)' : 'rgba(59, 130, 246, 0.8)');
            const borderColors = dataValues.map(v => v > 0 ? '#fb7185' : '#60a5fa');

            new Chart(ctxFreq, {{
                type: 'bar',
                data: {{
                    labels: dataLabels,
                    datasets: [{{
                        label: 'LogFC Medio',
                        data: dataValues,
                        backgroundColor: colors,
                        borderColor: borderColors,
                        borderWidth: 1,
                        borderRadius: 4,
                        barThickness: 12
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ 
                            grid: {{ color: '#1e293b', drawBorder: false }}, 
                            ticks: {{ color: '#94a3b8', font: {{ size: 10, weight: '600' }} }} 
                        }},
                        x: {{ 
                            grid: {{ color: '#1e293b' }}, 
                            ticks: {{ color: '#64748b' }},
                            title: {{ display: true, text: 'Magnitud del Cambio (Log2 Fold Change)', color: '#475569', font: {{ size: 10 }} }}
                        }}
                    }},
                    plugins: {{ 
                        legend: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return ' LogFC: ' + context.raw.toFixed(2);
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    ruta_html = os.path.join(BASE_PATH, "MEGA_DASHBOARD_CONSENSO_PULMON.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n  DASHBOARD DE CONSENSO ACTUALIZADO (Métrica de Magnitud): {ruta_html}")

if __name__ == "__main__":
    generar_dashboard_consenso()
