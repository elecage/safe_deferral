.PHONY: test test-mm test-rpi

test: test-mm test-rpi

test-mm:
	cd mac_mini/code && python -m pytest

test-rpi:
	cd rpi/code && python -m pytest
