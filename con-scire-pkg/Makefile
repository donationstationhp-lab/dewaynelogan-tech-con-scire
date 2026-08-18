API ?= http://localhost:5000

test:
	python -m pytest tests/ -v

origin:
	python bridge.py --api $(API) --origin $(if $(FOUNDED),--founded $(FOUNDED),)

station:
	python bridge.py --api $(API) --station

donors:
	python bridge.py --api $(API) --donors

stage:
	python bridge.py --api $(API) --stage $(STAGE)

item:
	python bridge.py --api $(API) --item $(ID)

health:
	python bridge.py --api $(API)

.PHONY: test origin station donors stage item health
