# Root Makefile for NVIDIA cuOpt Repository

.PHONY: all slides clean purge

all: slides

slides:
	$(MAKE) -C presentation all

clean:
	$(MAKE) -C presentation clean

purge:
	$(MAKE) -C presentation purge
