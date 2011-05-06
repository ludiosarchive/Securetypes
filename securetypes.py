__version__ = '11.5.6'

from types import NoneType
from os import urandom

try:
	from hashlib import sha1
except ImportError:
	# Python < 2.5 doesn't have hashlib
	from sha import sha as sha1


def _securehash_hasher(obj):
	t = type(obj)
	if t == str:
		h = sha1('\x01') # str or an ascii'able unicode
		h.update(obj)
	elif t in (int, long):
		h = sha1('\x00') # "number"
		h.update(str(obj))
	elif t == unicode:
		try:
			ascii = obj.encode('ascii')
			h = sha1('\x01') # str or an ascii'able unicode
			h.update(ascii)
		except UnicodeEncodeError:
			h = sha1('\x02') # non-ascii'able unicode
			h.update(obj.encode('utf-8'))
	elif t == bool:
		h = sha1('\x00') # "number"
		if obj:
			h.update("1")
		else:
			h.update("0")
	elif t == float:
		h = sha1('\x00') # "number"
		rep = repr(obj)
		if rep in ("-0.0", "nan"):
			h.update("0")
		elif rep == "inf":
			h.update("314159")
		elif rep == "-inf":
			h.update("-271828")
		elif rep.endswith(".0"):
			h.update(rep[:-2])
		else:
			h.update(rep)
	elif t == NoneType:
		h = sha1('\x03') # NoneType
	else:
		raise TypeError("Don't know how to securely hash a %r object" % (t,))

	return h


def _securehash(obj):
	return _securehash_hasher(obj).digest()


class _DictSubclass(dict):

	def keys(self):
		return ['a']


	def __iter__(self):
		return ['b']



def is_dict_update_broken():
	"""
	Return C{True} if the Python implementation's dict update algorithm is
	broken.  In CPython, it is broken, because it doesn't use .keys() for
	objects that are subclasses of dict.  See <http://bugs.python.org/issue10240>.
	In pypy, it isn't broken.

	Note that the update algorithm affects both C{dict.__init__} and
	C{dict.update}.
	"""
	special = _DictSubclass(a=1, b=2, c=3)
	d = {}
	d.update(special)
	return d != {'a': 1}


# This value should never be sent or displayed to *anyone*
_securetypes_SECRET = urandom(160/8)

# If you see "_securedictmarker" show up in your dict, you probably dict()ed a
# securedict in CPython.  Don't dict() securedicts for security reasons, but
# especially not in CPython, because CPython's dict update algorithm is broken:
# http://bugs.python.org/issue10240
_securedictmarker = "_securedictmarker"

_NO_ARG = object()

