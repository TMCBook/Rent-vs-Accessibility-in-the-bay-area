# Thin wrapper: all logic lives in run.py so Windows users can run `python run.py <target>`.
PY ?= python

.PHONY: data features split train predict eval tables figures all final check clean-clone-check test clean

data features split train predict eval tables figures all final check clean-clone-check test clean:
	$(PY) run.py $@
