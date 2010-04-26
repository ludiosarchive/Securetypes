#!/usr/bin/env python

from distutils.core import setup

import mypy

setup(
	name='mypy',
	version=mypy.__version__,
	description="Python utilities usable in a wide variety of applications.",
	packages=['mypy', 'mypy.test'],
	package_data={'mypy.test': ['images/*']},
)
