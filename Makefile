# Root Makefile for NVIDIA cuOpt Repository

.PHONY: all slides clean purge

all: slides

slides:
	$(MAKE) -C docs/presentation all

clean:
	$(MAKE) -C docs/presentation clean

purge:
	$(MAKE) -C docs/presentation purge
