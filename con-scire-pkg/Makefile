API ?= http://localhost:5000

test:
	python -m pytest tests/ -v

origin:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --origin $(if $(FOUNDED),--founded $(FOUNDED),)

station:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --station

donors:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --donors

stage:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --stage $(STAGE)

item:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --item $(ID)

health:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API))

.PHONY: test origin station donors stage item health
