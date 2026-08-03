# Framework transcriptómico — arquitectura del código

Documenta la estructura del paquete `tfm/`. Complementa al `README.md`, que
describe el pipeline y los resultados.

## Por qué existe el paquete

Antes de este refactor el proyecto era un conjunto de scripts. Concretamente:

- el bucle de validación LODO estaba **reimplementado cinco veces** (pasos 13,
  15, 16, 17 y 19), y el bloque de estandarización por estudio, cuatro;
- las cohortes, los modelos y los umbrales estaban escritos en `.py`, de modo
  que **añadir una pregunta biológica exigía escribir otro script**;
- **nueve ficheros** contenían la ruta `/Users/danieltapiadiez/Desktop`;
- no había tests, ni `__init__.py`, ni forma de importar nada.

Las cinco copias del LODO no eran equivalentes: divergían en el modelo, en el
escalado y en las métricas reportadas. Eso es precisamente el tipo de fallo
silencioso que el trabajo estudia.

## Estructura

```
tfm/
  cohortes.py        carga y alineamiento por geo_accession — nunca por posición
  tareas.py          una tarea = etiquetas + mapa, definida en YAML
  validacion.py      LODO y métricas honestas — una sola implementación
  firma.py           criterios de replicación y panel mínimo
  comprobaciones.py  los cuatro modos de fallo, como control automático
  cli.py             punto de entrada
configuracion/
  tareas.yaml        las tareas biológicas
tests/               17 tests, incluido el de regresión del bug de GSE30219
agentes/             los pasos del pipeline, ahora envoltorios del paquete
```

## Uso

```bash
pip install -e .

python -m tfm listar                          # tareas declaradas
python -m tfm comprobar                       # los 4 controles sobre los datos
python -m tfm ejecutar subtipo_histologico    # tarea completa
python -m pytest tests -q                     # 17 tests
```

## Añadir una pregunta nueva

Sin escribir código. Por ejemplo, predecir alteración conductora en GSE31210:

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

Y después `python -m tfm ejecutar gen_conductor`. El framework se encarga del
alineamiento, las comprobaciones previas, el LODO con baseline declarado, la
firma replicada y el panel mínimo.

## Invariantes que el código garantiza

1. **Toda carga alinea por `geo_accession`.** No hay vía alternativa: el bug de
   GSE30219 no puede reaparecer por descuido, y hay un test que lo comprueba.
2. **Una sola implementación del LODO.** Cambiar el escalado o el modelo se hace
   en un sitio.
3. **`random_state` fijado en `tfm.validacion`**, no a criterio de la tarea: dos
   ejecuciones producen resultados idénticos.
4. **Las cohortes de una sola clase se marcan no evaluables** y quedan fuera de
   las medias, con la media ingenua reportada aparte y etiquetada como tal.
5. **Los cuatro controles se ejecutan antes de cualquier análisis.**

## Equivalencia con los resultados publicados

El refactor no altera ninguna cifra. Verificado sobre las diez que aparecen en
la memoria y la presentación: balanced accuracy 0,7722, AUC 0,9252,
especificidad 0,5615, ρ −0,6257, concordancia 100,0 % / 77,33 %, AUC de subtipo
0,9683, 1174 genes validados, panel mínimo de 20 y 29,3785 % de asignaciones de
alta confianza. Todas idénticas antes y después.
