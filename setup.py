#!/usr/bin/env python

from distutils.core import setup

import securedict

setup(
	name='Securedict',
	version=securedict.__version__,
	description="Implementation of dict that protects against " +
		"algorithmic complexity attacks",
	py_modules=['securedict', 'test_securedict'],
)
