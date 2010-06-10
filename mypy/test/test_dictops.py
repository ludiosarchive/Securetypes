import unittest

from mypy.dictops import attrdict, consensualfrozendict, frozendict



class AttrDictTests(unittest.TestCase):

	dtype = attrdict

	def test_setattr(self):
		d = self.dtype()
		d.somekey = 3
		self.assertEqual(3, d.somekey)
		self.assertEqual(3, d['somekey'])



class _BaseFrozenDictTests(object):

	dtype = consensualfrozendict

	def test_hashable(self):
		d = self.dtype(x=3, y=(), z="string")
		self.assertTrue(isinstance(hash(d), int))
		# exercise _cachedHash
		self.assertTrue(isinstance(hash(d), int))


	def test_notHashable(self):
		d = self.dtype(x=[])
		# exceptions.TypeError: unhashable type: 'list'
		self.assertRaises(TypeError, lambda: hash(d))


	def test_repr(self):
		d = self.dtype(x=3)
		self.assertEqual(self.dtype.__name__ + "({'x': 3})", repr(d))


	def test_repr2(self):
		d = self.dtype(x=[{}])
		self.assertEqual(self.dtype.__name__ + "({'x': [{}]})", repr(d))


	def test_reprEmpty(self):
		d = self.dtype()
		self.assertEqual(self.dtype.__name__ + "({})", repr(d))


	def test_equality(self):
		self.assertEqual(self.dtype(), self.dtype())
		self.assertEqual(self.dtype(x=3), self.dtype(x=3))
		self.assertNotEqual(self.dtype(x=3), self.dtype(x=4))


	def test_equalityForUnhashable(self):
		"""
		If the frozendict is not hashable, equality still works properly.
		"""
		self.assertEqual(self.dtype(x=[]), self.dtype(x=[]))
		self.assertEqual(self.dtype(x=[3]), self.dtype(x=[3]))
		self.assertNotEqual(self.dtype(x=[3]), self.dtype(x=[4]))


	def test_immutable(self):
		def delete(obj, key):
			del obj[key]

		def set(obj, key, value):
			obj[key] = value

		d = self.dtype(x=3)
		self.assertRaises(AttributeError, lambda: d.pop())
		self.assertRaises(AttributeError, lambda: d.popitem())
		self.assertRaises(AttributeError, lambda: d.clear())
		self.assertRaises(AttributeError, lambda: delete(d, "x"))
		self.assertRaises(AttributeError, lambda: set(d, "x", 4))
		self.assertRaises(AttributeError, lambda: d.setdefault("x", "y"))
		self.assertRaises(AttributeError, lambda: d.update({"x": 4}))



class ConsensualFrozenDictTests(_BaseFrozenDictTests, unittest.TestCase):

	def test_callingInitDoesNotUpdate(self):
		"""
		You can do this to Python dictionaries:

		>>> d = {1: 2}
		>>> d
		{1: 2}
		>>> d.__init__({1: 3})
		>>> d
		{1: 3}

		We don't waste a slot on frozendict to strategically throw
		AttributeError; we assume people calling __init__ a second time
		are insane and just ignore their request.

		Make sure that __init__ can't mutate the dict, though.
		"""
		d = self.dtype(x=3)
		d.__init__({"x": 4})
		self.assertEqual(3, d['x'])


	def test_notReallyImmutable(self):
		"""
		Unfortunately, dict.__init__ (and other dict methods) can be used
		to update the frozendict.
		"""
		d = self.dtype(x=3)
		dict.__init__(d, {'x': 4})
		self.assertEqual(4, d['x'])



class _DictReadingTests(object):
	dtype = frozendict

	def test_len(self):
		self.assertEqual(0, len(self.dtype()))
		self.assertEqual(1, len(self.dtype(x=3)))


	def test_contains(self):
		d = self.dtype(x=3)
		self.assertTrue('x' in d)
		self.assertFalse('y' in d)
		self.assertFalse(3 in d)
		self.assertFalse(('x', 3) in d)


	def test_keys(self):
		self.assertEqual(['x'], self.dtype(x=3).keys())
		self.assertEqual([], self.dtype().keys())


	def test_values(self):
		self.assertEqual([3], self.dtype(x=3).values())
		self.assertEqual([], self.dtype().values())


	def test_items(self):
		self.assertEqual([('x', 3)], self.dtype(x=3).items())
		self.assertEqual([], self.dtype().items())


	def test_iteration(self):
		d = self.dtype(x=3)
		found = []
		for k in d:
			found.append(k)
		self.assertEqual(['x'], found)

# TODO: complete tests



class FrozenDictTests(_DictReadingTests, _BaseFrozenDictTests, unittest.TestCase):
	"""
	Tests for L{dictops.frozendict}
	"""
	dtype = frozendict

	def test_copy(self):
		d = self.dtype(x=3)
		# .copy() returns a reference to the same object
		self.assertIs(d, d.copy())



class DictSanityCheckTests(_DictReadingTests, unittest.TestCase):
	"""
	Test that L{_DictReadingTests} works the same on python dicts.
	"""
	dtype = dict
