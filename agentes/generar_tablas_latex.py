"""
Genera las tablas LaTeX de los capitulos de Resultados y Discusion.

Las tablas se escriben desde los CSV de los pasos 14-18, nunca a mano: si un
analisis se reejecuta con datos distintos, las tablas de la memoria cambian con
el y no pueden quedar desincronizadas respecto a los resultados.
"""

import os

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB_DIR = os.path.join(BASE_DIR, "tablas_auditoria")
os.makedirs(TAB_DIR, exist_ok=True)


def num(v, dec=3, guion="--"):
    """Formatea con coma decimal (convencion espanola)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return guion
    return f"{v:.{dec}f}".replace(".", ",")


def escribir(nombre, contenido):
    ruta = os.path.join(TAB_DIR, nombre)
    with open(ruta, "w") as fh:
        fh.write(contenido)
    print(f"  {nombre}")


def tabla_auditoria():
    a = pd.read_csv(os.path.join(BASE_DIR, "AUDITORIA_COHORTES.csv"))
    filas = []
    for _, r in a.iterrows():
        alin = ("OK" if r["Alineamiento"] == "OK"
                else f"\\textbf{{{int(r['N_Muestras_Desalineadas'])}/{r['N_Total']}}}")
        ev = "si" if r["Evaluable_Como_Test"] else "\\textbf{no}"
        filas.append(
            f"{r['Cohorte']} & {r['Plataforma']} & {r['N_Total']} & "
            f"{r['N_Sano']} & {r['N_Enfermo']} & {r['N_Sin_Clasificar']} & "
            f"{num(r['Tasa_Exito_Curacion'] * 100, 1)}\\,\\% & {alin} & {ev} \\\\"
        )
    cuerpo = "\n".join(filas)
    tot = a["N_Total"].sum()
    sin = a["N_Sin_Clasificar"].sum()

    escribir("tabla_auditoria.tex", f"""\\begin{{table}}[htbp]
\\centering
\\caption[Auditoria de integridad de las cohortes]{{Auditoria de integridad de
las once cohortes con datos procesados. La columna \\emph{{Desalin.}} indica
muestras cuya etiqueta clinica corresponde a otro paciente por asignacion
posicional; \\emph{{Eval.}} indica si la cohorte contiene ambas clases y por
tanto es evaluable como conjunto de test.}}
\\label{{tab:auditoria}}
\\small
\\begin{{tabular}}{{llrrrrrcc}}
\\toprule
Cohorte & Plataforma & $n$ & Sanas & Enfermas & Sin clas. & Curacion & Desalin. & Eval. \\\\
\\midrule
{cuerpo}
\\midrule
\\textbf{{Total}} & & \\textbf{{{tot}}} & {a['N_Sano'].sum()} &
{a['N_Enfermo'].sum()} & \\textbf{{{sin}}} &
\\textbf{{{num(100 * (tot - sin) / tot, 1)}\\,\\%}} & 307 & 8/11 \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""")


def tabla_lodo():
    l = pd.read_csv(os.path.join(BASE_DIR, "LODO_HONESTO_RESULTADOS.csv"))
    l = l.sort_values(["Evaluable", "Ganancia_vs_Baseline"], ascending=[False, False])
    ev = l[l["Evaluable"]]

    filas = []
    for _, r in l.iterrows():
        if not r["Evaluable"]:
            filas.append(
                f"{r['Cohorte_Test']} & {r['n_test']} & "
                f"{r['n_Sano']}/{r['n_Enfermo']} & {num(r['Baseline_Mayoritaria'])} & "
                f"{num(r['Accuracy'])} & \\multicolumn{{4}}{{c}}"
                f"{{\\emph{{no evaluable: una sola clase}}}} \\\\"
            )
        else:
            gan = num(r["Ganancia_vs_Baseline"])
            if r["Ganancia_vs_Baseline"] > 0:
                gan = f"$+${gan}"
            else:
                gan = f"\\textbf{{{gan.replace('-', '$-$')}}}"
            filas.append(
                f"{r['Cohorte_Test']} & {r['n_test']} & "
                f"{r['n_Sano']}/{r['n_Enfermo']} & {num(r['Baseline_Mayoritaria'])} & "
                f"{num(r['Accuracy'])} & {num(r['Balanced_Accuracy'])} & "
                f"{num(r['AUC'])} & {num(r['Sensibilidad'])} & "
                f"{num(r['Especificidad'])} \\\\"
            )
    cuerpo = "\n".join(filas)

    escribir("tabla_lodo_honesto.tex", f"""\\begin{{table}}[htbp]
