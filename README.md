Securetypes overview
====================

Securetypes' `securedict` is an implementation of `dict` that protects against
algorithmic complexity attacks.  With a normal `dict`, if an adversary can
control the keys inserted into the `dict`, he can slow the program to a halt
by picking keys with colliding `hash()`es.  To protect against this, internally
`securedict` stores a key wrapper for each key:

`("_securedictmarker", sha1(key + secret), key)`

`sha1` protects against collisions, and `secret` prevents adversaries from
controlling the `hash()` of the key wrapper.  (Without `secret`, you could just
pre-compute `hash(sha1(key))` for 2**32 keys.)

`securedict` implements most of the `dict` API; you can use it much like a `dict`:

```
from securetypes import securedict

d = securedict(x=3)
d['y'] = 4

print d # prints securedict({'y': 4, 'x': 3})

# Special features:
print d.repr_like_dict() # prints {'y': 4, 'x': 3}
```

For more information about algorithmic complexity attacks, see:

*	http://www.cs.rice.edu/~scrosby/hash/CrosbyWallach_UsenixSec2003/

*	http://mail.python.org/pipermail/python-dev/2003-May/035874.html



Using securedict with json/simplejson
=====================================

`securedict` is very useful when decoding JSON objects, because the objects
could contain many `hash()`-colliding keys.  You can tell json/simplejson
to create `securedict`s instead of `dict`s:

```
try:
	import simplejson as json
except ImportError:
	import json
from securetypes import securedict

dec = json.decoder.JSONDecoder(object_pairs_hook=securedict)
print dec.decode('{"b": ["bee", {}]}')
# prints securedict({'b': ['bee', securedict({})]})
```



The fine print
==============

*	A `securedict` supports only these types for keys: `str`, `unicode`,
	`int`, `long`, `float`, `bool`, and `NoneType`.  Future versions will
	support `tuple` and any object with a `__securehash__`.

*	A `securedict` is even less thread-safe than a `dict`.  Don't use the same
	`securedict` object in multiple threads.  Doing this may result in strange
	exceptions.

*	A `securedict` is `==` to a normal `dict` (if the contents are the same).

*	`securedict` is a subclass of `dict`.

*	In CPython, `dict()`ing a `securedict` gives you garbage (a dictionary
	containing key wrappers instead of the keys).  In pypy it works, though
	you still should never `dict()` a `securedict` because it defeats the
	purpose of `securedict`.

*	`.copy()` returns a `securedict`.

*	`.popitem()` may pop a different item than an equal dict would; see the
	unit tests.

*	A `securedict`'s `<` and `>` compares the `securedict`'s id instead of using
	Python's complicated algorithm.  This may change in the future to work
	like Python's algorithm (see CPython `dictobject.c:dict_compare`).  Don't
	rely on the current "compares id" behavior.

*	In Python 2.7+, calling `.viewitems()` or `.viewkeys()` raises
	`NotImplementedError`, while `.viewvalues()` works as usual.

*	`sys.setdefaultencoding` may affect a `securedict` differently than it
	affects `dict`.  (No one should ever use `setdefaultencoding`, but pygtk
	does.)

Again: *never* `dict()` a `securedict`.



Additional security considerations
==================================

Don't use `nan`s as dictionary keys.  `securedict` can't help you here.
All `nan`s have the same `hash()` and are not equal to any object.



Requirements
============

CPython 2.4+ or pypy (tested 1.4 and 1.5)



Installation
============

`python setup.py install`

This installs the modules `securetypes` and `test_securetypes`.

Securetypes is also available on PyPI <http://pypi.python.org/pypi/Securetypes>
and you can install it with pip:

`pip install Securetypes`



Running the tests
=================

Install Twisted, then run `trial test_securetypes`



Bugs
====

https://github.com/ludios/Securetypes/issues



Contributing
============

Patches and pull requests are welcome.

This coding standard applies: http://ludios.org/coding-standard/
