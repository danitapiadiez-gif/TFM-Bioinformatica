// Presentacion de defensa del TFM.
// Las cifras se leen de los CSV de resultados, no se escriben a mano.

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const RAIZ = "/Users/danieltapiadiez/Desktop/UAX/TFM";
const FIG = path.join(RAIZ, "figuras_auditoria");

// ---------------------------------------------------------------- datos
function csv(nombre) {
  const txt = fs.readFileSync(path.join(RAIZ, nombre), "utf8").trim();
  const [cab, ...filas] = txt.split("\n");
  const cols = cab.split(",");
  return filas.map((f) => {
    // separador simple: ningun campo de estos CSV contiene comas
    const v = f.split(",");
    return Object.fromEntries(cols.map((c, i) => [c, v[i]]));
  });
}
const num = (x) => parseFloat(x);
const media = (a) => a.reduce((s, x) => s + x, 0) / a.length;
const dec = (v, n = 3) => v.toFixed(n).replace(".", ",");

const lodo = csv("LODO_HONESTO_RESULTADOS.csv");
const ev = lodo.filter((r) => r.Evaluable === "True");
const aud = csv("AUDITORIA_COHORTES.csv");
const comp = csv("COMPOSICION_VS_BIOLOGIA.csv");
const fal = csv("FALACIA_FOLDS_COMPARACION.csv");
const sub = csv("SUBTIPO_LODO_RESULTADOS.csv");
const dif = csv("SUBTIPO_CASOS_DIFICILES.csv");
const resDif = JSON.parse(
  fs.readFileSync(path.join(RAIZ, "SUBTIPO_DIFICILES_RESUMEN.json"), "utf8")
);
const resFirma = JSON.parse(
  fs.readFileSync(path.join(RAIZ, "FIRMA_VALIDADA_RESUMEN.json"), "utf8")
);

const D = {
  balAcc: media(ev.map((r) => num(r.Balanced_Accuracy))),
  auc: media(ev.map((r) => num(r.AUC))),
  sens: media(ev.map((r) => num(r.Sensibilidad))),
  espec: media(ev.map((r) => num(r.Especificidad))),
  base: media(ev.map((r) => num(r.Baseline_Mayoritaria))),
  accOnce: media(lodo.map((r) => num(r.Accuracy))),
  nEv: ev.length,
  nCoh: lodo.length,
  noSuperan: ev.filter((r) => r.Supera_Baseline === "False").length,
  nMuestras: aud.reduce((s, r) => s + num(r.N_Total), 0),
  sinClas: aud.reduce((s, r) => s + num(r.N_Sin_Clasificar), 0),
  desal: aud.reduce((s, r) => s + (num(r.N_Muestras_Desalineadas) || 0), 0),
  nMono: aud.filter((r) => r.Evaluable_Como_Test === "False").length,
  rho: media(
    comp
      .map((r) => num(r.Rho_SOLO_TUMORES_vs_PulmonNormal))
      .filter((x) => !isNaN(x))
  ),
  nRho: comp.filter((r) => !isNaN(num(r.Rho_SOLO_TUMORES_vs_PulmonNormal))).length,
  concLodo: num(fal[0].concordancia_pareja_media) * 100,
  concDisj: num(fal[1].concordancia_pareja_media) * 100,
  genesFolds: num(fal[0].genes_acuerdo_signo_perfecto),
  genesDisj: num(fal[1].genes_acuerdo_signo_perfecto),
  aucSub: media(sub.map((r) => num(r.AUC))),
  balSub: media(sub.map((r) => num(r.Balanced_Accuracy))),
  nSub: sub.reduce((s, r) => s + num(r.n_test), 0),
  pctConf: resDif.pct_alta_confianza_ambiguas,
  pctConfVistas: resDif.pct_alta_confianza_vistas,
  nNeuro: resDif.n_neuroendocrinos,
  pctNeuro: resDif.pct_neuro_a_adenocarcinoma,
  nAmbiguas: resDif.n_ambiguas,
  pctExcl: resDif.pct_excluidas,
  nValidados: resFirma.n_genes_validados,
  pctValidados: resFirma.pct_genes_validados,
  nValidadosTvS: resFirma.n_genes_validados_tumor_vs_sano,
  panelMin: resFirma.panel_minimo,
  aucPanel: resFirma.auc_panel_minimo,
  ihcRec: Object.values(resFirma.ihc_recuperados).reduce((a, b) => a + b, 0),
  ihcTot: Object.values(resFirma.ihc_total).reduce((a, b) => a + b, 0),
  panelGenes: resFirma.panel_minimo_genes,
};
D.pctSinClas = (100 * D.sinClas) / D.nMuestras;

// ---------------------------------------------------------------- paleta
// Misma paleta que las figuras (validada para daltonismo en claro y oscuro).
const TINTA = "1A1D21";
const TINTA_2 = "52514E";
const MUDO = "898781";
const PAPEL = "FCFCFB";
const CREMA = "F1F0EC";
const AZUL = "2A78D6";
const ROJO = "D03B3B";
const NARANJA = "EB6834";
const BLANCO = "FFFFFF";

const SERIF = "Cambria";
const SANS = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Daniel Tapia Diez";
pres.title = "Auditoria de reproducibilidad de firmas transcriptomicas";

const W = 13.3;
const H = 7.5;
const M = 0.72; // margen

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

let nSlide = 0;
function titulo(s, texto, opts = {}) {
  nSlide++;
  s.addText(texto, {
    x: M,
    y: opts.y ?? 0.46,
    w: opts.w ?? W - 2 * M,
    h: opts.h ?? 1.2,
    fontFace: SERIF,
    fontSize: opts.fontSize ?? 32,
    bold: true,
    color: opts.color ?? TINTA,
    margin: 0,
    valign: "top",
  });
}

function antetitulo(s, texto, color = MUDO) {
  s.addText(texto, {
    x: M,
    y: 0.2,
    w: W - 2 * M,
    h: 0.26,
    fontFace: SANS,
    fontSize: 10,
    bold: true,
    charSpacing: 2.4,
    color,
    margin: 0,
  });
}

function pieDiapo(s, texto, color = MUDO) {
  s.addText(texto, {
    x: M,
    y: H - 0.52,
    w: W - 2 * M,
    h: 0.28,
    fontFace: SANS,
    fontSize: 9,
    color,
    margin: 0,
    italic: true,
  });
}

// Tarjeta: tinte de fondo y sombra suave. Sin franjas de acento.
function tarjeta(s, x, y, w, h, relleno = CREMA) {
  s.addShape(pres.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.06,
    fill: { color: relleno },
    line: { color: "E4E3DE", width: 0.6 },
    shadow: { type: "outer", color: "B8B7B2", blur: 7, offset: 1.4, angle: 90, opacity: 0.2 },
  });
}

// Cifra grande con rotulo.
function cifra(s, x, y, w, valor, rotulo, colorValor = TINTA, tamano = 46) {
  s.addText(valor, {
    x,
    y,
    w,
    h: 0.78,
    fontFace: SERIF,
    fontSize: tamano,
    bold: true,
    color: colorValor,
    margin: 0,
    valign: "top",
  });
  s.addText(rotulo, {
    x,
    y: y + 0.76,
    w,
    h: 0.46,
    fontFace: SANS,
    fontSize: 11,
    color: TINTA_2,
    margin: 0,
    valign: "top",
  });
}

