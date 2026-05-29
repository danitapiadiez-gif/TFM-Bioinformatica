import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from sklearn.decomposition import PCA
import numpy as np


def generar_graficos(gse_id):
    """
    PASO 5: Genera PCA, volcano (si hay diferencial) y heatmap.
    Funciona en modo exploratorio si no hay adj_pvalue o no hay genes significativos.
    """
    print(f"\n---  PASO 5: GENERANDO SET DE GRÁFICOS ({gse_id}) ---")
    base_path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    
    # 1. Cargar datos
    try:
        df_norm = pd.read_csv(os.path.join(base_path, "matriz_normalizada.csv"), index_col=0)
        meta = pd.read_csv(os.path.join(base_path, "metadata_procesada.csv"), index_col=0)
    except Exception as e:
        print(f" Error al cargar matriz/metadata: {e}")
        return
    
    # Intentar cargar resultados
    try:
        resultados = pd.read_csv(os.path.join(base_path, "resultados_completos.csv"))
        tiene_adj = 'adj_pvalue' in resultados.columns and len(resultados) > 0
    except Exception as e:
        print(f" No se pudo cargar resultados_completos.csv: {e}")
        resultados = pd.DataFrame()
        tiene_adj = False
    
    print(f" Modo gráfico: {'Diferencial' if tiene_adj else 'Exploratorio'}")
    
    # --- PCA ---
    print("[1/3] Generando PCA...")
    pca = PCA(n_components=2)
    comps = pca.fit_transform(df_norm.T.fillna(0))
    pca_df = pd.DataFrame(comps, columns=['PC1', 'PC2'], index=df_norm.columns)
    
    if 'grupo_analisis' in meta.columns:
        pca_df['grupo_analisis'] = meta.loc[pca_df.index, 'grupo_analisis']
    else:
        pca_df['grupo_analisis'] = 'Grupo único'
    
    plt.figure(figsize=(10, 7))
    sns.scatterplot(data=pca_df, x='PC1', y='PC2', hue='grupo_analisis', s=100)
    plt.title(f'PCA - {gse_id}')
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, "pca_plot.png"), dpi=300)
    plt.close()
    
    # --- VOLCANO ---
    print("[2/3] Generando Volcano Plot...")
    if tiene_adj and not resultados.empty:
        try:
            plt.figure(figsize=(10, 7))
            resultados = resultados.dropna(subset=['adj_pvalue', 'LogFC'])
            resultados['-log10FDR'] = -np.log10(resultados['adj_pvalue'].clip(lower=1e-300))
            
            # UMBRALES (ajustados)
            fdr_thr = 0.05
            lfc_thr = 0.5  # antes 1.0; ahora más sensible
            
            sig_up = (resultados['adj_pvalue'] < fdr_thr) & (resultados['LogFC'] > lfc_thr)
            sig_down = (resultados['adj_pvalue'] < fdr_thr) & (resultados['LogFC'] < -lfc_thr)
            
            # nube gris de fondo
            plt.scatter(resultados['LogFC'], resultados['-log10FDR'], 
                        c='lightgrey', alpha=0.5, s=10, label='No significativo')
            
            # puntos up/down si los hay
            if sig_up.any():
                plt.scatter(resultados.loc[sig_up, 'LogFC'], resultados.loc[sig_up, '-log10FDR'],
                            c='red', s=30, alpha=0.8, label='Up (FDR<0.05, |LogFC|>0.5)')
            if sig_down.any():
                plt.scatter(resultados.loc[sig_down, 'LogFC'], resultados.loc[sig_down, '-log10FDR'],
                            c='blue', s=30, alpha=0.8, label='Down (FDR<0.05, |LogFC|>0.5)')
            
            plt.axhline(-np.log10(fdr_thr), color='black', linestyle='--', alpha=0.5)
            plt.axvline(lfc_thr, color='black', linestyle='--', alpha=0.5)
            plt.axvline(-lfc_thr, color='black', linestyle='--', alpha=0.5)
            
            plt.title(f'Volcano Plot (FDR) - {gse_id}')
            plt.xlabel('Log2 Fold Change')
            plt.ylabel('-log10(FDR)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(base_path, "volcano_plot.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f" Error generando volcano: {e}")
    else:
        print("⏭ Saltando volcano (no hay adj_pvalue o resultados vacíos).")
    
    # --- HEATMAP ---
    print("[3/3] Generando Heatmap...")
    try:
        if tiene_adj and not resultados.empty:
            # Top 50 genes más significativos por FDR
            top_genes = resultados.sort_values('adj_pvalue').head(50)['GENE_SYMBOL'].values
            data_sub = df_norm.loc[df_norm.index.intersection(top_genes)]
        else:
            # Exploratorio: top 50 genes por varianza
            varianza = df_norm.var(axis=1).sort_values(ascending=False)
            top_genes = varianza.head(50).index
            data_sub = df_norm.loc[top_genes]
        
        if data_sub.empty:
            print(" No hay datos para heatmap.")
            return
        
        # Z-score por gen
        data_z = data_sub.apply(lambda x: (x - x.mean()) / (x.std() + 1e-8), axis=1)
        
        # Colores por grupo si hay
        if 'grupo_analisis' in meta.columns:
            grupos = meta.loc[data_z.columns, 'grupo_analisis'].astype('category')
            codigos = grupos.cat.codes
            palette = sns.color_palette("Set2", len(codigos.unique()))
            mapping = dict(zip(sorted(codigos.unique()), palette))
            col_colors = codigos.map(mapping)
        else:
            col_colors = None
        
        g = sns.clustermap(data_z, cmap='RdYlBu_r', col_colors=col_colors,
                           figsize=(12, 12), yticklabels=True, xticklabels=False, center=0)
        g.savefig(os.path.join(base_path, "heatmap_final.png"), dpi=300)
        plt.close()
        
        print(f" Los 3 gráficos han sido guardados en la carpeta de {gse_id}")
    except Exception as e:
        print(f" Error generando heatmap: {e}")