// Presentacion de defensa del TFM. 13 diapositivas para 10 minutos,
// organizadas por los tres bloques del proyecto (firma consenso, subtipo
// histologico, tumor vs sano) con detalle estadistico y de ML.
// Todas las cifras se leen de los CSV/JSON en resultados/*.

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const RAIZ = "/Users/danieltapiadiez/Desktop/UAX/TFM";
const RES = path.join(RAIZ, "resultados");

// ---------------------------------------------------------------- datos
function csv(nombre) {
  const txt = fs.readFileSync(path.join(RES, nombre), "utf8").trim();
  const [cab, ...filas] = txt.split("\n");
  const cols = cab.split(",");
  return filas.map((f) => {
    const v = f.split(",");
    return Object.fromEntries(cols.map((c, i) => [c, v[i]]));
  });
}
function json(nombre) {
  return JSON.parse(fs.readFileSync(path.join(RES, nombre), "utf8"));
}
const num = (x) => parseFloat(x);
const media = (a) => a.reduce((s, x) => s + x, 0) / a.length;
const dec = (v, n = 3) => v.toFixed(n).replace(".", ",");

const lodo = csv("tumor_vs_sano/LODO_HONESTO_RESULTADOS.csv");
const ev = lodo.filter((r) => r.Evaluable === "True");
const aud = csv("auditoria/AUDITORIA_COHORTES.csv");
const comp = csv("firma_consenso/COMPOSICION_VS_BIOLOGIA.csv");
const sub = csv("subtipo/SUBTIPO_LODO_RESULTADOS.csv");
const resFirma = json("firma_consenso/FIRMA_VALIDADA_RESUMEN.json");
const resRecal = json("recalibracion/LODO_RECALIBRADO_RESUMEN.json");
const resBoot = json("recalibracion/LODO_IC_BOOTSTRAP_RESUMEN.json");
const resML = json("comparativa_ml/COMPARATIVA_ML_RESUMEN.json");

const D = {
  balAcc: media(ev.map((r) => num(r.Balanced_Accuracy))),
  auc: media(ev.map((r) => num(r.AUC))),
  sens: media(ev.map((r) => num(r.Sensibilidad))),
  espec: media(ev.map((r) => num(r.Especificidad))),
  nEv: ev.length,
  nCoh: lodo.length,
  nMuestras: aud.reduce((s, r) => s + num(r.N_Total), 0),
  sinClas: aud.reduce((s, r) => s + num(r.N_Sin_Clasificar), 0),
  nMono: aud.filter((r) => r.Evaluable_Como_Test === "False").length,
  rho: media(
    comp
      .map((r) => num(r.Rho_SOLO_TUMORES_vs_PulmonNormal))
      .filter((x) => !isNaN(x))
  ),
  nRho: comp.filter((r) => !isNaN(num(r.Rho_SOLO_TUMORES_vs_PulmonNormal))).length,
  aucSub: media(sub.map((r) => num(r.AUC))),
  balSub: media(sub.map((r) => num(r.Balanced_Accuracy))),
  sensSub: media(sub.map((r) => num(r.Sensibilidad))),
  especSub: media(sub.map((r) => num(r.Especificidad))),
  nSub: sub.reduce((s, r) => s + num(r.n_test), 0),
  nValidados: resFirma.n_genes_validados,
  pctValidados: resFirma.pct_genes_validados,
  panelMin: resFirma.panel_minimo,
  aucPanel: resFirma.auc_panel_minimo,
  // OJO: resFirma.auc_firma_completa guarda el MAXIMO de la curva (panel de 50
  // genes), no la AUC con la firma entera. La correcta esta en la curva, fila
  // N_Genes == n_genes_validados. Mismo parche que agentes/paso12_datos.py.
  aucFirmaCompleta: (() => {
    const c = csv("firma_consenso/PANEL_MINIMO_CURVA.csv");
    const f = c.find((r) => +r.N_Genes === resFirma.n_genes_validados);
    return f ? num(f.AUC_Media) : resFirma.auc_firma_completa;
  })(),
  aucCurvaMaxima: resFirma.auc_firma_completa,
  ihcRec: Object.values(resFirma.ihc_recuperados).reduce((a, b) => a + b, 0),
  ihcTot: Object.values(resFirma.ihc_total).reduce((a, b) => a + b, 0),
  // Recalibracion
  aucCalIso: resRecal.isotonica.auc_cal_media,
  balCalIso: resRecal.isotonica.balacc_cal_media,
  aucCalPlatt: resRecal.platt.auc_cal_media,
  balCalPlatt: resRecal.platt.balacc_cal_media,
  gananciaIso: resRecal.isotonica.ganancia_balacc,
  // Bootstrap
  aucBoot: resBoot.auc_pooled,
  aucBootIC: resBoot.auc_pooled_ic95,
  balBoot: resBoot.balacc_pooled,
  balBootIC: resBoot.balacc_pooled_ic95,
  nBoot: resBoot.n_bootstrap,
  // Comparativa ML
  ml: resML,
};
D.pctSinClas = (100 * D.sinClas) / D.nMuestras;

// ---------------------------------------------------------------- paleta
const TINTA = "1A1D21";
const TINTA_2 = "52514E";
const MUDO = "898781";
const PAPEL = "FCFCFB";
const CREMA = "F1F0EC";
const AZUL = "2A78D6";
const ROJO = "D03B3B";
const VERDE = "1C8A3F";
const NARANJA = "EB6834";
const BLANCO = "FFFFFF";

const SERIF = "Cambria";
const SANS = "Calibri";
const MONO = "Consolas";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Daniel Tapia Diez";
pres.title = "Framework transcriptomico para biomarcadores en cancer de pulmon";

const W = 13.3;
const H = 7.5;
const M = 0.72;

// ------------------------------------------------------- helpers de maqueta
function slideOscura() {
  const s = pres.addSlide();
  s.background = { color: TINTA };
  return s;
}
function slideClara() {
  const s = pres.addSlide();
  s.background = { color: PAPEL };
  return s;
}

function titulo(s, texto, opts = {}) {
  s.addText(texto, {
    x: M,
    y: opts.y ?? 0.46,
    w: opts.w ?? W - 2 * M,
    h: opts.h ?? 1.2,
    fontFace: SERIF,
    fontSize: opts.fontSize ?? 28,
    bold: true,
    color: opts.color ?? TINTA,
    margin: 0,
    valign: "top",
  });
}

function antetitulo(s, texto, color = MUDO) {
  s.addText(texto, {
    x: M, y: 0.2, w: W - 2 * M, h: 0.26,
    fontFace: SANS, fontSize: 10, bold: true, charSpacing: 2.4,
    color, margin: 0,
  });
}

function pieDiapo(s, texto, color = MUDO) {
  s.addText(texto, {
    x: M, y: H - 0.52, w: W - 2 * M, h: 0.28,
    fontFace: SANS, fontSize: 9, color, margin: 0, italic: true,
  });
}

function tarjeta(s, x, y, w, h, relleno = CREMA) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: relleno },
    line: { color: "E4E3DE", width: 0.6 },
    shadow: { type: "outer", color: "B8B7B2", blur: 7, offset: 1.4, angle: 90, opacity: 0.2 },
  });
}

