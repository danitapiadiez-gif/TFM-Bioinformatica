# ==========================================================================
# Makefile para compilar la memoria del TFM
# Uso:
#   make          → compila main.pdf
#   make clean    → borra intermedios (mantiene main.pdf)
#   make distclean → borra todo, incluido main.pdf
#   make install-deps → instala los paquetes LaTeX necesarios (requiere tlmgr)
# ==========================================================================

MAIN    = main
LATEX   = pdflatex -interaction=nonstopmode
BIBTEX  = bibtex

TEX_FILES = main.tex preambulo.tex portada.tex resumen.tex \
            $(wildcard capitulos/*.tex)
BIB_FILE  = bibliografia.bib
FIG_FILES = $(wildcard figuras/*.pdf figuras/*.png figuras/interfaz/*.png)

.PHONY: all clean distclean install-deps quick

all: $(MAIN).pdf

$(MAIN).pdf: $(TEX_FILES) $(BIB_FILE) $(FIG_FILES)
	$(LATEX) $(MAIN).tex
	$(BIBTEX) $(MAIN)
	$(LATEX) $(MAIN).tex
	$(LATEX) $(MAIN).tex

# Compilación rápida sin regenerar bibliografía (solo si ya lo compilaste una vez)
quick:
	$(LATEX) $(MAIN).tex

clean:
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).toc $(MAIN).out $(MAIN).lof \
	      $(MAIN).lot $(MAIN).bbl $(MAIN).blg $(MAIN).fdb_latexmk \
	      $(MAIN).fls $(MAIN).synctex.gz \
	      capitulos/*.aux

distclean: clean
	rm -f $(MAIN).pdf

install-deps:
	@which tlmgr >/dev/null 2>&1 || { echo "ERROR: tlmgr no esta disponible. Instala TeX Live o MacTeX primero."; exit 1; }
	tlmgr install \
	  babel-spanish lmodern setspace \
	  fancyhdr geometry titlesec appendix \
	  graphicx float booktabs longtable multirow subcaption caption \
	  xcolor listings amsmath amssymb mathtools \
	  hyperref natbib pgf tikz
	@echo "Dependencias instaladas."
