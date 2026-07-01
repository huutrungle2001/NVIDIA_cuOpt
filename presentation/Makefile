# Makefile for compiling Beamer slides

# Compiler and Flags
LATEX = pdflatex
LATEX_FLAGS = -interaction=nonstopmode -halt-on-error

.PHONY: all clean purge

all: slides.pdf clean

slides.pdf: slides.tex
	$(LATEX) $(LATEX_FLAGS) slides.tex
	$(LATEX) $(LATEX_FLAGS) slides.tex # Compile twice to resolve references and page numbers

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb

purge: clean
	rm -f slides.pdf
