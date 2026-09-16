API ?= http://localhost:5000

test:
	python -m pytest tests/ -v

station:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --station

stage:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --stage $(STAGE)

item:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --item $(ID)

health:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API))

.PHONY: test station stage item health
