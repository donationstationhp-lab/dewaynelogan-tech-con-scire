API ?= http://localhost:5000
_SRC  = $(if $(ORG),--org $(ORG),--api $(API))
_DATA = $(if $(DATA),--data $(DATA),)

test:
	python -m pytest tests/ -v

station:
	python bridge.py $(_SRC) $(_DATA) --station

stage:
	python bridge.py $(_SRC) $(_DATA) --stage $(STAGE)

item:
	python bridge.py $(_SRC) $(_DATA) --item $(ID)

health:
	python bridge.py $(_SRC) $(_DATA)

.PHONY: test station stage item health
