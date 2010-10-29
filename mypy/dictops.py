from mypy.randgen import secureRandom
from mypy.constant import Constant

_postImportVars = vars().keys()


_NO_ARG = Constant("_NO_ARG")
_globalSeenStack = []

class securedict(dict):
	"""
	A dictionary that is relatively safe from algorithmic complexity attacks.

	It is == to normal dicts (if the contents are the same).

	C{.copy()} returns a L{securedict}.

	C{.popitem()} may behave slightly differently; see the unit tests.

	C{__lt__} and C{__gt__} behave in a completely undefined manner.

	Even if your Python runtime is patched to raise an exception if > n
	iterations are required to set/get an item from a dict/set, you may need
	securedict if more than one user contributes to the content of the dict.
	"""
	__slots__ = ('_random1', '_random2')

	def __new__(cls, x={}, **kwargs):
		# TODO: make sure this doesn't mutate old dict
		obj = dict.__new__(cls)
		obj._random1 = secureRandom(4)
		obj._random2 = secureRandom(4)
		obj.update(x, **kwargs)
		return obj


	def __init__(self, *args, **kwargs):
		# We must override __init__ to prevent dict.__init__ from inserting
		# unsecured keys during instantiation.
		pass


	def update(self, x={}, **kwargs):
		# See help({}.update) for the algorithm.
		if hasattr(x, 'keys'):
			for k in x.keys():
				self[k] = x[k]
		else:
			for k, v in x:
				self[k] = v
		for k, v in kwargs.iteritems():
			self[k] = v


	def __getitem__(self, key):
		if key in self:
			return dict.__getitem__(self, (self._random1, key, self._random2))
		else:
			# "__missing__ must be a method; it cannot be an instance variable."
			# See test_missing.
			missing = getattr(self.__class__, '__missing__', None)
			if missing:
				return missing(self, key)
			else:
				raise KeyError(key)


	def __setitem__(self, key, value):
		return dict.__setitem__(self, (self._random1, key, self._random2), value)


	def __delitem__(self, key):
		try:
			return dict.__delitem__(self, (self._random1, key, self._random2))
		except KeyError:
			raise KeyError(key)


	def __contains__(self, key):
		return dict.__contains__(self, (self._random1, key, self._random2))
	has_key = __contains__


	def __eq__(self, other):
		if not isinstance(other, dict):
			return False
		for k in self.__dictiter__():
			mykey = k[1]
			if mykey not in other:
				return False
			if self[mykey] != other[mykey]:
				return False
		for k in other:
			if k not in self:
				return False
		return True


	def __ne__(self, other):
		return not self.__eq__(other)


	def __repr__(self):
		if self in _globalSeenStack:
			return 'securedict({...})'
		try:
			isRootObject = False
			if not _globalSeenStack:
				isRootObject = True
				_globalSeenStack.append(self)
			buf = ['securedict({']
			comma = ''
			for k in self.__dictiter__():
				buf.append(comma)
				comma = ','
				_globalSeenStack.append(k[1])
				buf.append(repr(k[1]))
				_globalSeenStack.pop()
				buf.append(': ')
				v = self[k[1]]
				_globalSeenStack.append(v)
				buf.append(repr(v))
				_globalSeenStack.pop()
			buf.append('})')
			return ''.join(buf)
		finally:
			if isRootObject:
				del _globalSeenStack[:]


	def get(self, key, default=None):
		return dict.get(self, (self._random1, key, self._random2), default)


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
		return (pair[0][1], pair[1])


	def setdefault(self, key, d=None):
		if key not in self:
			self[key] = d
		return self[key]


	def keys(self):
		return list(k[1] for k in self.__dictiter__())

	__dictiter__ = dict.__iter__

	def __iter__(self):
		for k in self.__dictiter__():
			yield k[1]


	def iteritems(self):
		for k, v in dict.iteritems(self):
			yield k[1], v


	def items(self):
		return list((k[1], v) for k, v in dict.iteritems(self))


	def copy(self):
		# Must do this, otherwise the copy is "double secured"
		return securedict(self.items())



class attrdict(dict):
	"""
	A dict that can be modified by setting and getting attributes.
	This may be broken in funny ways; use with care.
	"""
	__slots__ = ()

	def __setattr__(self, key, value):
		self[key] = value


	def __getattribute__(self, key):
		return self[key]