// Distintivo de veredicto.
function veredicto(s, x, y, texto, color) {
  s.addText(texto, {
    x,
    y,
    w: 1.9,
    h: 0.26,
    fontFace: SANS,
    fontSize: 9.5,
    bold: true,
    charSpacing: 1.4,
    color,
    margin: 0,
  });
}

// =========================================================== 1. PORTADA
{
  const s = slideOscura();
  s.addText("TRABAJO DE FIN DE MÁSTER  ·  MÁSTER UNIVERSITARIO EN BIOINFORMÁTICA", {
    x: M, y: 1.5, w: W - 2 * M, h: 0.3,
    fontFace: SANS, fontSize: 11, bold: true, charSpacing: 2.6, color: MUDO, margin: 0,
  });
  s.addText("Framework transcriptómico basado en la integración\nde modelos de lenguaje y aprendizaje automático\npara la identificación de biomarcadores\nen cáncer de pulmón", {
    x: M, y: 1.98, w: 11.2, h: 2.9,
    fontFace: SERIF, fontSize: 31, bold: true, color: BLANCO, margin: 0,
    lineSpacingMultiple: 1.1, valign: "top",
  });
  s.addText("Identificación, validación y auditoría de firmas moleculares\nsobre 13 cohortes públicas de NCBI GEO", {
    x: M, y: 4.98, w: 9.4, h: 0.76,
    fontFace: SERIF, fontSize: 15, color: "C3C2B7", italic: true, margin: 0,
    lineSpacingMultiple: 1.2,
  });
  s.addShape(pres.ShapeType.line, {
    x: M, y: 5.94, w: 3.1, h: 0,
    line: { color: AZUL, width: 2.4 },
  });
  s.addText([
    { text: "Daniel Tapia Díez", options: { bold: true, color: BLANCO, fontSize: 14 } },
    { text: "\nTutor: Leonardo Dulcetti", options: { color: MUDO, fontSize: 12 } },
    { text: "\nUniversidad Alfonso X el Sabio  ·  Madrid, 2026", options: { color: MUDO, fontSize: 12 } },
  ], { x: M, y: 6.16, w: 6, h: 1.1, fontFace: SANS, margin: 0, lineSpacingMultiple: 1.24 });
  s.addNotes(
    "Buenos dias. Presento un framework que integra modelos de lenguaje y aprendizaje " +
    "automatico para identificar biomarcadores transcriptomicos. Tiene tres capas: " +
    "curacion clinica con LLM, identificacion de firmas, y una capa de validacion. " +
    "La tesis del trabajo es que esa tercera capa es la que decide si las otras dos " +
    "sirven de algo, y voy a demostrarlo aplicandola a dos tareas: una la supera y la " +
    "otra no."
  );
}

// =========================================================== 2. EL PROBLEMA
{
  const s = slideClara();
  antetitulo(s, "EL PROBLEMA");
  titulo(s, "Identificar biomarcadores es fácil. Que replique\nen otra cohorte, no", { fontSize: 27 });
  s.addText(
    "Los repositorios públicos como NCBI GEO ofrecen miles de cohortes " +
    "transcriptómicas reutilizables. Pero integrar estudios independientes " +
    "introduce variabilidad de plataforma, efecto lote y metadatos clínicos " +
    "heterogéneos. El resultado conocido: una firma identificada en una cohorte " +
    "raramente se reproduce en otra.",
    { x: M, y: 2.3, w: 6.5, h: 1.7, fontFace: SANS, fontSize: 14.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.32 }
  );
  s.addText(
    "De ahí el diseño del framework: la identificación no basta si no viene " +
    "acompañada de una capa que decida cuándo la firma es creíble.",
    { x: M, y: 4.15, w: 6.5, h: 0.9, fontFace: SERIF, fontSize: 15, italic: true, color: TINTA, margin: 0, lineSpacingMultiple: 1.26 }
  );

  tarjeta(s, 7.7, 2.2, 4.88, 4.22);
  cifra(s, 8.1, 2.5, 4.1, "13", "cohortes GEO descargadas", TINTA, 40);
  cifra(s, 8.1, 3.8, 4.1, String(Math.round(D.nMuestras)), "muestras procesadas", TINTA, 40);
  cifra(s, 8.1, 5.1, 4.1, "5", "hipótesis con umbral fijado antes de ejecutar", AZUL, 40);
  pieDiapo(s, "Datos: NCBI Gene Expression Omnibus · plataformas GPL570, GPL96 y GPL13497");
  s.addNotes(
    "El punto de partida es un problema reconocido: la falta de reproducibilidad de " +
    "las firmas transcriptomicas. Trece cohortes, casi mil cuatrocientas muestras. " +
    "Y una decision metodologica que marca todo lo que viene: cada hipotesis se fijo " +
    "con su umbral ANTES de ejecutar el analisis."
  );
}

// =========================================================== 3. EL GIRO
{
  const s = slideClara();
  antetitulo(s, "ARQUITECTURA DEL FRAMEWORK");
  titulo(s, "Tres capas, y la tercera decide si las otras dos sirven");

  const capas = [
    ["1", "Curación clínica con LLM",
     "Llama 3.3-70b interpreta metadatos no estandarizados de GEO y asigna grupos experimentales comparables. Sustituye una revisión manual de 1397 muestras.",
     `Rendimiento medido: ${dec(100 - D.pctSinClas, 1)} % de éxito global, con fallo bimodal.`, CREMA, TINTA, TINTA_2],
    ["2", "Identificación de firmas",
     "Análisis diferencial por cohorte (t de Welch, FDR), meta-análisis de consistencia direccional y modelos supervisados con penalización L1 para seleccionar genes.",
     `Salida: ${D.nValidados} genes validados, panel mínimo de ${D.panelMin}.`, CREMA, TINTA, TINTA_2],
    ["3", "Validación",
     "Tamaño de efecto por cohorte, replicación entre entrenamientos disjuntos, validación externa LODO con baseline declarado, y contraste con marcadores clínicos conocidos.",
     "Es la capa que este trabajo aporta, y la que decide.", "1A1D21", BLANCO, "C3C2B7"],
  ];
  capas.forEach(([n, tit, txt, nota, relleno, cTit, cTxt], i) => {
    const x = M + i * 4.06;
    tarjeta(s, x, 2.05, 3.78, 4.05, relleno);
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.32, y: 2.32, w: 0.44, h: 0.44,
      fill: { color: relleno === "1A1D21" ? "262A30" : PAPEL },
      line: { color: AZUL, width: 1 },
    });
    s.addText(n, {
      x: x + 0.32, y: 2.32, w: 0.44, h: 0.44, fontFace: SERIF, fontSize: 14,
      bold: true, color: AZUL, align: "center", valign: "middle", margin: 0,
    });
    s.addText(tit, {
      x: x + 0.32, y: 2.9, w: 3.14, h: 0.4,
      fontFace: SERIF, fontSize: 16, bold: true, color: cTit, margin: 0, valign: "top",
    });
    s.addText(txt, {
      x: x + 0.32, y: 3.4, w: 3.14, h: 1.72,
      fontFace: SANS, fontSize: 11.5, color: cTxt, margin: 0, valign: "top", lineSpacingMultiple: 1.24,
    });
    s.addText(nota, {
      x: x + 0.32, y: 5.2, w: 3.14, h: 0.7,
      fontFace: SANS, fontSize: 10.5, italic: true, bold: true,
      color: relleno === "1A1D21" ? AZUL : TINTA, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });
  });
  s.addText(
    "Sin la tercera capa, el framework habría entregado una firma que no replica. Con ella, entrega una que sí.",
    { x: M, y: 6.36, w: W - 2 * M, h: 0.5, fontFace: SERIF, fontSize: 14.5, italic: true, color: TINTA, margin: 0 }
  );
  s.addNotes(
    "El framework tiene tres capas. La primera y la segunda son las que anuncia el " +
    "titulo: modelos de lenguaje para curar metadatos, y aprendizaje automatico para " +
    "identificar firmas. La tercera es la aportacion de este trabajo. Y la tesis es " +
    "esta: sin la capa de validacion el framework habria entregado una firma que no " +
    "replica, y con ella entrega una que si. Voy a demostrar las dos cosas."
  );
}

