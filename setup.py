#!/usr/bin/env python

from distutils.core import setup

import securetypes

setup(
	name='Securetypes',
	version=securetypes.__version__,
	description="Implementation of dict that protects against " +
		"algorithmic complexity attacks",
	url="https://github.com/ludios/Securetypes",
	author="Ivan Kozik",
	author_email="ivan@ludios.org",
	classifiers=[
		'Programming Language :: Python :: 2',
		'Development Status :: 4 - Beta',
		'Operating System :: OS Independent',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
	],
	py_modules=['securetypes', 'test_securetypes'],
)
