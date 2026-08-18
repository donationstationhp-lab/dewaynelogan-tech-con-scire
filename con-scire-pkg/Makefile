API ?= http://localhost:5000

test:
	python -m pytest tests/ -v

station:
	python bridge.py --api $(API) --station

stage:
	python bridge.py --api $(API) --stage $(STAGE)

item:
	python bridge.py --api $(API) --item $(ID)

health:
	python bridge.py --api $(API)

.PHONY: test station stage item health