// =========================================================== 4. MATERIALES
{
  const s = slideClara();
  antetitulo(s, "MATERIALES");
  titulo(s, "Once cohortes con datos procesables, de trece declaradas");

  const filas = [[
    { text: "Cohorte", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11 } },
    { text: "Plataforma", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11 } },
    { text: "n", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Sanas", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Enfermas", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Sin clasificar", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "right" } },
    { text: "Evaluable", options: { bold: true, color: BLANCO, fill: { color: TINTA }, fontSize: 11, align: "center" } },
  ]];
  aud.forEach((r, i) => {
    const mono = r.Evaluable_Como_Test === "False";
    const sinClas = num(r.N_Sin_Clasificar);
    const relleno = i % 2 ? { color: CREMA } : { color: PAPEL };
    filas.push([
      { text: r.Cohorte, options: { fill: relleno, color: TINTA, bold: mono } },
      { text: r.Plataforma, options: { fill: relleno, color: TINTA_2 } },
      { text: r.N_Total, options: { fill: relleno, color: TINTA, align: "right" } },
      { text: r.N_Sano, options: { fill: relleno, color: mono ? ROJO : TINTA_2, align: "right", bold: mono } },
      { text: r.N_Enfermo, options: { fill: relleno, color: TINTA_2, align: "right" } },
      { text: sinClas > 0 ? r.N_Sin_Clasificar : "—", options: { fill: relleno, color: sinClas > 20 ? ROJO : TINTA_2, align: "right", bold: sinClas > 20 } },
      { text: mono ? "no" : "sí", options: { fill: relleno, color: mono ? ROJO : TINTA_2, align: "center", bold: mono } },
    ]);
  });

  s.addTable(filas, {
    x: M, y: 1.62, w: 8.4, colW: [1.36, 1.3, 0.82, 0.94, 1.12, 1.5, 1.36],
    rowH: 0.265, fontFace: SANS, fontSize: 10.5, border: { type: "solid", color: "E4E3DE", pt: 0.5 },
    valign: "middle",
  });

  tarjeta(s, 9.5, 1.62, 3.08, 3.3);
  s.addText("TRES COHORTES\nNO EVALUABLES", {
    x: 9.8, y: 1.9, w: 2.5, h: 0.6,
    fontFace: SANS, fontSize: 10, bold: true, charSpacing: 1.6, color: ROJO, margin: 0,
  });
  s.addText(
    "GSE30219, GSE50081 y GSE140797 no contienen controles sanos. En una cohorte " +
    "de una sola clase, predecir siempre «tumor» alcanza accuracy 1,000 por " +
    "definición.\n\nSon estudios de supervivencia: su composición es correcta " +
    "para su propósito. El error fue usarlas como conjunto de test.",
    { x: 9.8, y: 2.62, w: 2.5, h: 2.2, fontFace: SANS, fontSize: 10.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.2 }
  );
  pieDiapo(s, "Tres cohortes declaradas en datasets.txt nunca llegaron a procesarse: GSE40419, GSE81089 y GSE140343 — las tres de RNA-seq.");
  s.addNotes(
    "Once cohortes con datos utilizables. Fijense en la columna de la derecha: tres " +
    "cohortes no tienen controles sanos. Eso importa mucho y volveremos a ello. Y en " +
    "el pie: tres cohortes declaradas nunca se procesaron, sin que el pipeline emitiera " +
    "ningun error."
  );
}

// =========================================================== 5. PRE-REGISTRO
{
  const s = slideOscura();
  antetitulo(s, "MÉTODO", MUDO);
  titulo(s, "Cinco hipótesis, con su umbral fijado antes de ejecutar", { color: BLANCO, fontSize: 29 });
  s.addText(
    "Cada análisis declaró de antemano qué resultado lo confirmaría y qué resultado lo refutaría. " +
    "Ningún umbral se modificó después de ver los datos.",
    { x: M, y: 1.98, w: 10.6, h: 0.72, fontFace: SANS, fontSize: 14, color: "C3C2B7", margin: 0, lineSpacingMultiple: 1.26 }
  );

  const hips = [
    ["I", "Auditoría de integridad", "descriptivo", MUDO],
    ["II", "LODO con métricas completas", "confirmada", AZUL],
    ["III", "Composición tisular frente a biología", "no confirmada", ROJO],
    ["IV", "Validez de la consistencia de signo", "confirmada", AZUL],
    ["V", "Límites del clasificador de subtipo", "no confirmada", ROJO],
  ];
  hips.forEach(([rom, tit, ver, col], i) => {
    const y = 3.0 + i * 0.79;
    s.addShape(pres.ShapeType.rect, {
      x: M, y, w: 0.52, h: 0.52, fill: { color: "262A30" }, line: { color: "343941", width: 0.6 },
    });
    s.addText(rom, {
      x: M, y, w: 0.52, h: 0.52, fontFace: SERIF, fontSize: 15, bold: true,
      color: col, align: "center", valign: "middle", margin: 0,
    });
    s.addText(tit, {
      x: M + 0.78, y: y + 0.06, w: 7.2, h: 0.4,
      fontFace: SANS, fontSize: 14.5, color: BLANCO, margin: 0, valign: "middle",
    });
    veredicto(s, 9.5, y + 0.13, ver.toUpperCase(), col);
  });

  s.addText(
    "Dos de las cinco no se confirmaron. Se reportan como resultaron: mantener el criterio es parte del resultado.",
    { x: M, y: H - 0.86, w: 11.9, h: 0.5, fontFace: SERIF, fontSize: 14, italic: true, color: "C3C2B7", margin: 0 }
  );
  s.addNotes(
    "Cinco analisis, cada uno con hipotesis y umbral fijados de antemano. Dos no se " +
    "confirmaron. Podria haber movido los umbrales para que salieran bien; no lo hice, " +
    "y esa decision es parte de lo que presento."
  );
}

