all:
	python3 -m build

test:
	tox --sitepackages
