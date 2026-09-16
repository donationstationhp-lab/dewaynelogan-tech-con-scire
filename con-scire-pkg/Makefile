_ORG  = $(if $(ORG),--org $(ORG),)
_API  = $(if $(API),--api $(API),)
_DATA = $(if $(DATA),--data $(DATA),)
_ARGS = $(_ORG) $(_API) $(_DATA)

test:
	python -m pytest tests/ -v

station:
	python bridge.py $(_ARGS) --station

stage:
	python bridge.py $(_ARGS) --stage $(STAGE)

item:
	python bridge.py $(_ARGS) --item $(ID)

origin:
	python bridge.py $(_ARGS) --stage intake

health:
	python bridge.py $(_ARGS)

.PHONY: test station stage item origin health