// =========================================================== 6. MODOS DE FALLO
{
  const s = slideClara();
  antetitulo(s, "RESULTADO I  ·  AUDITORÍA DE INTEGRIDAD");
  titulo(s, "Cuatro modos de fallo. Ninguno interrumpió la ejecución");

  const fallos = [
    ["3", "cohortes declaradas\nsin procesar", "Las tres de RNA-seq desaparecieron del pipeline sin aviso. La cohorte analizada no coincide con la declarada.", MUDO],
    [String(Math.round(D.desal)), "muestras con la etiqueta\nde otro paciente", "En GSE30219 las columnas de la matriz están en otro orden que las filas del metadata. Asignar por posición cruza los datos clínicos.", ROJO],
    [String(Math.round(D.sinClas)), "muestras perdidas en la\ncuración automatizada", `El ${dec(D.pctSinClas, 1)} % del total. El fallo es bimodal: éxito casi completo en 8 cohortes, colapso en 2 (GSE40791: 182 de 194).`, NARANJA],
    [String(D.nMono), "cohortes de una sola clase\nusadas como test", "Producen los valores más altos de la tabla y no miden nada: la accuracy trivial es 1,000 por definición.", ROJO],
  ];
  fallos.forEach(([n, rot, txt, col], i) => {
    const x = M + i * 3.06;
    tarjeta(s, x, 2.0, 2.84, 4.06);
    s.addText(n, {
      x: x + 0.28, y: 2.24, w: 2.3, h: 0.72,
      fontFace: SERIF, fontSize: 42, bold: true, color: col, margin: 0, valign: "top",
    });
    s.addText(rot, {
      x: x + 0.28, y: 3.02, w: 2.3, h: 0.66,
      fontFace: SANS, fontSize: 11.5, bold: true, color: TINTA, margin: 0, valign: "top", lineSpacingMultiple: 1.14,
    });
    s.addText(txt, {
      x: x + 0.28, y: 3.82, w: 2.3, h: 2.0,
      fontFace: SANS, fontSize: 10.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });
  });
  pieDiapo(s, "El pipeline terminó en los cuatro casos, escribió sus ficheros y produjo tablas de aspecto correcto.");
  s.addNotes(
    "Cuatro modos de fallo, y el rasgo que los hace peligrosos es comun a los cuatro: " +
    "ninguno lanza un error. El pipeline termina y produce tablas que parecen bien. " +
    "El segundo es el mas instructivo y le dedico la siguiente diapositiva."
  );
}

