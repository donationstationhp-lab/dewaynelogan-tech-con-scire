API ?= http://localhost:5000

test:
	python -m pytest tests/ -v

origin:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --origin $(if $(FOUNDED),--founded $(FOUNDED),)

station:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) $(if $(DATA),--data $(DATA),) --station

donors:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) $(if $(DATA),--data $(DATA),) --donors

intake:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --stage intake

stage:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --stage $(STAGE)

item:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) $(if $(DATA),--data $(DATA),) --item $(ID)

health:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API))

loop:
	python bridge.py $(if $(ORG),--org $(ORG),--api $(API)) --loop

.PHONY: test origin intake station donors stage item health loop
