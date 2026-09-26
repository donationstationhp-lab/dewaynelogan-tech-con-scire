_ORG  = $(if $(ORG),--org $(ORG),)
_API  = $(if $(API),--api $(API),)
_DATA = $(if $(DATA),--data $(DATA),)
_ARGS = $(_ORG) $(_API) $(_DATA)

test:
	python -m pytest tests/ -v

origin:
	python bridge.py $(_ORG) $(_API) --origin $(if $(FOUNDED),--founded $(FOUNDED),)

station:
	python bridge.py $(_ARGS) --station

donors:
	python bridge.py $(_ARGS) --donors

intake:
	python bridge.py $(_ORG) $(_API) --stage intake

stage:
	python bridge.py $(_ORG) $(_API) --stage $(STAGE)

item:
	python bridge.py $(_ARGS) --item $(ID)

health:
	python bridge.py $(_ORG) $(_API)

loop:
	python bridge.py $(_ORG) $(_API) --loop

.PHONY: test origin intake station donors stage item health loop
