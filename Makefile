NAME = StenoDictate
ICON = data/icon.inkscape.icns

.PHONY: build
build: build_ui
	pyinstaller \
		--windowed \
		--noconfirm \
		--name $(NAME) \
		--icon $(ICON) \
		stenodictate/__main__.py

.PHONY: build_ui
build_ui:
	python setup.py build_ui

.PHONY: launch
launch: build_ui
	python -m stenodictate