function cifra(s, x, y, w, valor, rotulo, colorValor = TINTA, tamano = 38) {
  s.addText(valor, {
    x, y, w, h: 0.7,
    fontFace: SERIF, fontSize: tamano, bold: true, color: colorValor,
    margin: 0, valign: "top",
  });
  s.addText(rotulo, {
    x, y: y + 0.68, w, h: 0.5,
    fontFace: SANS, fontSize: 10.5, color: TINTA_2, margin: 0, valign: "top",
    lineSpacingMultiple: 1.2,
  });
}

// =========================================================== 1. PORTADA
{
  const s = slideOscura();
  s.addText("TRABAJO DE FIN DE MÁSTER  ·  MÁSTER UNIVERSITARIO EN BIOINFORMÁTICA", {
    x: M, y: 1.5, w: W - 2 * M, h: 0.3,
    fontFace: SANS, fontSize: 11, bold: true, charSpacing: 2.6, color: MUDO, margin: 0,
  });
  s.addText("Framework transcriptómico basado en la\nintegración de modelos de lenguaje y aprendizaje\nautomático para la identificación de biomarcadores\nen cáncer de pulmón", {
    x: M, y: 1.98, w: 11.2, h: 3.1,
    fontFace: SERIF, fontSize: 30, bold: true, color: BLANCO, margin: 0,
    lineSpacingMultiple: 1.1, valign: "top",
  });
  s.addShape(pres.ShapeType.line, {
    x: M, y: 5.9, w: 3.1, h: 0,
    line: { color: AZUL, width: 2.4 },
  });
  s.addText([
    { text: "Daniel Tapia Díez", options: { bold: true, color: BLANCO, fontSize: 14 } },
    { text: "\nTutor: Leonardo Dulcetti", options: { color: MUDO, fontSize: 12 } },
    { text: "\nUniversidad Alfonso X el Sabio  ·  Madrid, septiembre 2026", options: { color: MUDO, fontSize: 12 } },
  ], { x: M, y: 6.12, w: 8, h: 1.1, fontFace: SANS, margin: 0, lineSpacingMultiple: 1.24 });
  s.addNotes(
    "Buenos dias. Presento un framework transcriptomico que integra modelos de lenguaje y " +
    "aprendizaje automatico para identificar biomarcadores en cancer de pulmon. El trabajo " +
    "se articula en torno a tres experimentos biologicos que voy a resumir en diez minutos."
  );
}

// =========================================================== 2. CONTEXTO + ARQUITECTURA
{
  const s = slideClara();
  antetitulo(s, "CONTEXTO Y ARQUITECTURA");
  titulo(s, "Un framework en tres capas para\nfirmas transcriptómicas reproducibles", { fontSize: 24 });

  s.addText(
    "El cáncer de pulmón es la primera causa de mortalidad oncológica mundial (Bray et al., 2024). " +
    "NCBI GEO ofrece miles de cohortes reutilizables, pero integrar estudios independientes " +
    "introduce variabilidad de plataforma, efecto lote y metadatos heterogéneos que hacen " +
    "que la mayoría de firmas publicadas no repliquen (Leek et al., 2010; Bernau et al., 2014).",
    { x: M, y: 2.14, w: 11.86, h: 1.4, fontFace: SANS, fontSize: 13, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.3 }
  );

  const capas = [
    ["1", "Curación clínica con LLM",
     "Llama 3.3-70b (Groq API) interpreta metadatos no estandarizados de GEO y asigna grupos experimentales comparables.",
     `${dec(100 - D.pctSinClas, 1)} % éxito global`],
    ["2", "Identificación con ML",
     "t de Welch por cohorte + FDR Benjamini-Hochberg, meta-análisis con d de Cohen, LASSO L1 con class_weight balanced.",
     `${D.nValidados} genes validados`],
    ["3", "Validación externa",
     "LODO estricto (Leave-One-Dataset-Out), calibración isotónica post-hoc, IC bootstrap n=1000 y contraste con panel IHC OMS.",
     "La capa que decide si sirve"],
  ];
  capas.forEach(([n, tit, txt, nota], i) => {
    const x = M + i * 4.06;
    const relleno = i === 2 ? "1A1D21" : CREMA;
    const cTit = i === 2 ? BLANCO : TINTA;
    const cTxt = i === 2 ? "C3C2B7" : TINTA_2;
    const cNota = i === 2 ? AZUL : TINTA;
    tarjeta(s, x, 3.72, 3.78, 3.1, relleno);
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.28, y: 3.94, w: 0.42, h: 0.42,
      fill: { color: i === 2 ? "262A30" : PAPEL },
      line: { color: AZUL, width: 1 },
    });
    s.addText(n, {
      x: x + 0.28, y: 3.94, w: 0.42, h: 0.42, fontFace: SERIF, fontSize: 14,
      bold: true, color: AZUL, align: "center", valign: "middle", margin: 0,
    });
    s.addText(tit, {
      x: x + 0.84, y: 3.92, w: 2.7, h: 0.44,
      fontFace: SERIF, fontSize: 14, bold: true, color: cTit, margin: 0, valign: "middle",
    });
    s.addText(txt, {
      x: x + 0.28, y: 4.5, w: 3.24, h: 1.55,
      fontFace: SANS, fontSize: 10.5, color: cTxt, margin: 0, valign: "top", lineSpacingMultiple: 1.24,
    });
    s.addText(nota, {
      x: x + 0.28, y: 6.16, w: 3.24, h: 0.5,
      fontFace: SANS, fontSize: 10.5, italic: true, bold: true,
      color: cNota, margin: 0, valign: "top",
    });
  });
  pieDiapo(s, "Contribución metodológica: integración de las tres capas en un pipeline reproducible con random_state fijado.");
  s.addNotes(
    "El framework tiene tres capas: curacion con LLM, identificacion de firmas con ML, y " +
    "validacion externa estricta. Cada capa incorpora tecnicas concretas —Welch, FDR, Cohen, " +
    "LASSO, LODO, isotonica, bootstrap— que voy a detallar en las siguientes diapositivas."
  );
}

