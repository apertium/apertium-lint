all:
	rm -rf dist
	python3 -m build

test:
	python3 -m unittest discover -v

upload:
	python3 -m twine check dist/* --strict
	python3 -m twine upload dist/* --verbose
