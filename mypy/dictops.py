_postImportVars = vars().keys()


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
