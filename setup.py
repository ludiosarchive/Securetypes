#!/usr/bin/env python

from distutils.core import setup

import securedict

setup(
	name='Securedict',
	version=securedict.__version__,
	description="Implementation of dict that protects against " +
		"algorithmic complexity attacks",
	url="https://github.com/ludios/Securedict",
	author="Ivan Kozik",
	author_email="ivan@ludios.org",
	classifiers=[
		'Programming Language :: Python :: 2',
		'Development Status :: 4 - Beta',
		'Operating System :: OS Independent',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
	],
	py_modules=['securedict', 'test_securedict'],
)