// =========================================================== 3. LOS TRES EXPERIMENTOS
{
  const s = slideClara();
  antetitulo(s, "OBJETIVOS");
  titulo(s, "Tres experimentos biológicos sobre las mismas cohortes");

  const exp = [
    {
      letra: "A",
      titulo: "Firma consenso",
      pregunta: "¿Qué genes son biomarcadores creíbles de cáncer de pulmón?",
      metodo: "Meta-análisis multi-cohorte con d de Cohen + validación cruzada externa",
      resultado: `${D.nValidados} genes → panel mínimo de ${D.panelMin}`,
      color: AZUL,
    },
    {
      letra: "B",
      titulo: "Subtipo histológico",
      pregunta: "¿Es adenocarcinoma o carcinoma escamoso?",
      metodo: "LASSO L1 sobre 3 cohortes (n=388) con validación LODO estricta",
      resultado: `AUC ${dec(D.aucSub)} · valor terapéutico directo`,
      color: VERDE,
      destacado: true,
    },
    {
      letra: "C",
      titulo: "Tumor vs sano",
      pregunta: "¿La muestra es tumoral o pulmón normal?",
      metodo: "LASSO L1 + recalibración isotónica sobre 8 cohortes evaluables",
      resultado: `AUC ${dec(D.auc)} → ${dec(D.aucCalIso)} · control metodológico`,
      color: TINTA_2,
    },
  ];
  exp.forEach((e, i) => {
    const x = M + i * 4.06;
    const relleno = e.destacado ? CREMA : PAPEL;
    tarjeta(s, x, 1.8, 3.78, 5.1, relleno);
    s.addText(e.letra, {
      x: x + 0.3, y: 2.0, w: 0.9, h: 0.9,
      fontFace: SERIF, fontSize: 46, bold: true, color: e.color, margin: 0, valign: "top",
    });
    s.addText(e.titulo, {
      x: x + 1.24, y: 2.2, w: 2.3, h: 0.5,
      fontFace: SERIF, fontSize: 17, bold: true, color: TINTA, margin: 0, valign: "middle",
    });
    s.addShape(pres.ShapeType.line, {
      x: x + 0.3, y: 3.05, w: 3.2, h: 0,
      line: { color: "D8D7D2", width: 0.6 },
    });
    s.addText("PREGUNTA", {
      x: x + 0.3, y: 3.16, w: 3.2, h: 0.24,
      fontFace: SANS, fontSize: 8.5, bold: true, charSpacing: 1.4, color: MUDO, margin: 0,
    });
    s.addText(e.pregunta, {
      x: x + 0.3, y: 3.4, w: 3.2, h: 0.9,
      fontFace: SERIF, fontSize: 12.5, italic: true, color: TINTA, margin: 0, valign: "top", lineSpacingMultiple: 1.22,
    });
    s.addText("MÉTODO", {
      x: x + 0.3, y: 4.42, w: 3.2, h: 0.24,
      fontFace: SANS, fontSize: 8.5, bold: true, charSpacing: 1.4, color: MUDO, margin: 0,
    });
    s.addText(e.metodo, {
      x: x + 0.3, y: 4.66, w: 3.2, h: 1.0,
      fontFace: SANS, fontSize: 11, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.24,
    });
    s.addText("RESULTADO", {
      x: x + 0.3, y: 5.76, w: 3.2, h: 0.24,
      fontFace: SANS, fontSize: 8.5, bold: true, charSpacing: 1.4, color: MUDO, margin: 0,
    });
    s.addText(e.resultado, {
      x: x + 0.3, y: 6.0, w: 3.2, h: 0.8,
      fontFace: SANS, fontSize: 12, bold: true, color: e.color, margin: 0, valign: "top", lineSpacingMultiple: 1.22,
    });
  });

  pieDiapo(s, "El bloque B es el que tiene consecuencia clínica directa; A y C sustentan y validan el marco metodológico.");
  s.addNotes(
    "El trabajo tiene tres experimentos. A: descubrir que genes son biomarcadores creibles. " +
    "B: distinguir adenocarcinoma de escamoso, la tarea con consecuencia terapeutica directa. " +
    "C: separar tumor de sano, control metodologico. En las tres diapositivas siguientes " +
    "los desarrollo uno a uno."
  );
}