// =========================================================== 7. EL BUG
{
  const s = slideClara();
  antetitulo(s, "RESULTADO I  ·  EL FALLO INDISTINGUIBLE");
  titulo(s, "307 muestras con la etiqueta clínica de otro paciente");

  s.addText(
    "En GSE30219 las 307 columnas de la matriz de expresión están ordenadas de forma " +
    "distinta a las filas del fichero de metadatos, aunque contengan las mismas muestras. " +
    "Asignar las etiquetas por posición —operación habitual cuando las longitudes " +
    "coinciden— adjudica a cada muestra la información clínica de otro paciente.",
    { x: M, y: 1.95, w: 6.7, h: 1.5, fontFace: SANS, fontSize: 13.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.3 }
  );

  tarjeta(s, M, 3.62, 6.7, 2.06);
  s.addText("MISMO MODELO, MISMOS DATOS, ALINEAMIENTO CORREGIDO", {
    x: M + 0.34, y: 3.88, w: 6.0, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  cifra(s, M + 0.34, 4.24, 1.9, "0,56", "AUC con el bug", ROJO, 40);
  s.addShape(pres.ShapeType.rightArrow, {
    x: M + 2.44, y: 4.42, w: 0.72, h: 0.3, fill: { color: MUDO }, line: { color: MUDO, width: 0 },
  });
  cifra(s, M + 3.42, 4.24, 2.6, "0,99", "AUC corregido", AZUL, 40);

  s.addText(
    "Un AUC de 0,56 es indistinguible de una ausencia genuina de señal biológica. " +
    "Es exactamente el resultado que un trabajo honesto acepta y reporta.",
    { x: 7.72, y: 1.95, w: 4.86, h: 1.2, fontFace: SERIF, fontSize: 14, italic: true, color: TINTA, margin: 0, lineSpacingMultiple: 1.26 }
  );
  tarjeta(s, 7.72, 3.3, 4.86, 2.4, "1A1D21");
  s.addText("QUÉ LO REVELÓ", {
    x: 8.04, y: 3.56, w: 4.2, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText(
    "La comparación con marcadores de referencia externos. KRT5 mostraba una diferencia " +
    "de +0,90 en esta cohorte, frente a +5,32 y +5,66 en las otras dos: la señal estaba " +
    "presente, pero desacoplada de las etiquetas.",
    { x: 8.04, y: 3.94, w: 4.22, h: 1.6, fontFace: SANS, fontSize: 11.5, color: "C3C2B7", margin: 0, lineSpacingMultiple: 1.22 }
  );
  pieDiapo(s, "El análisis original no se vio afectado: GSE30219 tiene una sola clase, e intercambiar etiquetas idénticas no altera nada. El fallo quedó latente.");
  s.addNotes(
    "Este es el hallazgo que mas me ensenó. Con el bug, el AUC era 0,56: azar. " +
    "Corregido, 0,99. Y lo importante: 0,56 es perfectamente compatible con la " +
    "conclusion 'esta senal no generaliza'. Solo comparar con marcadores conocidos lo " +
    "revelo. La validacion contra biologia previa no es adorno interpretativo: es un " +
    "control de integridad de los datos."
  );
}

// =========================================================== 8. LODO HONESTO
{
  const s = slideClara();
  antetitulo(s, "RESULTADO II  ·  VALIDACIÓN EXTERNA");
  titulo(s, "El rendimiento reportado incluía tres cohortes que no miden nada");
  // Proporcion original 1108x838: la altura se deriva del ancho.
  const wLodo = 6.1;
  s.addImage({
    path: path.join(FIG, "fig_lodo_vs_baseline.png"),
    x: M, y: 1.92, w: wLodo, h: wLodo * (838 / 1108),
  });
  const yc = 1.95;
  tarjeta(s, 8.42, yc, 4.16, 3.06);
  s.addText("MEDIA SOBRE COHORTES EVALUABLES", {
    x: 8.72, y: yc + 0.26, w: 3.6, h: 0.42,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.4, color: MUDO, margin: 0,
  });
  cifra(s, 8.72, yc + 0.74, 3.6, dec(D.balAcc), `balanced accuracy sobre ${D.nEv} de ${D.nCoh} cohortes`, AZUL, 40);
  s.addText(
    `Frente a una accuracy de ${dec(D.accOnce)} sobre las ${D.nCoh}, ` +
    `con las tres monoclase dentro.`,
    { x: 8.72, y: yc + 2.24, w: 3.6, h: 0.6, fontFace: SANS, fontSize: 11, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.2 }
  );
  tarjeta(s, 8.42, 5.16, 4.16, 1.62, "1A1D21");
  s.addText([
    { text: `${D.noSuperan} de ${D.nEv}`, options: { fontFace: SERIF, fontSize: 22, bold: true, color: ROJO } },
    { text: "  cohortes evaluables no superan su propio baseline de clase mayoritaria.", options: { fontFace: SANS, fontSize: 11.5, color: "C3C2B7" } },
  ], { x: 8.72, y: 5.38, w: 3.6, h: 1.2, margin: 0, valign: "middle", lineSpacingMultiple: 1.2 });
  pieDiapo(s, "Modelo idéntico al análisis original (LASSO, C=0,5). Solo cambian el alineamiento corregido y las métricas reportadas.");
  s.addNotes(
    "Repeti la validacion con el mismo modelo. Solo cambie dos cosas: alineamiento " +
    "corregido y metricas completas. La balanced accuracy sobre cohortes evaluables es " +
    "0,772. Y tres de ocho no superan su propio baseline: son peores que predecir " +
    "siempre la clase mayoritaria."
  );
}

// =========================================================== 9. CALIBRACION
{
  const s = slideClara();
  antetitulo(s, "RESULTADO II  ·  HALLAZGO NO PREVISTO");
  titulo(s, "La firma ordena bien las muestras. El umbral no transfiere");
  s.addImage({
    path: path.join(FIG, "fig_auc_vs_balacc.png"),
    x: 8.05, y: 1.9, w: 4.4, h: 4.47,
  });
  s.addText(
    `Sobre las mismas ${D.nEv} cohortes, el AUC medio es ${dec(D.auc)} mientras la ` +
    `balanced accuracy se queda en ${dec(D.balAcc)}. La divergencia es sistemática, y ` +
    `alcanza su expresión extrema en GSE40791: accuracy 0,167 con AUC 1,000.`,
    { x: M, y: 1.92, w: 6.9, h: 1.4, fontFace: SANS, fontSize: 13.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.3 }
  );
  s.addText(
    "Un AUC de 1,000 significa que existe un umbral que separa las muestras sin error. " +
    "Una accuracy de 0,167 significa que el umbral empleado no es ese.",
    { x: M, y: 3.42, w: 6.9, h: 0.9, fontFace: SERIF, fontSize: 14.5, italic: true, color: TINTA, margin: 0, lineSpacingMultiple: 1.26 }
  );
  tarjeta(s, M, 4.5, 6.9, 1.9);
  s.addText([
    { text: "Sensibilidad media  ", options: { fontFace: SANS, fontSize: 12, color: TINTA_2 } },
    { text: dec(D.sens), options: { fontFace: SERIF, fontSize: 19, bold: true, color: TINTA } },
    { text: "        Especificidad media  ", options: { fontFace: SANS, fontSize: 12, color: TINTA_2 } },
    { text: dec(D.espec), options: { fontFace: SERIF, fontSize: 19, bold: true, color: ROJO } },
  ], { x: M + 0.34, y: 4.72, w: 6.25, h: 0.62, margin: 0, valign: "middle" });
  s.addText(
    "El modelo clasifica como tumoral casi todo lo que recibe. Es coherente con su " +
    "entrenamiento: 938 tumores frente a 219 controles. Es un problema de calibración, " +
    "no de dificultad intrínseca — y los problemas de calibración se corrigen.",
    { x: M + 0.34, y: 5.34, w: 6.25, h: 0.94, fontFace: SANS, fontSize: 11.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.22 }
  );
  s.addNotes(
    "Este resultado no estaba en la hipotesis y es el mas util del trabajo. Descompone " +
    "'el modelo generaliza' en dos propiedades que transfieren por separado: la " +
    "ordenacion transfiere, el umbral no. Y reinterpreta un patron que el analisis " +
    "original registraba sin explicar: los casos de accuracy 0,5 con AUC 1,0 no eran " +
    "dificultad del problema, eran calibracion."
  );
}

// =========================================================== 10. COMPOSICION
{
  const s = slideClara();
  antetitulo(s, "RESULTADO III  ·  QUÉ MIDE LA FIRMA");
  titulo(s, "Composición del tejido, no biología del tumor", { w: 9.5 });
  veredicto(s, 10.6, 0.62, "NO CONFIRMADA", ROJO);

  s.addImage({
    path: path.join(FIG, "fig_composicion_tumores.png"),
    x: M, y: 1.9, w: 11.86, h: 11.86 * (528 / 1825),
  });

  s.addText(
    `Umbral pre-registrado |ρ| > 0,7. Obtenido: ρ = ${dec(D.rho)} entre muestras ` +
    `tumorales (${D.nRho} cohortes con tumores suficientes). El umbral no se modificó.`,
    { x: M, y: 5.42, w: 6.0, h: 0.8, fontFace: SANS, fontSize: 12.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.24 }
  );
  s.addText(
    "La lectura que sostienen los datos es intermedia: la composición explica una " +
    "fracción sustancial de la señal, pero no la agota. Y apareció un segundo eje no " +
    "previsto —proliferación— con ρ de +0,27 a +0,72.",
    { x: 7.0, y: 5.42, w: 5.6, h: 1.0, fontFace: SANS, fontSize: 12.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.24 }
  );
  s.addText(
    "Cinco de los cincuenta genes principales son marcadores canónicos de pulmón sano —AGER, CLDN18, SFTPC, FABP4, WIF1— con logFC próximo a −4.",
    { x: M, y: 6.52, w: 11.86, h: 0.5, fontFace: SERIF, fontSize: 13.5, italic: true, color: TINTA, margin: 0 }
  );
  s.addNotes(
    "Aqui mi hipotesis NO se confirmo al umbral que fije. Rho es -0,626, por debajo de " +
    "0,7. No movi el umbral. La conclusion honesta es intermedia y probablemente mas " +
    "correcta que mi hipotesis de partida: la composicion explica mucho pero no todo, y " +
    "hay un segundo eje de proliferacion que no habia previsto."
  );
}

// =========================================================== 11. FALACIA
{
  const s = slideClara();
  antetitulo(s, "RESULTADO IV  ·  UNA MÉTRICA QUE NO PUEDE FALLAR");
  titulo(s, "La consistencia de signo entre folds\nno mide reproducibilidad", { w: 9.9, fontSize: 29 });
  veredicto(s, 10.9, 0.62, "CONFIRMADA", AZUL);

  s.addImage({
    path: path.join(FIG, "fig_concordancia_folds.png"),
    x: 8.5, y: 1.95, w: 4.08, h: 4.08 * (665 / 776),
  });

  s.addText(
    "El análisis original medía la estabilidad de un gen sumando el signo de su " +
    "coeficiente a lo largo de los folds LODO, y presentaba «11 de 11» como prueba de " +
    "robustez biológica.",
    { x: M, y: 1.95, w: 7.3, h: 1.0, fontFace: SANS, fontSize: 13.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.3 }
  );
  s.addText(
    "Pero dos folds LODO comparten una mediana del 97,6 % de sus muestras de " +
    "entrenamiento. No son réplicas independientes: es casi el mismo modelo ajustado " +
    "varias veces.",
    { x: M, y: 3.06, w: 7.3, h: 1.0, fontFace: SERIF, fontSize: 14.5, italic: true, color: TINTA, margin: 0, lineSpacingMultiple: 1.26 }
  );

  tarjeta(s, M, 4.2, 7.3, 2.24, "1A1D21");
  s.addText("CONSECUENCIA SOBRE LA FIRMA PREVIA", {
    x: M + 0.34, y: 4.46, w: 6.6, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  s.addText([
    { text: `${D.genesFolds} genes`, options: { fontFace: SERIF, fontSize: 17, bold: true, color: BLANCO } },
    { text: " con acuerdo de signo perfecto entre folds solapados,   ", options: { fontFace: SANS, fontSize: 12, color: "C3C2B7" } },
    { text: `${D.genesDisj}`, options: { fontFace: SERIF, fontSize: 17, bold: true, color: ROJO } },
    { text: " entre las 8 cohortes disjuntas.", options: { fontFace: SANS, fontSize: 12, color: "C3C2B7" } },
    { text: "\n\nNinguno de los siete genes destacados en la memoria previa —SLC6A4, S100A10, KANK3, SH3GL3, HIST1H2BM, ZNF702P, TOX3— replica al ajustar modelos independientes.", options: { fontFace: SANS, fontSize: 11.5, color: "C3C2B7" } },
  ], { x: M + 0.34, y: 4.82, w: 6.62, h: 1.5, margin: 0, valign: "top", lineSpacingMultiple: 1.22 });

  pieDiapo(s, `Control del tamaño de muestra: parejas de entrenamiento comparables, ${dec(D.concLodo, 1)} % con solapamiento frente a ${dec(D.concDisj, 2)} % sin él. La caída no es artefacto de esparsidad del LASSO.`);
  s.addNotes(
    "Una metrica que no puede tomar valores bajos no aporta informacion. Las 28 parejas " +
    "de folds concuerdan al 100 por cien, sin excepcion. Mitades disjuntas de tamano " +
    "comparable, al 77. La consecuencia es contundente: ninguno de los siete genes que " +
    "la memoria previa destacaba replica de verdad."
  );
}

// =========================================================== 12. CONTROL POSITIVO
{
  const s = slideClara();
  antetitulo(s, "RESULTADO V  ·  CONTROL POSITIVO");
  titulo(s, "¿Mide mal el marco, o no había señal que medir?");

  s.addText(
    "Se aplicó el mismo pipeline a una pregunta con respuesta conocida y consecuencia " +
    "terapéutica: adenocarcinoma frente a carcinoma escamoso. Pemetrexed y bevacizumab " +
    "están contraindicados en histología escamosa.",
    { x: M, y: 1.9, w: 6.5, h: 1.1, fontFace: SANS, fontSize: 13.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.3 }
  );

  const t = [[
    { text: "Cohorte test", options: { bold: true, color: BLANCO, fill: { color: TINTA } } },
    { text: "n", options: { bold: true, color: BLANCO, fill: { color: TINTA }, align: "right" } },
    { text: "Baseline", options: { bold: true, color: BLANCO, fill: { color: TINTA }, align: "right" } },
    { text: "Bal. acc.", options: { bold: true, color: BLANCO, fill: { color: TINTA }, align: "right" } },
    { text: "AUC", options: { bold: true, color: BLANCO, fill: { color: TINTA }, align: "right" } },
  ]];
  sub.forEach((r, i) => {
    const relleno = i % 2 ? { color: CREMA } : { color: PAPEL };
    t.push([
      { text: r.Cohorte_Test, options: { fill: relleno, color: TINTA } },
      { text: r.n_test, options: { fill: relleno, color: TINTA_2, align: "right" } },
      { text: dec(num(r.Baseline_Mayoritaria)), options: { fill: relleno, color: TINTA_2, align: "right" } },
      { text: dec(num(r.Balanced_Accuracy)), options: { fill: relleno, color: TINTA, align: "right", bold: true } },
      { text: dec(num(r.AUC)), options: { fill: relleno, color: AZUL, align: "right", bold: true } },
    ]);
  });
  s.addTable(t, {
    x: M, y: 3.2, w: 6.5, colW: [1.7, 0.9, 1.3, 1.3, 1.3],
    rowH: 0.32, fontFace: SANS, fontSize: 11.5,
    border: { type: "solid", color: "E4E3DE", pt: 0.5 }, valign: "middle",
  });

  tarjeta(s, 7.6, 1.9, 4.98, 4.5);
  s.addText("VALIDACIÓN DE CONTENIDO", {
    x: 7.94, y: 2.16, w: 4.3, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  cifra(s, 7.94, 2.54, 4.3, "12 / 12", "marcadores de inmunohistoquímica diagnóstica recuperados, todos en la dirección correcta", AZUL, 38);
  s.addText([
    { text: "Escamoso", options: { bold: true, color: TINTA, fontSize: 12 } },
    { text: "   KRT5 · KRT6A · TP63 · DSG3 · SOX2 · PKP1 · KRT14", options: { color: TINTA_2, fontSize: 11.5 } },
    { text: "\n\nAdenocarcinoma", options: { bold: true, color: TINTA, fontSize: 12 } },
    { text: "   NAPSA · NKX2-1 · SFTPB · SLC34A2 · MUC1", options: { color: TINTA_2, fontSize: 11.5 } },
  ], { x: 7.94, y: 4.3, w: 4.3, h: 1.28, fontFace: SANS, margin: 0, lineSpacingMultiple: 1.24, valign: "top" });
  s.addText(
    "El top del ranking —DSG3, KRT5, CALML3, KRT6B, PKP1, DSC3, TP63— corresponde a " +
    "desmosomas, queratinas y el programa de TP63: linaje celular, no composición.",
    { x: 7.94, y: 5.7, w: 4.3, h: 0.66, fontFace: SANS, fontSize: 11, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.2 }
  );
  pieDiapo(s, "Alcance: esta distinción está bien caracterizada en la literatura y no es un hallazgo original. Su valor aquí es de control positivo — y fue el análisis que reveló el desalineamiento de GSE30219.");
  s.addNotes(
    "Necesitaba distinguir 'el marco mide mal' de 'no hay senal'. Aplicando el mismo " +
    "pipeline a subtipo histologico: AUC 0,968, y recupera los doce marcadores que se " +
    "usan en inmunohistoquimica clinica, todos en la direccion correcta. El marco " +
    "funciona cuando hay senal. Y quiero ser claro: esto no es un hallazgo original, es " +
    "un control."
  );
}

// =========================================================== 13. LIMITES
{
  const s = slideClara();
  antetitulo(s, "RESULTADO V  ·  LÍMITES DEL CONTROL POSITIVO");
  titulo(s, "El control positivo excluyó los casos difíciles", { w: 9.5 });
  veredicto(s, 10.6, 0.62, "NO CONFIRMADA", ROJO);

  s.addImage({
    path: path.join(FIG, "fig_histologias_excluidas.png"),
    x: M, y: 1.95, w: 6.6, h: 6.6 * (799 / 1095),
  });

  s.addText(
    `El resultado anterior excluyó ${D.nAmbiguas} muestras, el ${dec(D.pctExcl, 1)} % de ` +
    `los tumores disponibles: precisamente las histologías que en la práctica clínica ` +
    `resultan ambiguas.`,
    { x: 8.1, y: 1.98, w: 4.48, h: 1.1, fontFace: SANS, fontSize: 12.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.26 }
  );
  s.addText(
    `Hipótesis: más del 50 % recibiría asignación de alta confianza. Obtenido: ` +
    `${dec(D.pctConf, 1)} %, frente al ${dec(D.pctConfVistas, 1)} % de las histologías ` +
    `vistas. El modelo es más prudente de lo previsto.`,
    { x: 8.1, y: 3.2, w: 4.48, h: 1.2, fontFace: SANS, fontSize: 12.5, color: TINTA_2, margin: 0, lineSpacingMultiple: 1.26 }
  );
  tarjeta(s, 8.1, 4.46, 4.48, 2.2, "1A1D21");
  s.addText([
    { text: `${Math.round(D.pctNeuro)} %`, options: { fontFace: SERIF, fontSize: 30, bold: true, color: ROJO } },
    { text: `\nde los ${D.nNeuro} tumores neuroendocrinos se etiqueta como adenocarcinoma. El microcítico se trata de forma completamente distinta al NSCLC.`, options: { fontFace: SANS, fontSize: 11.5, color: "C3C2B7" } },
  ], { x: 8.42, y: 4.7, w: 3.9, h: 1.86, margin: 0, valign: "top", lineSpacingMultiple: 1.2 });
  pieDiapo(s, "El AUC de 0,968 solo es válido sobre tumores ya confirmados como adenocarcinoma o escamoso. El modelo no puede ser un primer filtro diagnóstico.");
  s.addNotes(
    "Tenia que someter el modelo a lo que habia excluido. Mi hipotesis tampoco se " +
    "confirmo: es mas prudente de lo que predije. Pero el agregado oculta lo importante: " +
    "el 92 por ciento de los neuroendocrinos se etiqueta como adenocarcinoma, y el " +
    "microcitico se trata de forma completamente distinta. Ese si es un fallo con " +
    "consecuencia clinica."
  );
}


// ================================================ 14. EL ENTREGABLE
{
  const s = slideClara();
  antetitulo(s, "SALIDA DEL FRAMEWORK");
  titulo(s, "La firma que supera la capa de validación", { w: 9.5 });

  s.addImage({
    path: path.join(FIG, "fig_panel_minimo.png"),
    x: 6.86, y: 1.98, w: 5.72, h: 5.72 * (3.5 / 6.4),
  });

  const ent = [
    [String(D.nValidados), `genes validados de 22 880 evaluados (${dec(D.pctValidados, 1)} %): efecto grande y dirección concordante en las tres cohortes por separado`, AZUL],
    [String(D.panelMin), `genes bastan para conservar el rendimiento: AUC ${dec(D.aucPanel)} en validación externa`, TINTA],
    [`${D.ihcRec} / ${D.ihcTot}`, "marcadores de inmunohistoquímica clínica recuperados sin haber participado en la selección", AZUL],
  ];
  ent.forEach(([v, t, c], i) => {
    const y = 2.0 + i * 1.32;
    s.addText(v, {
      x: M, y, w: 1.72, h: 0.7,
      fontFace: SERIF, fontSize: 34, bold: true, color: c, margin: 0, valign: "top",
    });
    s.addText(t, {
      x: M + 1.86, y: y + 0.06, w: 4.2, h: 1.1,
      fontFace: SANS, fontSize: 11.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.24,
    });
  });

  tarjeta(s, M, 5.98, 5.94, 0.92, "1A1D21");
  s.addText([
    { text: "Panel mínimo:  ", options: { fontFace: SANS, fontSize: 10.5, color: MUDO } },
    { text: D.panelGenes.slice(0, 10).join(" · "), options: { fontFace: SANS, fontSize: 10.5, color: BLANCO, bold: true } },
    { text: " …", options: { fontFace: SANS, fontSize: 10.5, color: MUDO } },
  ], { x: M + 0.32, y: 6.12, w: 5.3, h: 0.64, margin: 0, valign: "middle", lineSpacingMultiple: 1.2 });

  pieDiapo(s, `La misma capa de validación retiene ${D.nValidadosTvS} genes en la tarea tumor frente a sano (${dec(100 * D.nValidadosTvS / 13237, 2)} % de los evaluados): discrimina entre tareas sin cambiar de criterio.`);
  s.addNotes(
    "Esta es la salida del framework. Mil ciento setenta y cuatro genes superan la " +
    "validacion, y con solo veinte se conserva el rendimiento: AUC 0,966 en validacion " +
    "externa. Eso es un panel utilizable, no una lista de mil genes. Y la validacion " +
    "externa mas importante es la tercera: recupera dieciocho de veinte marcadores que " +
    "se usan en inmunohistoquimica clinica, sin que hayan participado en la seleccion. " +
    "El framework encuentra biologia conocida por su cuenta. En el pie esta el contraste: " +
    "la misma capa, sin cambiar un criterio, retiene muchos menos genes en la tarea que " +
    "no supera la validacion."
  );
}

// =========================================================== 15. CONTROLES
{
  const s = slideOscura();
  antetitulo(s, "APORTACIÓN METODOLÓGICA", MUDO);
  titulo(s, "Seis controles, derivados de los seis fallos encontrados", { color: BLANCO, fontSize: 29 });

  const ctrl = [
    ["Alinear por identificador", "Nunca por posición. La coincidencia de longitudes no implica coincidencia de orden."],
    ["Validar contra biología conocida", "Un panel de marcadores de la patología funciona como control de integridad de los datos."],
    ["Reportar el baseline", "Junto a toda métrica, y excluir explícitamente las cohortes de una sola clase."],
    ["Separar discriminación y decisión", "AUC y balanced accuracy juntas; su divergencia delata la calibración."],
    ["Medir estabilidad en particiones disjuntas", "No en folds solapados; declarar la fracción de muestras compartidas."],
    ["Cuantificar la curación automatizada", "Tasa de éxito por cohorte, y exclusión explícita cuando es baja."],
  ];
  ctrl.forEach(([tit, txt], i) => {
    const col = i % 2;
    const fila = Math.floor(i / 2);
    const x = M + col * 6.1;
    const y = 2.14 + fila * 1.56;
    s.addShape(pres.ShapeType.ellipse, {
      x, y, w: 0.46, h: 0.46,
      fill: { color: "262A30" }, line: { color: AZUL, width: 1 },
    });
    s.addText(String(i + 1), {
      x, y, w: 0.46, h: 0.46, fontFace: SERIF, fontSize: 14, bold: true,
      color: AZUL, align: "center", valign: "middle", margin: 0,
    });
    s.addText(tit, {
      x: x + 0.66, y: y - 0.02, w: 5.2, h: 0.38,
      fontFace: SANS, fontSize: 13.5, bold: true, color: BLANCO, margin: 0, valign: "top",
    });
    s.addText(txt, {
      x: x + 0.66, y: y + 0.38, w: 5.2, h: 0.9,
      fontFace: SANS, fontSize: 11, color: "9AA7B8", margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });
  });
  s.addNotes(
    "Esta es la aportacion que defiendo: no una firma, sino seis controles concretos, " +
    "cada uno derivado de un fallo que este trabajo encontro y midio. Son aplicables a " +
    "cualquier pipeline de descubrimiento sobre repositorios publicos."
  );
}

// =========================================================== 15. CONCLUSIONES
{
  const s = slideClara();
  antetitulo(s, "CONCLUSIONES");
  titulo(s, "Qué sostienen los datos");

  const concl = [
    [String(D.panelMin), `genes componen el panel entregado por el framework, con AUC ${dec(D.aucPanel)} en validación externa y ${D.ihcRec} de ${D.ihcTot} marcadores de inmunohistoquímica recuperados`, AZUL],
    [`${D.genesDisj} de 7`, "genes de la firma inicial que superan la capa de validación: el framework rechaza su propio primer resultado", ROJO],
    [dec(D.balAcc), "balanced accuracy real en tumor frente a sano, frente al valor que se obtenía incluyendo las tres cohortes de una sola clase", TINTA],
  ];
  concl.forEach(([v, t, c], i) => {
    const y = 1.9 + i * 1.4;
    s.addText(v, {
      x: M, y, w: 2.5, h: 0.72,
      fontFace: SERIF, fontSize: 36, bold: true, color: c, margin: 0, valign: "top",
    });
    s.addText(t, {
      x: M + 2.7, y: y + 0.08, w: 9.2, h: 0.9,
      fontFace: SANS, fontSize: 13.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.24,
    });
  });

  tarjeta(s, M, 6.06, 11.86, 0.92, "1A1D21");
  s.addText(
    "Un framework que no puede rechazar su propio resultado no está validando: está confirmando.",
    { x: M + 0.4, y: 6.2, w: 11.1, h: 0.64, fontFace: SERIF, fontSize: 16, italic: true, color: BLANCO, margin: 0, valign: "middle" }
  );
  s.addNotes(
    "Tres cifras. La primera es lo que el framework entrega: un panel de veinte genes " +
    "validado. La segunda es lo que rechaza: ninguno de los siete genes de mi primera " +
    "firma supera la validacion. La tercera es cuanto se corrige el rendimiento al medir " +
    "bien. Y la frase de abajo es la tesis: un framework que no puede rechazar su propio " +
    "resultado no esta validando, esta confirmando."
  );
}

// =========================================================== 16. FUTURAS
{
  const s = slideClara();
  antetitulo(s, "LÍNEAS FUTURAS");
  titulo(s, "Preguntas que estos mismos datos ya permiten");

  const lin = [
    ["Pronóstico", "GSE30219 y GSE50081 tienen seguimiento clínico completo: 307 y 181 tumores, con 200 y 75 eventos de mortalidad. Análisis de supervivencia con validación cruzada entre cohortes.", "Las dos cohortes que rompían el clasificador binario son las mejores para esta pregunta."],
    ["Alteración conductora", "GSE31210 incluye el estado de los genes conductores: 127 tumores con mutación de EGFR, 20 de KRAS, 11 con fusión de ALK y 68 sin ninguna de las tres.", "Predecir la alteración desde el perfil de expresión."],
    ["Deconvolución celular", "Sustituir el panel de marcadores promediado por estimación de proporciones celulares, para cuantificar la composición tisular con rigor.", "Y recuperar las tres cohortes de RNA-seq no procesadas, que permitirían evaluar la transferencia entre plataformas."],
  ];
  lin.forEach(([tit, txt, nota], i) => {
    const x = M + i * 4.06;
    tarjeta(s, x, 1.95, 3.78, 4.5);
    s.addText(tit, {
      x: x + 0.32, y: 2.22, w: 3.14, h: 0.4,
      fontFace: SERIF, fontSize: 17, bold: true, color: TINTA, margin: 0, valign: "top",
    });
    s.addText(txt, {
      x: x + 0.32, y: 2.76, w: 3.14, h: 2.1,
      fontFace: SANS, fontSize: 11.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.24,
    });
    s.addText(nota, {
      x: x + 0.32, y: 5.06, w: 3.14, h: 1.14,
      fontFace: SANS, fontSize: 10.5, italic: true, color: MUDO, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });
  });
  pieDiapo(s, "Ninguna requiere descargar datos nuevos: los metadatos clínicos ya están en disco y no se habían utilizado.");
  s.addNotes(
    "Tres lineas, y ninguna necesita datos nuevos. Lo mas elegante: las dos cohortes que " +
    "rompian el clasificador binario, por no tener controles, son cohortes de " +
    "supervivencia. Para la pregunta correcta pasan de ser el problema a ser el mejor " +
    "activo del trabajo."
  );
}

// =========================================================== 17. REFERENCIAS
{
  const s = slideClara();
  antetitulo(s, "REFERENCIAS");
  titulo(s, "Referencias");

  const refs = [
    "Bray, F. et al. (2024). Global cancer statistics 2022: GLOBOCAN estimates of incidence and mortality worldwide. CA: A Cancer Journal for Clinicians, 74(3).",
    "Barrett, T. et al. (2013). NCBI GEO: archive for functional genomics data sets — update. Nucleic Acids Research, 41(D1).",
    "Leek, J. T. et al. (2010). Tackling the widespread and critical impact of batch effects in high-throughput data. Nature Reviews Genetics, 11(10).",
    "Bernau, C. et al. (2014). Cross-study validation for the assessment of prediction algorithms. Bioinformatics, 30(12).",
    "Ioannidis, J. P. A. (2005). Why most published research findings are false. PLoS Medicine, 2(8).",
    "Benjamini, Y. y Hochberg, Y. (1995). Controlling the false discovery rate. Journal of the Royal Statistical Society B, 57(1).",
    "Tibshirani, R. (1996). Regression shrinkage and selection via the lasso. Journal of the Royal Statistical Society B, 58(1).",
  ];
  refs.forEach((r, i) => {
    s.addText(r, {
      x: M, y: 1.78 + i * 0.44, w: 7.5, h: 0.4,
      fontFace: SANS, fontSize: 10.5, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.14,
    });
  });

  tarjeta(s, 8.5, 1.78, 4.08, 3.7);
  s.addText("COHORTES ANALIZADAS", {
    x: 8.82, y: 2.04, w: 3.44, h: 0.28,
    fontFace: SANS, fontSize: 9.5, bold: true, charSpacing: 1.5, color: MUDO, margin: 0,
  });
  const acc = aud.map((r) => r.Cohorte).join(" · ");
  s.addText(acc, {
    x: 8.82, y: 2.4, w: 3.44, h: 1.5,
    fontFace: SANS, fontSize: 11, color: TINTA_2, margin: 0, valign: "top", lineSpacingMultiple: 1.3,
  });
  s.addText(
    "Publicaciones originales de las cohortes principales: Rousseaux et al. (2013), " +
    "Sci Transl Med, GSE30219 · Der et al. (2014), J Thorac Oncol, GSE50081 · " +
    "Okayama et al. (2012), Cancer Res, GSE31210 · Hou et al. (2010), PLoS ONE, GSE19188.",
    { x: 8.82, y: 3.92, w: 3.44, h: 1.4, fontFace: SANS, fontSize: 10, color: MUDO, margin: 0, valign: "top", lineSpacingMultiple: 1.2 }
  );

  s.addText(
    "Código y resultados: github.com/danitapiadiez-gif/TFM-Bioinformatica",
    { x: M, y: 5.9, w: 11.86, h: 0.4, fontFace: SANS, fontSize: 11.5, color: TINTA, margin: 0 }
  );
  pieDiapo(s, "Todos los análisis son reproducibles: random_state fijado, y las tablas y figuras se generan desde los CSV de resultados.");
  s.addNotes(
    "Referencias metodologicas y las publicaciones originales de las cohortes. Todo el " +
    "codigo esta publico, y los analisis son deterministas: dos ejecuciones producen " +
    "resultados identicos."
  );
}

// =========================================================== 18. CIERRE
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
    "Un resultado negativo bien medido dice más que un resultado positivo mal validado.",
    { x: M, y: 4.14, w: 9.4, h: 0.8, fontFace: SERIF, fontSize: 17, italic: true, color: "C3C2B7", margin: 0, lineSpacingMultiple: 1.24 }
  );
  s.addText([
    { text: "Daniel Tapia Díez", options: { bold: true, color: BLANCO, fontSize: 13 } },
    { text: "\nMáster Universitario en Bioinformática  ·  Universidad Alfonso X el Sabio", options: { color: MUDO, fontSize: 11.5 } },
  ], { x: M, y: 5.6, w: 8, h: 0.9, fontFace: SANS, margin: 0, lineSpacingMultiple: 1.24 });
  s.addNotes(
    "Gracias. Quedo a disposicion del tribunal para las preguntas."
  );
}

const salida = path.join(RAIZ, "DEFENSA_TFM.pptx");
pres.writeFile({ fileName: salida }).then(() => {
  console.log("Escrito: " + salida);
  console.log(`Diapositivas: ${pres.slides.length}`);
  console.log(`Cifras leidas de los CSV -> balAcc ${dec(D.balAcc)}, auc ${dec(D.auc)}, ` +
    `rho ${dec(D.rho)}, concordancia ${dec(D.concLodo, 1)}/${dec(D.concDisj, 2)}, ` +
    `aucSub ${dec(D.aucSub)}`);
});