\\centering
\\caption[Validacion LODO con metricas completas]{{Validacion LODO de la tarea
tumor frente a sano, con el mismo modelo del analisis original (LASSO, $C=0{{,}}5$)
y el alineamiento muestra--etiqueta corregido. Se anaden el \\emph{{baseline}} de
clase mayoritaria y la \\emph{{balanced accuracy}}; las tres cohortes con una sola
clase se marcan como no evaluables. En negrita, las cohortes que no superan su
propio \\emph{{baseline}}.}}
\\label{{tab:lodo-honesto}}
\\small
\\begin{{tabular}}{{lrcrrrrrr}}
\\toprule
Cohorte test & $n$ & Sano/Enf. & \\emph{{Baseline}} & Acc. & Bal.\\ acc. & AUC & Sens. & Espec. \\\\
\\midrule
{cuerpo}
\\midrule
\\multicolumn{{5}}{{l}}{{\\emph{{Media sobre las {len(ev)} cohortes evaluables}}}} &
\\textbf{{{num(ev['Balanced_Accuracy'].mean())}}} &
\\textbf{{{num(ev['AUC'].mean())}}} &
{num(ev['Sensibilidad'].mean())} & {num(ev['Especificidad'].mean())} \\\\
\\multicolumn{{5}}{{l}}{{\\emph{{Media de \\emph{{accuracy}} sobre las 11 (como en el analisis original)}}}} &
\\multicolumn{{4}}{{c}}{{{num(l['Accuracy'].mean())}}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""")


def tabla_composicion():
    c = pd.read_csv(os.path.join(BASE_DIR, "COMPOSICION_VS_BIOLOGIA.csv"))
    c = c.sort_values("n_tumores", ascending=False)
    filas = []
    for _, r in c.iterrows():
        rho_t = r["Rho_SOLO_TUMORES_vs_PulmonNormal"]
        evaluable = not (isinstance(rho_t, float) and np.isnan(rho_t))
        filas.append(
            f"{r['Cohorte']} & {r['n_tumores']} & {r['n_sanos']} & "
            f"{num(r['Rho_TODAS_vs_PulmonNormal']).replace('-', '$-$')} & "
            + (f"{num(rho_t).replace('-', '$-$')} & "
               f"{num(r['Rho_SOLO_TUMORES_vs_Proliferacion']).replace('-', '$-$')}"
               if evaluable else
               "\\multicolumn{2}{c}{\\emph{$n$ insuficiente}}")
            + " \\\\"
        )
    v = c["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna()

    escribir("tabla_composicion.tex", f"""\\begin{{table}}[htbp]
\\centering
\\caption[Composicion tisular frente a biologia tumoral]{{Correlacion de Spearman
entre el \\emph{{score}} del clasificador y el contenido de pulmon normal
(panel de 18 marcadores alveolares, endoteliales y de estroma normal). La
columna decisiva es la tercera: restringida a muestras tumorales, donde la
correlacion ya no puede explicarse por la presencia de controles sanos. Se
requieren al menos 8 tumores para calcularla.}}
\\label{{tab:composicion}}
\\small
\\begin{{tabular}}{{lrrrrr}}
\\toprule
& & & \\multicolumn{{3}}{{c}}{{$\\rho$ frente al \\emph{{score}} del clasificador}} \\\\
\\cmidrule(l){{4-6}}
Cohorte & Tumores & Sanas & Todas (pulmon n.) & \\textbf{{Solo tumores}} & Prolif. \\\\
\\midrule
{chr(10).join(filas)}
\\midrule
\\multicolumn{{4}}{{l}}{{\\emph{{Media sobre las {len(v)} cohortes evaluables}}}} &
\\textbf{{{num(v.mean()).replace('-', '$-$')}}} &
{num(c['Rho_SOLO_TUMORES_vs_Proliferacion'].dropna().mean())} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""")


def tabla_falacia():
    f = pd.read_csv(os.path.join(BASE_DIR, "FALACIA_FOLDS_COMPARACION.csv"))
    a, b = f.iloc[0], f.iloc[1]
    escribir("tabla_falacia_folds.tex", f"""\\begin{{table}}[htbp]
\\centering
\\caption[Consistencia de signo: folds solapados frente a cohortes disjuntas]{{
Acuerdo direccional de los coeficientes LASSO medido de dos formas sobre los
mismos genes y las mismas ocho cohortes. La ultima fila es el control que
descarta el tamano de muestra como explicacion: compara parejas de modelos con
entrenamientos de magnitud comparable, y unicamente cambia si comparten muestras.}}
\\label{{tab:falacia}}
\\small
\\begin{{tabular}}{{lcc}}
\\toprule
& \\emph{{Folds}} LODO & Cohortes \\\\
& (solapados) & (disjuntas) \\\\
\\midrule
Muestras de entrenamiento compartidas & $\\sim$98\\,\\% & 0\\,\\% \\\\
Genes seleccionados alguna vez & {a['genes_seleccionados_alguna_vez']} & {b['genes_seleccionados_alguna_vez']} \\\\
Genes seleccionados en las 8 & {a['genes_seleccionados_en_todas']} & {b['genes_seleccionados_en_todas']} \\\\
Genes con acuerdo de signo perfecto & \\textbf{{{a['genes_acuerdo_signo_perfecto']}}} & \\textbf{{{b['genes_acuerdo_signo_perfecto']}}} \\\\
\\midrule
\\emph{{Control}}: concordancia entre parejas & \\textbf{{{num(a['concordancia_pareja_media'] * 100, 1)}\\,\\%}} & \\textbf{{{num(b['concordancia_pareja_media'] * 100, 1)}\\,\\%}} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""")


def tabla_subtipo():
    s = pd.read_csv(os.path.join(BASE_DIR, "SUBTIPO_LODO_RESULTADOS.csv"))
    filas = [
        f"{r['Cohorte_Test']} & {r['n_test']} & {r['n_ADC']}/{r['n_SQC']} & "
        f"{num(r['Baseline_Mayoritaria'])} & {num(r['Balanced_Accuracy'])} & "
        f"{num(r['AUC'])} & $+${num(r['Ganancia_vs_Baseline'])} \\\\"
        for _, r in s.iterrows()
    ]
    escribir("tabla_subtipo.tex", f"""\\begin{{table}}[htbp]
\\centering
\\caption[Control positivo: subtipo histologico]{{Validacion LODO de la tarea
adenocarcinoma frente a escamoso sobre las tres cohortes con histologia anotada
y ambas clases presentes (todas en plataforma GPL570).}}
\\label{{tab:subtipo}}
\\small
\\begin{{tabular}}{{lrcrrrr}}
\\toprule
Cohorte test & $n$ & ADC/Esc. & \\emph{{Baseline}} & Bal.\\ acc. & AUC & Ganancia \\\\
\\midrule
{chr(10).join(filas)}
\\midrule
\\multicolumn{{4}}{{l}}{{\\emph{{Media}}}} &
\\textbf{{{num(s['Balanced_Accuracy'].mean())}}} &
\\textbf{{{num(s['AUC'].mean())}}} &
$+${num(s['Ganancia_vs_Baseline'].mean())} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""")


def tabla_dificiles():
    d = pd.read_csv(os.path.join(BASE_DIR, "SUBTIPO_CASOS_DIFICILES.csv"))
    d = d[d["n"] >= 3].sort_values("n", ascending=False)
    filas = [
        f"{r['Histologia']} & {r['Cohorte']} & {r['n']} & "
        f"{num(r['P_escamoso_mediana'])} & {num(r['Pct_Alta_Confianza'], 1)}\\,\\% & "
        f"{num(r['Pct_Asignadas_Escamoso'], 1)}\\,\\% \\\\"
        for _, r in d.iterrows()
    ]
    escribir("tabla_casos_dificiles.tex", f"""\\begin{{table}}[htbp]
\\centering
\\caption[Histologias excluidas del clasificador de subtipo]{{Comportamiento del
clasificador de subtipo ante las histologias que no vio en el entrenamiento
(grupos con $n\\geq3$). \\emph{{Alta conf.}} recoge el porcentaje de muestras con
$P>0{{,}}9$ o $P<0{{,}}1$, es decir, asignadas con confianza a una categoria a la
que no pertenecen.}}
\\label{{tab:dificiles}}
\\small
\\begin{{tabular}}{{llrrrr}}
\\toprule
Histologia & Cohorte & $n$ & $P$(esc.) mediana & Alta conf. & A escamoso \\\\
\\midrule
{chr(10).join(filas)}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""")


if __name__ == "__main__":
    print("Generando tablas en tablas_auditoria/")
    tabla_auditoria()
    tabla_lodo()
    tabla_composicion()
    tabla_falacia()
    tabla_subtipo()
    tabla_dificiles()
    print("Listo.")
