Securedict overview
===================

Securedict is an implementation of `dict` that protects against algorithmic
complexity attacks.  With a normal `dict`, if the attacker can control the keys
inserted into the dict, he can slow the server to a halt by picking keys with
colliding `hash()`es.  `securedict.securedict` protects against this by
surrounding the key with random data, making it (hopefully) impossible to
predict the `hash()`.

You can use `securedict` very much like a `dict`:

```
from securedict import securedict

d = securedict(x=3)
d['y'] = 4

print d # prints: securedict({'y': 4, 'x': 3})
```

For more information about algorithmic complexity attacks, see:

*	http://www.cs.rice.edu/~scrosby/hash/CrosbyWallach_UsenixSec2003/

*	http://mail.python.org/pipermail/python-dev/2003-May/035874.html



The fine print
==============

*	A securedict is `==` to a normal dict (if the contents are the same).

*	`securedict` is a subclass of `dict`.

*	There is a major limitation: in CPython, `dict()`ing a `securedict` gives you
	garbage.  In pypy it works, though you still should not do it because
	it defeats the purpose of `securedict`.

*	`.copy()` returns a `securedict`.

*	`.popitem()` may pop a different item than an equal dict would; see the
	unit tests.

*	A securedict's `<` and `>` compares the `securedict`'s id instead of using
	Python's complicated algorithm.  This may change in the future to work
	like Python's algorithm (see CPython `dictobject.c:dict_compare`).  Don't
	rely on the current "compares id" behavior.

*	In Python 2.7+, calling `.viewitems()` or `.viewkeys()` raises
	`NotImplementedError`, while `.viewvalues()` works as usual.

Again: *never* `dict()` a `securedict`.



Requirements
============

CPython 2.4+ or pypy (tested 1.4 and 1.5)



Installation
============

`python setup.py install`

This installs the modules `securedict` and `test_securedict`.



Running the tests
=================

Install Twisted, then run `trial test_securedict`



Code style notes
================

This package mostly follows the Divmod Coding Standard
<http://replay.web.archive.org/http://divmod.org/trac/wiki/CodingStandard> with a few exceptions:

*	Use hard tabs for indentation.

*	Use hard tabs only at the beginning of a line.

*	Prefer to have lines <= 80 characters, but always less than 100.