class securedict(dict):
	"""
	A `dict` that is safe against algorithmic complexity attacks.  Internally,
	for each key, it stores a key wrapper like this:

		("_securedictmarker", sha1(key + secret), key)

	`sha1` protects against collisions, and `secret` makes the `hash()` of the
	wrapper unknowable to adversaries.

	The fine print:

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

	Additional security considerations:

	Don't use `nan`s as dictionary keys.  `securedict` can't help you here.
	All `nan`s have the same `hash()` and are not equal to any object.
	"""
	__slots__ = ('_inMyRepr',)

	def __new__(cls, *args, **kwargs):
		obj = dict.__new__(cls)
		obj._inMyRepr = False
		return obj


	def update(self, *args, **kwargs):
		# We use *args instead of a variable `x` to avoid blowing up if
		# we get a key named "x".
		if len(args) == 1:
			x = args[0]
			# Update like the documented update algorithm and like pypy,
			# not like CPython.
			if hasattr(x, 'keys'):
				for k in x.keys():
					self[k] = x[k]
			else:
				for k, v in x:
					self[k] = v
		elif len(args) > 1:
			raise TypeError("update expected at most 1 arguments, "
				"got %d" % (len(args),))

		for k, v in kwargs.iteritems():
			self[k] = v

	__init__ = update


	def _getSecureHash(self, key):
		h = _securehash_hasher(key)
		h.update(_securetypes_SECRET)
		return h.digest()


	def __getitem__(self, key):
		if key in self:
			return dict.__getitem__(self,
				(_securedictmarker, self._getSecureHash(key), key))
		else:
			# "__missing__ must be a method; it cannot be an instance variable."
			# See test_missing.
			missing = getattr(self.__class__, '__missing__', None)
			if missing:
				return missing(self, key)
			else:
				raise KeyError(key)


	def __setitem__(self, key, value):
		return dict.__setitem__(self,
			(_securedictmarker, self._getSecureHash(key), key), value)


	def __delitem__(self, key):
		try:
			return dict.__delitem__(self,
				(_securedictmarker, self._getSecureHash(key), key))
		except KeyError:
			raise KeyError(key)


	def __contains__(self, key):
		return dict.__contains__(self,
			(_securedictmarker, self._getSecureHash(key), key))
	has_key = __contains__


	def __eq__(self, other):
		return self.__cmp__(other) == 0


	def __ne__(self, other):
		return self.__cmp__(other) != 0


	def __lt__(self, other):
		return id(self) < id(other)


	def __gt__(self, other):
		return id(self) > id(other)


	def __le__(self, other):
		# Object id comparison is faster, so try that first.
		if id(self) < id(other):
			return True
		return self.__cmp__(other) == 0


	def __ge__(self, other):
		# Object id comparison is faster, so try that first.
		if id(self) > id(other):
			return True
		return self.__cmp__(other) == 0


	# Note that we must have a __cmp__ so that dict.__cmp__ is not used
	# by cmp()
	def __cmp__(self, other):
		if not isinstance(other, dict) or len(self) != len(other):
			return (-1, 1)[id(self) > id(other)]
		for k in self.__dictiter__():
			mykey = k[2]
			if mykey not in other or self[mykey] != other[mykey]:
				return (-1, 1)[id(self) > id(other)]
		for k in other:
			if k not in self:
				return (-1, 1)[id(self) > id(other)]
		return 0


	__dictiter__ = dict.__iter__

	def __iter__(self):
		for k in self.__dictiter__():
			yield k[2]


	def _repr(self, withSecureDictString):
		if self._inMyRepr:
			return 'securedict({...})'
		try:
			isRootObject = False
			if not self._inMyRepr:
				isRootObject = True
				self._inMyRepr = True
			buf = []
			buf.append(('{', 'securedict({')[withSecureDictString])
			comma = ''
			for k in self.__dictiter__():
				buf.append(comma)
				comma = ', '
				buf.append(repr(k[2]))
				buf.append(': ')
				v = self[k[2]]
				buf.append(repr(v))
			buf.append(('}', '})')[withSecureDictString])
			return ''.join(buf)
		finally:
			if isRootObject:
				self._inMyRepr = False


	def __repr__(self):
		return self._repr(True)


	def repr_like_dict(self):
		return self._repr(False)


	def get(self, key, default=None):
		return dict.get(self,
			(_securedictmarker, self._getSecureHash(key), key), default)


	def pop(self, key, d=_NO_ARG):
		try:
			v = self[key]
			del self[key]
			return v
		except KeyError:
			if d is _NO_ARG:
				raise
			return d


	def popitem(self):
		pair = dict.popitem(self)
		return (pair[0][2], pair[1])


	def setdefault(self, key, d=None):
		if key not in self:
			self[key] = d
		return self[key]


	def keys(self):
		return list(k[2] for k in self.__dictiter__())


	def iteritems(self):
		for k, v in dict.iteritems(self):
			yield k[2], v


	def items(self):
		return list((k[2], v) for k, v in dict.iteritems(self))


	def copy(self):
		return securedict(self)


	if hasattr({}, 'viewitems'): # Python 2.7+
		def viewitems(self):
			raise NotImplementedError("no viewitems on securedict")


		def viewkeys(self):
			raise NotImplementedError("no viewkeys on securedict")

		# viewvalues is okay



__all__ = ['__version__', 'is_dict_update_broken', 'securedict']