class consensualfrozendict(dict):
	"""
	A C{dict} that block naive attempts to mutate it, but isn't really
	immutable.

	Allowed to have unhashable values, so it is not necessarily hashable.
	"""
	__slots__ = ('_cachedHash')

	@property
	def _blocked(self):
		raise AttributeError("A consensualfrozendict cannot be modified.")

	__delitem__ = \
	__setitem__ = \
	clear = \
	pop = \
	popitem = \
	setdefault = \
	update = \
	_blocked

	def __new__(cls, *args, **kwargs):
		new = dict.__new__(cls)
		new._cachedHash = None
		dict.__init__(new, *args, **kwargs)
		return new


	# A Python dict can be updated with __init__ after it is created,
	# which is the only reason we override __init__ and __new__.
	def __init__(self, *args, **kwargs):
		pass


	def __hash__(self):
		h = self._cachedHash
		if h is None:
			h = self._cachedHash = hash(tuple(self.iteritems()))
		return h


	def __repr__(self):
		return "consensualfrozendict(%s)" % dict.__repr__(self)



class frozendict(tuple):
	"""
	A C{dict} that is really immutable. Ideal for small dicts.

	It is slower than a dict (often O(N) instead of O(1)) because it is based
	on a tuple, but it does use less memory just sitting around.

	Allowed to have unhashable values, so it is not necessarily hashable.

	Note that __eq__ on this is probably broken, because it assumes that
	the other frozendict has the same underlying order.  This is usually
	but not necessarily the case.  For example:
	>>> print {-1: None, -2: None}, {-2: None, -1: None}
	{-2: None, -1: None} {-1: None, -2: None}
	"""
	__slots__ = ()

	@property
	def _blocked(self):
		raise AttributeError("A frozendict cannot be modified.")

	__delitem__ = \
	__setitem__ = \
	clear = \
	pop = \
	popitem = \
	setdefault = \
	update = \
	_blocked

	def __new__(cls, obj={}, **kwargs):
		d = obj.copy()
		for k, v in kwargs.iteritems():
			d[k] = v
		new = tuple.__new__(cls, tuple(d.iteritems()))
		return new


	def __getitem__(self, key):
		for k, v in self.__tupleiter__():
			if k == key:
				return self[v]
		raise KeyError(key)


	def get(self, key, default=None):
		for k, v in self.__tupleiter__():
			if k == key:
				return self[v]
		return default


	def __contains__(self, key):
		for k, v in self.__tupleiter__():
			if k == key:
				return True
		return False


	def keys(self):
		return list(i[0] for i in self.__tupleiter__())


	def values(self):
		return list(i[1] for i in self.__tupleiter__())


	def items(self):
		return list(self.__tupleiter__())


	def iterkeys(self):
		# Not a dictionary-keyiterator object, but close enough.
		for k, v in self.__tupleiter__():
			yield k

	__tupleiter__ = tuple.__iter__
	__iter__ = iterkeys


	def itervalues(self):
		# Not a dictionary-valueiterator object, but close enough.
		for k, v in self.__tupleiter__():
			yield v


	def iteritems(self):
		# Not a dictionary-itemiterator object, but close enough.
		for kv in self.__tupleiter__():
			yield kv


	def copy(self):
		return self


	def __repr__(self):
		return 'frozendict(%r)' % dict(self.__tupleiter__())


	def viewitems(self):
		return dict(self.__tupleiter__()).viewitems()


	def viewkeys(self):
		return dict(self.__tupleiter__()).viewkeys()


	def viewvalues(self):
		return dict(self.__tupleiter__()).viewvalues()


# A custom __repr__, speed difference unknown:
#	def __repr__(self):
#		buf = ['frozendict({']
#		comma = ''
#		for k, v in self.__tupleiter__():
#			buf.append(comma)
#			comma = ','
#			buf.append(repr(k))
#			buf.append(': ')
#			buf.append(repr(v))
#		buf.append('})')
#		return ''.join(buf)


# We could also do an insane hack based on using both a frozenset and a
# tuple. The frozenset would have fake-hashable markers that tell you which
# index to look up in the tuple.


from pypycpyo import optimizer
optimizer.bind_all_many(vars(), _postImportVars)