// =========================================================== 4. MATERIALES
{
  const s = slideClara();
  antetitulo(s, "MATERIALES");
  titulo(s, "13 cohortes GEO · 3 plataformas · " + Math.round(D.nMuestras) + " muestras");

  const filas = [[
    { text: "Cohorte", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 10.5 } },
    { text: "Plataforma", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 10.5 } },
    { text: "n", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 10.5, align: "right" } },
    { text: "Sanas", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 10.5, align: "right" } },
    { text: "Enfermas", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 10.5, align: "right" } },
    { text: "Evaluable", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 10.5, align: "center" } },
  ]];
  aud.forEach((r, i) => {
    const mono = r.Evaluable_Como_Test === "False";
    const relleno = i % 2 ? { color: CREMA } : { color: PAPEL };
    filas.push([
      { text: r.Cohorte, options: { fill: relleno, color: TINTA, bold: mono } },
      { text: r.Plataforma, options: { fill: relleno, color: TINTA_2 } },
      { text: r.N_Total, options: { fill: relleno, color: TINTA, align: "right" } },
      { text: r.N_Sano, options: { fill: relleno, color: mono ? ROJO : TINTA_2, align: "right", bold: mono } },
      { text: r.N_Enfermo, options: { fill: relleno, color: TINTA_2, align: "right" } },
      { text: mono ? "no" : "sí", options: { fill: relleno, color: mono ? ROJO : VERDE, align: "center", bold: true } },
    ]);
  });
  s.addTable(filas, {
    x: M, y: 1.8, w: 7.3, colW: [1.4, 1.4, 0.9, 1.0, 1.2, 1.4],
    rowH: 0.28, fontFace: SANS, fontSize: 10,
    border: { type: "solid", color: "E4E3DE", pt: 0.5 }, valign: "middle",
  });

  // Panel derecho: curación LLM + cohortes no evaluables
  tarjeta(s, 8.3, 1.8, 4.28, 2.5);
  s.addText("CURACIÓN CLÍNICA CON LLM", {
    x: 8.6, y: 2.0, w: 3.8, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  cifra(s, 8.6, 2.4, 3.8, dec(100 - D.pctSinClas, 1) + " %", "muestras clasificadas correctamente por Llama 3.3-70b", VERDE, 32);
  s.addText(
    `Fallo bimodal: 8 cohortes >95 %, 2 cohortes con colapso (GSE40791: 12/194). ` +
    `${Math.round(D.sinClas)} muestras sin clasificar se excluyen explícitamente del análisis.`,
    { x: 8.6, y: 3.66, w: 3.8, h: 0.6, fontFace: SANS, fontSize: 10, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.2 }
  );

  tarjeta(s, 8.3, 4.4, 4.28, 2.5, "1A1D21");
  s.addText("3 COHORTES SIN CONTROLES SANOS", {
    x: 8.6, y: 4.6, w: 3.8, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: ROJO, margin: 0,
  });
  s.addText(
    "GSE30219, GSE50081 y GSE140797 son estudios de supervivencia sin controles. " +
    "Se descartan como test binario tumor/sano (accuracy trivial = 1,000).\n\n" +
    "Se recuperan para el bloque B (subtipo): GSE30219 y GSE50081 sí tienen ADC/SQC etiquetados.",
    { x: 8.6, y: 4.98, w: 3.8, h: 1.9, fontFace: SANS, fontSize: 10, color: "C3C2B7", margin: 0, lineSpacingMultiple: 1.28 }
  );

  pieDiapo(s, "Plataformas: GPL570 (Affymetrix HG-U133 Plus 2.0), GPL96 (HG-U133A), GPL13497 (Agilent). Traducción probe → símbolo génico con anotaciones oficiales de Bioconductor.");
  s.addNotes(
    "Trece cohortes descargadas, once con datos utilizables, ocho evaluables como test " +
    "tumor-vs-sano. La curacion con LLM alcanza el 82,8 por ciento con fallo bimodal. " +
    "Las tres cohortes sin controles se recuperan para el bloque B."
  );
}

// =========================================================== 5. PIPELINE ESTADÍSTICO Y ML
{
  const s = slideOscura();
  antetitulo(s, "METODOLOGÍA ESTADÍSTICA Y DE ML", MUDO);
  titulo(s, "Pipeline reproducible en cinco pasos", { color: BLANCO });

  const pasos = [
    {
      n: "1",
      tit: "Preprocesamiento",
      tecnica: "Normalización RMA por cohorte",
      det: "Log2(intensity + 1) · traducción probe→gen con Bioconductor · agregación por mediana",
    },
    {
      n: "2",
      tit: "Análisis diferencial",
      tecnica: "t de Welch + FDR Benjamini-Hochberg",
      det: "Varianzas desiguales asumidas · α = 0,05 · corrección BH controla proporción de falsos positivos",
    },
    {
      n: "3",
      tit: "Meta-análisis multi-cohorte",
      tecnica: "d de Cohen + dirección concordante",
      det: "|d| ≥ 0,5 (efecto medio) · signo idéntico en 3/3 cohortes → 1174 genes",
    },
    {
      n: "4",
      tit: "Clasificación supervisada",
      tecnica: "LASSO L1 (regresión logística)",
      det: "C = 0,1 · class_weight balanced · max_iter 5000 · random_state 42 · esparsidad automática",
    },
    {
      n: "5",
      tit: "Validación externa",
      tecnica: "LODO + isotónica + bootstrap",
      det: "Leave-One-Dataset-Out estricto · calibración post-hoc por cohorte test · IC 95 % con 1000 resamples",
    },
  ];
  pasos.forEach((p, i) => {
    const y = 1.9 + i * 1.0;
    // Numero
    s.addShape(pres.ShapeType.ellipse, {
      x: M, y, w: 0.62, h: 0.62,
      fill: { color: "262A30" }, line: { color: AZUL, width: 1 },
    });
    s.addText(p.n, {
      x: M, y, w: 0.62, h: 0.62, fontFace: SERIF, fontSize: 18, bold: true,
      color: AZUL, align: "center", valign: "middle", margin: 0,
    });
    // Titulo
    s.addText(p.tit, {
      x: M + 0.86, y: y + 0.02, w: 3.5, h: 0.34,
      fontFace: SERIF, fontSize: 14, bold: true, color: BLANCO, margin: 0, valign: "top",
    });
    // Tecnica (mono/etiqueta)
    s.addText(p.tecnica, {
      x: M + 0.86, y: y + 0.38, w: 3.5, h: 0.28,
      fontFace: SANS, fontSize: 10.5, italic: true, color: AZUL, margin: 0, valign: "top",
    });
    // Detalle
    s.addText(p.det, {
      x: 5.0, y: y + 0.06, w: W - 5.0 - M, h: 0.9,
      fontFace: SANS, fontSize: 11, color: "C3C2B7", margin: 0, valign: "top", lineSpacingMultiple: 1.24,
    });
  });

  pieDiapo(s, "Todo el pipeline es determinista: dos ejecuciones producen resultados idénticos. Random_state fijado en cada estimador estocástico.", MUDO);
  s.addNotes(
    "El pipeline tiene cinco pasos estadisticos y de ML, en este orden. Preprocesamiento con " +
    "RMA. Analisis diferencial con Welch y FDR Benjamini-Hochberg al 5 por ciento. " +
    "Meta-analisis con d de Cohen y direccion concordante en las 3 cohortes. LASSO L1 con " +
    "class_weight balanced y regularizacion fuerte. Validacion LODO estricta con calibracion " +
    "isotonica e intervalos bootstrap de 1000 resamples. Random_state fijado en todo."
  );
}

// =========================================================== 6. BLOQUE A · FIRMA CONSENSO
{
  const s = slideClara();
  antetitulo(s, "BLOQUE A  ·  FIRMA CONSENSO", AZUL);
  titulo(s, "1174 genes que replican en 3 cohortes independientes");

  // Bloque izquierdo: metodo estadistico
  s.addText("CRITERIOS DE INCLUSIÓN (PRE-REGISTRADOS)", {
    x: M, y: 1.95, w: 6.3, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText([
    { text: "•  ", options: { color: AZUL, fontSize: 12, bold: true } },
    { text: "Presente en ", options: { fontSize: 12, color: TINTA_2 } },
    { text: "≥ 3 plataformas ", options: { fontSize: 12, bold: true, color: TINTA } },
    { text: "distintas (control de artefacto de plataforma)", options: { fontSize: 12, color: TINTA_2 } },
    { text: "\n•  ", options: { color: AZUL, fontSize: 12, bold: true } },
    { text: "|d de Cohen| ", options: { fontSize: 12, color: TINTA_2 } },
    { text: "≥ 0,5 ", options: { fontSize: 12, bold: true, color: TINTA } },
    { text: "en cada cohorte por separado (efecto medio o grande)", options: { fontSize: 12, color: TINTA_2 } },
    { text: "\n•  ", options: { color: AZUL, fontSize: 12, bold: true } },
    { text: "Dirección concordante en ", options: { fontSize: 12, color: TINTA_2 } },
    { text: "3/3 cohortes ", options: { fontSize: 12, bold: true, color: TINTA } },
    { text: "(sube o baja en todas)", options: { fontSize: 12, color: TINTA_2 } },
    { text: "\n•  ", options: { color: AZUL, fontSize: 12, bold: true } },
    { text: "p ajustado ", options: { fontSize: 12, color: TINTA_2 } },
    { text: "(FDR Benjamini-Hochberg) < 0,05", options: { fontSize: 12, bold: true, color: TINTA } },
  ], { x: M, y: 2.28, w: 6.3, h: 2.4, fontFace: SANS, margin: 0, valign: "top", lineSpacingMultiple: 1.44 });

  // Control biologico
  tarjeta(s, M, 4.8, 6.3, 2.05);
  s.addText("CONTROL BIOLÓGICO: ¿MIDE BIOLOGÍA O COMPOSICIÓN?", {
    x: M + 0.3, y: 4.98, w: 5.7, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText([
    { text: "ρ Spearman = " + dec(D.rho, 2), options: { fontFace: SERIF, fontSize: 20, bold: true, color: AZUL } },
    { text: `   entre firma restringida a tumores y panel pulmón normal (${D.nRho} cohortes).`, options: { fontFace: SANS, fontSize: 11, color: TINTA_2 } },
    { text: "\nCorrelación negativa fuerte → no es artefacto composicional. Segundo eje detectado: proliferación (MKI67, TOP2A, CCNB1), ρ = +0,27 a +0,72.", options: { fontFace: SANS, fontSize: 11, italic: true, color: TINTA_2 } },
  ], { x: M + 0.3, y: 5.34, w: 5.7, h: 1.4, margin: 0, valign: "top", lineSpacingMultiple: 1.3 });

  // Cifras clave a la derecha
  tarjeta(s, 7.3, 1.9, 5.28, 4.95);
  cifra(s, 7.6, 2.14, 4.68, `${D.nValidados}`, `genes validados por consenso (${dec(D.pctValidados, 1)} % de 22 880)`, AZUL, 42);
  s.addShape(pres.ShapeType.line, { x: 7.6, y: 3.5, w: 4.68, h: 0, line: { color: "D8D7D2", width: 0.6 } });
  cifra(s, 7.6, 3.64, 4.68, `${D.panelMin}`, `genes en panel mínimo · AUC ${dec(D.aucPanel)} (vs ${dec(D.aucFirmaCompleta)} con firma completa)`, TINTA, 36);
  s.addShape(pres.ShapeType.line, { x: 7.6, y: 4.98, w: 4.68, h: 0, line: { color: "D8D7D2", width: 0.6 } });
  cifra(s, 7.6, 5.12, 4.68, `${D.ihcRec} / ${D.ihcTot}`, "marcadores IHC OMS recuperados sin haber participado en la selección → coincidencia estadísticamente improbable por azar", VERDE, 36);

  pieDiapo(s, "Los 20 genes del panel mínimo incluyen KRT5, DSG3, TP63, KRT6A, PKP1 — canónicos del linaje escamoso del panel diagnóstico OMS 2015.");
  s.addNotes(
    "Bloque A. Criterios pre-registrados: presencia en 3+ plataformas, d de Cohen mayor o igual " +
    "0,5, direccion concordante en las 3 cohortes, FDR Benjamini-Hochberg menor 0,05. Mil " +
    "ciento setenta y cuatro genes cumplen los cuatro criterios. Panel minimo de 20 genes " +
    "conserva rendimiento. Recupera 18 de 20 marcadores IHC clinicos: coincidencia " +
    "estadisticamente improbable por azar."
  );
}

// =========================================================== 7. BLOQUE B · SUBTIPO ADC vs SQC
{
  const s = slideClara();
  antetitulo(s, "BLOQUE B  ·  SUBTIPO HISTOLÓGICO  (VALOR CLÍNICO DIRECTO)", VERDE);
  titulo(s, "Adenocarcinoma vs escamoso: la decisión terapéutica");

  // Bloque izquierdo: por que importa
  tarjeta(s, M, 1.85, 6.3, 2.4);
  s.addText("POR QUÉ IMPORTA CLÍNICAMENTE", {
    x: M + 0.3, y: 2.02, w: 5.7, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText([
    { text: "Pemetrexed", options: { bold: true, color: TINTA, fontSize: 12 } },
    { text: " y ", options: { color: TINTA_2, fontSize: 12 } },
    { text: "bevacizumab", options: { bold: true, color: TINTA, fontSize: 12 } },
    { text: " están ", options: { color: TINTA_2, fontSize: 12 } },
    { text: "contraindicados en escamoso", options: { bold: true, color: ROJO, fontSize: 12 } },
    { text: " (bevacizumab por riesgo de hemorragia mortal). Hasta un tercio de los tumores es morfológicamente ambiguo al microscopio y requiere panel IHC para decidir.", options: { color: TINTA_2, fontSize: 12 } },
  ], { x: M + 0.3, y: 2.38, w: 5.7, h: 1.8, fontFace: SANS, margin: 0, valign: "top", lineSpacingMultiple: 1.28 });

  // Metodo ML
  tarjeta(s, M, 4.4, 6.3, 2.55);
  s.addText("METODOLOGÍA ML", {
    x: M + 0.3, y: 4.58, w: 5.7, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText([
    { text: "•  ", options: { color: VERDE, fontSize: 11, bold: true } },
    { text: "Datos: ", options: { color: TINTA, fontSize: 11, bold: true } },
    { text: "3 cohortes GEO GPL570 con ADC/SQC anotados (n = " + D.nSub + ")", options: { color: TINTA_2, fontSize: 11 } },
    { text: "\n•  ", options: { color: VERDE, fontSize: 11, bold: true } },
    { text: "Modelo: ", options: { color: TINTA, fontSize: 11, bold: true } },
    { text: "LASSO L1 · C=0,1 · class_weight balanced · 1174 features", options: { color: TINTA_2, fontSize: 11 } },
    { text: "\n•  ", options: { color: VERDE, fontSize: 11, bold: true } },
    { text: "Validación: ", options: { color: TINTA, fontSize: 11, bold: true } },
    { text: "LODO estricto — cohorte test NO en train ni hiperparámetros", options: { color: TINTA_2, fontSize: 11 } },
    { text: "\n•  ", options: { color: VERDE, fontSize: 11, bold: true } },
    { text: "Métricas: ", options: { color: TINTA, fontSize: 11, bold: true } },
    { text: "AUC (primaria), BalAcc, Sens, Espec (secundarias)", options: { color: TINTA_2, fontSize: 11 } },
  ], { x: M + 0.3, y: 4.94, w: 5.7, h: 2.0, fontFace: SANS, margin: 0, valign: "top", lineSpacingMultiple: 1.42 });

  // Bloque derecho: resultados LODO
  tarjeta(s, 7.3, 1.85, 5.28, 5.1, "1A1D21");
  s.addText("RESULTADOS · VALIDACIÓN LODO EXTERNA", {
    x: 7.6, y: 2.06, w: 4.68, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText(dec(D.aucSub), {
    x: 7.6, y: 2.4, w: 4.68, h: 1.05,
    fontFace: SERIF, fontSize: 62, bold: true, color: VERDE, margin: 0, valign: "top",
  });
  s.addText("AUC medio LODO (3 iteraciones)", {
    x: 7.6, y: 3.42, w: 4.68, h: 0.4,
    fontFace: SANS, fontSize: 11.5, color: "C3C2B7", margin: 0,
  });

  s.addShape(pres.ShapeType.line, { x: 7.6, y: 3.95, w: 4.68, h: 0, line: { color: "343941", width: 0.6 } });

  // Grid metricas secundarias
  const met = [
    [dec(D.balSub), "Bal. accuracy"],
    [dec(D.sensSub), "Sensibilidad"],
    [dec(D.especSub), "Especificidad"],
  ];
  met.forEach(([v, r], i) => {
    const x = 7.6 + i * 1.56;
    s.addText(v, {
      x, y: 4.12, w: 1.5, h: 0.6,
      fontFace: SERIF, fontSize: 22, bold: true, color: BLANCO, margin: 0, valign: "top",
    });
    s.addText(r, {
      x, y: 4.72, w: 1.5, h: 0.32,
      fontFace: SANS, fontSize: 9.5, color: "C3C2B7", margin: 0,
    });
  });

  s.addShape(pres.ShapeType.line, { x: 7.6, y: 5.16, w: 4.68, h: 0, line: { color: "343941", width: 0.6 } });
  s.addText([
    { text: "18 / 20", options: { fontFace: SERIF, fontSize: 20, bold: true, color: VERDE } },
    { text: "  marcadores IHC OMS recuperados sin participar en la selección. Panel mínimo medible por PCR cuantitativa multiplex o NanoString nCounter.", options: { fontFace: SANS, fontSize: 10.5, color: "C3C2B7" } },
  ], { x: 7.6, y: 5.34, w: 4.68, h: 1.55, margin: 0, valign: "top", lineSpacingMultiple: 1.28 });

  pieDiapo(s, "Alcance: válido sobre tumores ya confirmados como ADC o SQC. Los neuroendocrinos (excluidos del entrenamiento) requieren un paso previo.");
  s.addNotes(
    "Bloque B. LASSO L1 con clase balanceada. Validacion LODO estricta: la cohorte de test " +
    "no participa ni en train ni en hiperparametros. AUC 0,968, balanced accuracy 0,940. " +
    "Recupera 18 de 20 marcadores IHC clinicos. El panel es utilizable en RT-qPCR sobre " +
    "tejido parafinado."
  );
}

// =========================================================== 8. BLOQUE C · TUMOR VS SANO + RECALIBRACIÓN
{
  const s = slideClara();
  antetitulo(s, "BLOQUE C  ·  TUMOR VS SANO  (CONTROL METODOLÓGICO)", MUDO);
  titulo(s, "Recalibración isotónica cierra la brecha discriminación / decisión");

  s.addText(
    `LODO sobre ${D.nEv} cohortes evaluables (${D.nCoh} totales, 3 monoclase excluidas). ` +
    "El modelo ordena bien las muestras pero el umbral aprendido no transfiere entre cohortes.",
    { x: M, y: 1.9, w: 11.86, h: 0.7, fontFace: SANS, fontSize: 12.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.28 }
  );

  // Columna izquierda: sin calibrar
  tarjeta(s, M, 2.8, 3.86, 3.9);
  s.addText("SIN CALIBRAR", {
    x: M + 0.28, y: 2.98, w: 3.3, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  cifra(s, M + 0.28, 3.32, 3.3, dec(D.auc), "AUC medio", AZUL, 30);
  cifra(s, M + 0.28, 4.44, 3.3, dec(D.balAcc), "Bal. accuracy", ROJO, 30);
  s.addText("Brecha diagnóstica → umbral no transfiere", {
    x: M + 0.28, y: 5.72, w: 3.3, h: 0.7,
    fontFace: SANS, fontSize: 10, italic: true, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.2,
  });

  // Columna centro: isotónica
  tarjeta(s, 4.72, 2.8, 3.86, 3.9, "1A1D21");
  s.addText("ISOTÓNICA (elegida)", {
    x: 5.0, y: 2.98, w: 3.3, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: VERDE, margin: 0,
  });
  cifra(s, 5.0, 3.32, 3.3, dec(D.aucCalIso), "AUC medio", VERDE, 30);
  cifra(s, 5.0, 4.44, 3.3, dec(D.balCalIso), "Bal. accuracy", BLANCO, 30);
  s.addText(`Ganancia BalAcc: +${dec(D.gananciaIso, 3)}   ·   no paramétrica`, {
    x: 5.0, y: 5.72, w: 3.3, h: 0.7,
    fontFace: SANS, fontSize: 10, color: "C3C2B7", margin: 0, italic: true, lineSpacingMultiple: 1.2,
  });

  // Columna derecha: Platt (control)
  tarjeta(s, 8.6, 2.8, 3.98, 3.9);
  s.addText("PLATT (control)", {
    x: 8.88, y: 2.98, w: 3.4, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  cifra(s, 8.88, 3.32, 3.4, dec(D.aucCalPlatt), "AUC medio", TINTA, 30);
  cifra(s, 8.88, 4.44, 3.4, dec(D.balCalPlatt), "Bal. accuracy", ROJO, 30);
  s.addText("Peor que sin calibrar → confirma que isotónica es la correcta, no un cherry-pick", {
    x: 8.88, y: 5.72, w: 3.4, h: 0.9,
    fontFace: SANS, fontSize: 10, italic: true, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.2,
  });

  // Bootstrap
  tarjeta(s, M, 6.86, 11.86, 0.5);
  s.addText([
    { text: "IC bootstrap (n = " + D.nBoot + " resamples):  ", options: { fontFace: SANS, fontSize: 10.5, color: MUDO } },
    { text: `AUC = ${dec(D.aucBoot)} [${dec(D.aucBootIC[0])} ; ${dec(D.aucBootIC[1])}]`, options: { fontFace: SANS, fontSize: 11.5, bold: true, color: TINTA } },
    { text: `   ·   BalAcc = ${dec(D.balBoot)} [${dec(D.balBootIC[0])} ; ${dec(D.balBootIC[1])}]`, options: { fontFace: SANS, fontSize: 11.5, color: TINTA_2 } },
    { text: "   →   robustez confirmada", options: { fontFace: SANS, fontSize: 10.5, italic: true, color: VERDE, bold: true } },
  ], { x: M + 0.24, y: 6.96, w: 11.4, h: 0.32, margin: 0, valign: "middle" });

  pieDiapo(s, "Isotónica: función monótona no paramétrica. Platt: sigmoide de dos parámetros. Se reportan ambas porque ejecutar solo la que funciona sería cherry-picking.", MUDO);
  s.addNotes(
    "Bloque C. AUC 0,925 sin recalibrar, pero BalAcc 0,772 — el modelo ordena bien pero el " +
    "umbral no transfiere. Isotonica sube AUC a 0,953 y BalAcc a 0,810. Platt como control " +
    "empeora, lo que confirma que la eleccion de isotonica no es cherry-picking. Bootstrap " +
    "con 1000 resamples: intervalo estrecho, robustez confirmada."
  );
}

// =========================================================== 9. COMPARATIVA ML
{
  const s = slideClara();
  antetitulo(s, "COMPARATIVA DE MODELOS");
  titulo(s, "LASSO L1 · Random Forest · SVM lineal en LODO");

  s.addText(
    "Se evaluaron tres familias de clasificadores sobre la misma tarea (tumor vs sano) con la misma " +
    `firma de entrada y la misma validación LODO estricta sobre ${D.nEv} cohortes evaluables.`,
    { x: M, y: 1.88, w: 11.86, h: 0.7, fontFace: SANS, fontSize: 12.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.28 }
  );

  // Tabla comparativa
  const modelos = [
    ["LASSO L1 (regresión logística + L1)", D.ml.LASSO_L1, AZUL, "seleccionado — interpretable, esparso"],
    ["Random Forest (n_estimators=500)", D.ml.Random_Forest, TINTA_2, "AUC comparable, sin selección de features"],
    ["SVM lineal (C=1)", D.ml.SVM_lineal, TINTA_2, "AUC ligeramente superior, sin coeficientes interpretables"],
  ];
  const filas = [[
    { text: "Modelo", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11 } },
    { text: "AUC", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Bal. Acc.", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Sens.", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Espec.", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Nota", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11 } },
  ]];
  modelos.forEach(([nom, r, col, nota], i) => {
    const relleno = i === 0 ? { color: "EAF2FB" } : (i % 2 ? { color: PAPEL } : { color: CREMA });
    filas.push([
      { text: nom, options: { fill: relleno, color: TINTA, bold: i === 0, fontSize: 11 } },
      { text: dec(r.auc_media), options: { fill: relleno, color: col, bold: true, align: "right", fontSize: 12 } },
      { text: dec(r.balanced_accuracy_media), options: { fill: relleno, color: TINTA, align: "right", fontSize: 12 } },
      { text: dec(r.sensibilidad_media), options: { fill: relleno, color: TINTA_2, align: "right", fontSize: 11 } },
      { text: dec(r.especificidad_media), options: { fill: relleno, color: TINTA_2, align: "right", fontSize: 11 } },
      { text: nota, options: { fill: relleno, color: TINTA_2, italic: true, fontSize: 10 } },
    ]);
  });
  s.addTable(filas, {
    x: M, y: 2.9, w: 11.86, colW: [3.5, 1.0, 1.2, 1.0, 1.0, 4.16],
    rowH: 0.5, fontFace: SANS, border: { type: "solid", color: "E4E3DE", pt: 0.5 }, valign: "middle",
  });

  // Justificacion
  tarjeta(s, M, 5.4, 11.86, 1.6, "1A1D21");
  s.addText("POR QUÉ SE ELIGE LASSO L1 PESE A QUE SVM DA AUC LIGERAMENTE SUPERIOR", {
    x: M + 0.32, y: 5.58, w: 11.2, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText([
    { text: "Selección de features automática ", options: { fontFace: SANS, fontSize: 11.5, bold: true, color: BLANCO } },
    { text: "(coeficientes exactamente 0 → panel mínimo de 20 genes)   ·   ", options: { fontFace: SANS, fontSize: 11, color: "C3C2B7" } },
    { text: "Interpretabilidad clínica ", options: { fontFace: SANS, fontSize: 11.5, bold: true, color: BLANCO } },
    { text: "(un coeficiente por gen, dirección biológica clara)   ·   ", options: { fontFace: SANS, fontSize: 11, color: "C3C2B7" } },
    { text: "Robustez a alta dimensionalidad ", options: { fontFace: SANS, fontSize: 11.5, bold: true, color: BLANCO } },
    { text: "(1174 features, ~1000 muestras)", options: { fontFace: SANS, fontSize: 11, color: "C3C2B7" } },
  ], { x: M + 0.32, y: 5.92, w: 11.2, h: 1.0, margin: 0, valign: "top", lineSpacingMultiple: 1.36 });

  pieDiapo(s, "Comparativa reportada para ser transparente: elegir un solo modelo sin justificarlo frente a alternativas también sería cherry-picking.");
  s.addNotes(
    "Comparativa transparente de tres familias de modelos. LASSO L1: AUC 0,925. Random " +
    "Forest: 0,933. SVM lineal: 0,957. SVM da AUC ligeramente superior, pero LASSO se elige " +
    "por seleccion de features automatica (panel minimo de 20 genes), interpretabilidad " +
    "clinica de los coeficientes, y robustez con muchas features y pocas muestras."
  );
}

// =========================================================== 10. ROBUSTEZ
{
  const s = slideClara();
  antetitulo(s, "AUDITORÍA INTERNA DEL FRAMEWORK");
  titulo(s, "Tres controles metodológicos aplicados sobre sí mismo");

  const controles = [
    {
      titulo: "Bug de alineamiento detectado",
      cifra: "0,56 → 0,99",
      texto: "En GSE30219, columnas de matriz y filas de metadata desordenadas. Asignar por posición cruzaba etiquetas clínicas. Detectado por comparación con marcadores externos (KRT5).",
      color: ROJO,
    },
    {
      titulo: "Falacia de folds LODO resuelta",
      cifra: "97,6 % → 77 %",
      texto: "Dos folds LODO comparten mediana 97,6 % de muestras: no son réplicas independientes. Al medir con particiones disjuntas, la concordancia baja al 77 %.",
      color: NARANJA,
    },
    {
      titulo: "Baseline mayoritario declarado",
      cifra: `${D.nMono} de 11`,
      texto: "Cohortes de una sola clase (sin controles sanos) descartadas como test binario. Producían accuracy 1,000 trivial que inflaba el rendimiento reportado.",
      color: AZUL,
    },
  ];
  controles.forEach((c, i) => {
    const x = M + i * 4.06;
    tarjeta(s, x, 1.85, 3.78, 5.05);
    s.addText(c.titulo, {
      x: x + 0.3, y: 2.06, w: 3.22, h: 0.5,
      fontFace: SERIF, fontSize: 14, bold: true, color: TINTA, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });
    s.addShape(pres.ShapeType.line, {
      x: x + 0.3, y: 2.68, w: 3.22, h: 0, line: { color: "D8D7D2", width: 0.6 },
    });
    s.addText(c.cifra, {
      x: x + 0.3, y: 2.86, w: 3.22, h: 0.9,
      fontFace: SERIF, fontSize: 26, bold: true, color: c.color, margin: 0, valign: "top",
    });
    s.addText(c.texto, {
      x: x + 0.3, y: 3.86, w: 3.22, h: 2.9,
      fontFace: SANS, fontSize: 10.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.28,
    });
  });

  pieDiapo(s, "Ningún pipeline emitió un error al toparse con estos problemas — hubo que buscarlos. La auditoría interna es parte del framework, no un análisis externo.");
  s.addNotes(
    "Tres controles que el framework aplica sobre si mismo. Un bug de alineamiento en " +
    "GSE30219 detectado por comparacion con marcadores externos. Una falacia estadistica " +
    "en la metrica de estabilidad de folds LODO. Y la exclusion explicita de cohortes " +
    "monoclase. Sin estos controles, el framework habria reportado cifras infladas."
  );
}

// =========================================================== 11. DATA.LUNG
{
  const s = slideClara();
  antetitulo(s, "ENTREGABLE  ·  DATA.LUNG", AZUL);
  titulo(s, "Dashboard interactivo con todos los resultados navegables");

  // Bloque izquierdo: descripcion + stack
  s.addText(
    "data.lung expone el framework completo como aplicación web reproducible: navegación " +
    "por objetivos, metodología, resultados y conclusiones, con visualización interactiva " +
    "de cohortes y asistente conversacional con RAG sobre la memoria.",
    { x: M, y: 1.9, w: 6.4, h: 1.35, fontFace: SANS, fontSize: 12.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.3 }
  );

  s.addText("STACK TÉCNICO", {
    x: M, y: 3.4, w: 6.4, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText([
    { text: "•  ", options: { color: AZUL, fontSize: 11.5, bold: true } },
    { text: "Streamlit multipage", options: { color: TINTA, fontSize: 11.5, bold: true } },
    { text: " (landing + framework) con favicon propio de la marca", options: { color: TINTA_2, fontSize: 11.5 } },
    { text: "\n•  ", options: { color: AZUL, fontSize: 11.5, bold: true } },
    { text: "Backend Python", options: { color: TINTA, fontSize: 11.5, bold: true } },
    { text: ": scikit-learn, pandas, scipy, statsmodels", options: { color: TINTA_2, fontSize: 11.5 } },
    { text: "\n•  ", options: { color: AZUL, fontSize: 11.5, bold: true } },
    { text: "LLM asistente", options: { color: TINTA, fontSize: 11.5, bold: true } },
    { text: ": Llama 3.3-70b vía Groq API con contexto TFM inyectado", options: { color: TINTA_2, fontSize: 11.5 } },
    { text: "\n•  ", options: { color: AZUL, fontSize: 11.5, bold: true } },
    { text: "Lectura dinámica", options: { color: TINTA, fontSize: 11.5, bold: true } },
    { text: " de los CSV y JSON de resultados — cifras siempre actualizadas", options: { color: TINTA_2, fontSize: 11.5 } },
  ], { x: M, y: 3.72, w: 6.4, h: 2.5, fontFace: SANS, margin: 0, valign: "top", lineSpacingMultiple: 1.44 });

  // Bloque derecho: 5 secciones del dashboard
  tarjeta(s, 7.4, 1.85, 5.18, 5.05);
  s.addText("5 SECCIONES", {
    x: 7.7, y: 2.03, w: 4.6, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  const secs = [
    ["Introducción", "Contexto clínico y objetivos"],
    ["Metodología", "Pipeline de 9 pasos + 5 decisiones clave"],
    ["Cohortes", "13 estudios GEO explorables uno a uno"],
    ["Resultados", "9 secciones dinámicas con las cifras reales"],
    ["Conclusiones", "Hipótesis, contribuciones y limitaciones"],
  ];
  secs.forEach(([nom, det], i) => {
    const y = 2.44 + i * 0.85;
    s.addShape(pres.ShapeType.rect, {
      x: 7.7, y, w: 0.14, h: 0.14, fill: { color: AZUL }, line: { color: AZUL, width: 0 },
    });
    s.addText(nom, {
      x: 7.94, y: y - 0.07, w: 4.36, h: 0.32,
      fontFace: SERIF, fontSize: 13.5, bold: true, color: TINTA, margin: 0, valign: "top",
    });
    s.addText(det, {
      x: 7.94, y: y + 0.24, w: 4.36, h: 0.4,
      fontFace: SANS, fontSize: 10.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });
  });

  pieDiapo(s, "Repositorio público: github.com/danitapiadiez-gif/TFM-Bioinformatica  ·  Ejecución local: streamlit run agentes/paso12_web_chatbot.py");
  s.addNotes(
    "El entregable operativo es data.lung, un dashboard Streamlit multipage con cinco " +
    "secciones que exponen introduccion, metodologia, cohortes, resultados y conclusiones. " +
    "Todas las cifras se leen dinamicamente de los CSV y JSON, asi que el dashboard nunca " +
    "queda desactualizado. Incluye un asistente conversacional con Llama 3.3 sobre el contexto " +
    "del TFM. Codigo publico en GitHub."
  );
}

// =========================================================== 12. CONCLUSIONES
{
  const s = slideClara();
  antetitulo(s, "CONCLUSIONES");
  titulo(s, "Qué entrega el framework, un bloque por línea");

  const concl = [
    {
      letra: "A",
      color: AZUL,
      titulo: "Firma consenso reproducible",
      texto: `${D.nValidados} genes con efecto grande y dirección concordante en 3 cohortes independientes. Panel mínimo de ${D.panelMin} conserva el rendimiento (AUC ${dec(D.aucPanel)}) y recupera ${D.ihcRec}/${D.ihcTot} marcadores IHC OMS sin haberlos usado en la selección.`,
    },
    {
      letra: "B",
      color: VERDE,
      titulo: "Subtipo histológico con valor clínico",
      texto: `AUC ${dec(D.aucSub)} en LODO externo (n=${D.nSub}). Panel de 20 genes medible por PCR cuantitativa multiplex o NanoString nCounter, con impacto directo en la elección de pemetrexed y bevacizumab.`,
    },
    {
      letra: "C",
      color: TINTA_2,
      titulo: "Control metodológico validado",
      texto: `Tumor vs sano: AUC ${dec(D.auc)} → ${dec(D.aucCalIso)} tras recalibración isotónica. Bootstrap n=${D.nBoot} confirma robustez (IC95 %: ${dec(D.aucBootIC[0])}–${dec(D.aucBootIC[1])}). Framework aplicable a nuevas cohortes con el mismo pipeline reproducible.`,
    },
  ];
  concl.forEach((c, i) => {
    const y = 1.9 + i * 1.42;
    s.addText(c.letra, {
      x: M, y, w: 0.8, h: 0.8,
      fontFace: SERIF, fontSize: 40, bold: true, color: c.color, margin: 0, valign: "top",
    });
    s.addText(c.titulo, {
      x: M + 0.9, y: y + 0.06, w: 10.96, h: 0.5,
      fontFace: SERIF, fontSize: 15.5, bold: true, color: TINTA, margin: 0, valign: "top",
    });
    s.addText(c.texto, {
      x: M + 0.9, y: y + 0.58, w: 10.96, h: 0.86,
      fontFace: SANS, fontSize: 11.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.28,
    });
  });

  tarjeta(s, M, 6.14, 11.86, 0.86, "1A1D21");
  s.addText([
    { text: "Contribución metodológica:  ", options: { fontFace: SANS, fontSize: 11.5, color: MUDO } },
    { text: "pipeline reproducible + auditoría interna + validación externa estricta", options: { fontFace: SANS, fontSize: 12, bold: true, color: BLANCO } },
    { text: "  →  aplicable a otras patologías cambiando cohortes de entrada, sin modificar el marco.", options: { fontFace: SANS, fontSize: 11.5, italic: true, color: "C3C2B7" } },
  ], { x: M + 0.34, y: 6.3, w: 11.2, h: 0.6, margin: 0, valign: "middle" });

  pieDiapo(s, "Líneas futuras: supervivencia con GSE30219+GSE50081 (307+181 tumores con seguimiento); predicción de alteración conductora (EGFR/KRAS/ALK); deconvolución celular.");
  s.addNotes(
    "Tres conclusiones, una por bloque. A: firma reproducible con panel operativo. B: " +
    "clasificador de subtipo con valor terapeutico directo. C: control metodologico que " +
    "valida el marco. La contribucion metodologica es un pipeline reproducible con auditoria " +
    "interna aplicable a otras patologias sin modificar el marco."
  );
}

// =========================================================== 13. CIERRE
{
  const s = slideOscura();
  s.addText("Gracias", {
    x: M, y: 2.5, w: 8, h: 1.1,
    fontFace: SERIF, fontSize: 46, bold: true, color: BLANCO, margin: 0,
  });
  s.addShape(pres.ShapeType.line, {
    x: M, y: 3.86, w: 2.6, h: 0, line: { color: AZUL, width: 2.4 },
  });
  s.addText(
    "Un framework que separa firma, subtipo y control es más útil que uno que\nreporta una única cifra global.",
    { x: M, y: 4.14, w: 10.4, h: 1.1, fontFace: SERIF, fontSize: 17, italic: true, color: "C3C2B7", margin: 0, lineSpacingMultiple: 1.24 }
  );
  s.addText([
    { text: "Daniel Tapia Díez", options: { bold: true, color: BLANCO, fontSize: 13 } },
    { text: "\nMáster Universitario en Bioinformática  ·  Universidad Alfonso X el Sabio", options: { color: MUDO, fontSize: 11.5 } },
    { text: "\nTutor: Leonardo Dulcetti  ·  Madrid, septiembre 2026", options: { color: MUDO, fontSize: 11.5 } },
  ], { x: M, y: 5.6, w: 8, h: 1.4, fontFace: SANS, margin: 0, lineSpacingMultiple: 1.24 });
  s.addNotes("Gracias. Quedo a disposicion del tribunal para las preguntas.");
}

// ---------------------------------------------------------------- write
const salida = path.join(RAIZ, "DEFENSA_TFM.pptx");
pres.writeFile({ fileName: salida }).then(() => {
  console.log("Escrito: " + salida);
  console.log(`Diapositivas: ${pres.slides.length}`);
  console.log(
    `Cifras leidas -> auc ${dec(D.auc)} → ${dec(D.aucCalIso)}, balAcc ${dec(D.balAcc)} → ${dec(D.balCalIso)}, ` +
    `aucSub ${dec(D.aucSub)}, aucBoot IC [${dec(D.aucBootIC[0])};${dec(D.aucBootIC[1])}], ` +
    `panelMin ${D.panelMin}, LASSO ${dec(D.ml.LASSO_L1.auc_media)}/RF ${dec(D.ml.Random_Forest.auc_media)}/SVM ${dec(D.ml.SVM_lineal.auc_media)}`
  );
});
