__version__ = '11.5.5.1'

from os import urandom


class _DictSubclass(dict):

	def keys(self):
		return ['a']


	def __iter__(self):
		return ['b']



def isDictUpdateBroken():
	"""
	Return C{True} if the Python implementation's dict update algorithm is
	broken. In CPython, it is broken, because it does not use .keys() for
	subclasses of dicts.  In pypy, it isn't broken.
	"""
	special = _DictSubclass(a=1, b=2, c=3)
	d = {}
	d.update(special)
	return d != {'a': 1}


# If you see ("_securedictmarker", <object object at 0x>) show up in your dict,
# you probably dict()ed a securedict in CPython.  Don't dict() securedicts
# for security reasons, but especially not in CPython, because CPython's dict
# update algorithm is broken: http://bugs.python.org/issue10240
_securedictmarker = ("_securedictmarker", object())

_NO_ARG = object()

class securedict(dict):
	"""
	A dictionary that is relatively safe from algorithmic complexity attacks.
	To be safe from such attacks, it modifies the keys, so that they have
	unpredictable C{hash()}es.

	The fine print:

	A securedict is C{==} to a normal dict (if the contents are the same).

	securedict is a subclass of dict.

	There is a major limitation: in CPython, dict()ing a securedict gives you
	garbage.  In pypy it works, though you still should not do it because
	it defeats the purpose of securedict.

	C{.copy()} returns a L{securedict}.

	C{.popitem()} may pop a different item than an equal dict would; see the
	unit tests.

	A securedict's < and > compares the securedict's id instead of using
	Python's complicated algorithm.  This may change in the future to work
	like Python's algorithm (see CPython dictobject.c:dict_compare).  Don't
	rely on the current "compares id" behavior.

	In Python 2.7+, calling C{.viewitems()} or C{.viewkeys()} raises
	L{NotImplementedError}, while C{.viewvalues()} works as usual.
	"""
	__slots__ = ('_random1', '_random2', '_inMyRepr')

	def __new__(cls, x={}, **kwargs):
		obj = dict.__new__(cls)
		obj._inMyRepr = False
		rand = urandom(16)
		obj._random1 = rand[:8]
		obj._random2 = rand[8:]
		return obj


	def update(self, __securedict_securedict_arg1={}, **kwargs):
		# Update like the documented update algorithm and like pypy, not
		# like CPython.
		x = __securedict_securedict_arg1
		if hasattr(x, 'keys'):
			for k in x.keys():
				self[k] = x[k]
		else:
			for k, v in x:
				self[k] = v

		for k, v in kwargs.iteritems():
			self[k] = v

	__init__ = update


	def __getitem__(self, key):
		if key in self:
			return dict.__getitem__(self,
				(_securedictmarker, self._random1, key, self._random2))
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
			(_securedictmarker, self._random1, key, self._random2), value)


	def __delitem__(self, key):
		try:
			return dict.__delitem__(self,
				(_securedictmarker, self._random1, key, self._random2))
		except KeyError:
			raise KeyError(key)


	def __contains__(self, key):
		return dict.__contains__(self,
			(_securedictmarker, self._random1, key, self._random2))
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


	def reprLikeDict(self):
		return self._repr(False)


	def get(self, key, default=None):
		return dict.get(self,
			(_securedictmarker, self._random1, key, self._random2), default)


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
