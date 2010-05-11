class frozendict(dict):
	"""
	A C{dict} that tries hard to be immutable.
	"""
	__slots__ = ('_cachedHash')

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
		return "frozendict(%s)" % dict.__repr__(self)
