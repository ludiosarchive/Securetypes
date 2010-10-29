from twisted.trial import unittest
import UserDict

from mypy.dictops import securedict, attrdict, consensualfrozendict, frozendict
from mypy.testhelpers import ReallyEqualMixin


class SimpleUserDict:
	def __init__(self):
		self.d = {1:1, 2:2, 3:3}


	def keys(self):
		return self.d.keys()


	def __getitem__(self, i):
		return self.d[i]



class SecureDictTest(unittest.TestCase, ReallyEqualMixin):
	"""
	These tests are based on CPython 2.7's Python/Lib/test/test_dict.py 
	"""
	def test_constructor(self):
		# calling built-in types without argument must return empty
		self.assertEqual(securedict(), {})
		self.assertEqual(securedict(), securedict())
		self.assertIsNot(securedict(), {})

		self.assertEqual(securedict(one=1, two=2), {'one': 1, 'two': 2})


	def test_constructorUsesUpdate(self):
		s = SimpleUserDict()
		self.assertEqual(securedict(s), {1:1, 2:2, 3:3})


	def test_equality(self):
		for a, b in [
			(securedict(), securedict()),
			(securedict({'one': 2}), securedict({'one': 2})),
			(securedict({'one': 2}), securedict(one=2)),
		]:
			self.assertReallyEqual(a, b)

		for a, b in [
			(securedict({1: 2}), securedict({1: 3})),
			(securedict({1: 2}), securedict({1: 2, 3: 4})),
			(securedict({1: 2, 3: 4}), securedict({1: 2})),
			(securedict({1: 2}), None),
		]:
			self.assertReallyNotEqual(a, b)


	def test_bool(self):
		self.assertIs(not securedict(), True)
		self.assertTrue(securedict({1: 2}))
		self.assertIs(bool(securedict()), False)
		self.assertIs(bool(securedict({1: 2})), True)


	def test_keys(self):
		d = securedict()
		self.assertEqual(d.keys(), [])
		d = securedict({'a': 1, 'b': 2})
		k = d.keys()
		self.assertTrue(d.has_key('a'))
		self.assertTrue(d.has_key('b'))

		self.assertRaises(TypeError, d.keys, None)


	def test_values(self):
		d = securedict()
		self.assertEqual(d.values(), [])
		d = securedict({1:2})
		self.assertEqual(d.values(), [2])

		self.assertRaises(TypeError, d.values, None)


	def test_items(self):
		d = securedict()
		self.assertEqual(d.items(), [])

		d = securedict({1:2})
		self.assertEqual(d.items(), [(1, 2)])

		self.assertRaises(TypeError, d.items, None)


	def test_iteritems(self):
		d = securedict()
		self.assertEqual(list(d.iteritems()), [])

		d = securedict({1:2})
		self.assertEqual(list(d.iteritems()), [(1, 2)])

		self.assertRaises(TypeError, d.iteritems, None)


	def test_has_key(self):
		d = securedict()
		self.assertFalse(d.has_key('a'))
		d = securedict({'a': 1, 'b': 2})
		k = d.keys()
		k.sort()
		self.assertEqual(k, ['a', 'b'])

		self.assertRaises(TypeError, d.has_key)


	def test_contains(self):
		d = securedict()
		self.assertNotIn('a', d)
		self.assertFalse('a' in d)
		self.assertTrue('a' not in d)
		d = securedict({'a': 1, 'b': 2})
		self.assertIn('a', d)
		self.assertIn('b', d)
		self.assertNotIn('c', d)

		self.assertRaises(TypeError, d.__contains__)


	def test_len(self):
		d = securedict()
		self.assertEqual(len(d), 0)
		d = securedict({'a': 1, 'b': 2})
		self.assertEqual(len(d), 2)


	def test_getitem(self):
		d = securedict({'a': 1, 'b': 2})
		self.assertEqual(d['a'], 1)
		self.assertEqual(d['b'], 2)
		d['c'] = 3
		d['a'] = 4
		self.assertEqual(d['c'], 3)
		self.assertEqual(d['a'], 4)
		del d['b']
		self.assertEqual(d, {'a': 4, 'c': 3})
		self.assertEqual(d, securedict({'a': 4, 'c': 3}))

		self.assertRaises(TypeError, d.__getitem__)

		class BadEq(object):
			def __eq__(self, other):
				raise Exc()
			def __hash__(self):
				return 24

		d = securedict()
		d[BadEq()] = 42
		self.assertRaises(KeyError, d.__getitem__, 23)

		class Exc(Exception): pass

		class BadHash(object):
			fail = False
			def __hash__(self):
				if self.fail:
					raise Exc()
				else:
					return 42

		x = BadHash()
		d[x] = 42
		x.fail = True
		self.assertRaises(Exc, d.__getitem__, x)


	def test_delitem(self):
		d = securedict({'a': 1, 'b': 2})
		del d['a']
		def delc():
			del d['c']
		e = self.assertRaises(KeyError, delc)
		self.assertEqual(e.args, ('c',))


	def test_clear(self):
		d = securedict({1:1, 2:2, 3:3})
		d.clear()
		self.assertEqual(d, {})
		self.assertEqual(d, securedict())

		self.assertRaises(TypeError, d.clear, None)


	def test_update(self):
		d = securedict()
		d.update({1:100})
		d.update({2:20})
		d.update({1:1, 2:2, 3:3})
		self.assertEqual(d, {1:1, 2:2, 3:3})
		self.assertEqual(d, securedict({1:1, 2:2, 3:3}))

		d.update()
		self.assertEqual(d, {1:1, 2:2, 3:3})
		self.assertEqual(d, securedict({1:1, 2:2, 3:3}))

		self.assertRaises((TypeError, AttributeError), d.update, None)

		d.clear()
		d.update(SimpleUserDict())
		self.assertEqual(d, {1:1, 2:2, 3:3})
		self.assertEqual(d, securedict({1:1, 2:2, 3:3}))

		class Exc(Exception): pass

		d.clear()
		class FailingUserDict:
			def keys(self):
				raise Exc
		self.assertRaises(Exc, d.update, FailingUserDict())

		class FailingUserDict:
			def keys(self):
				class BogonIter:
					def __init__(self):
						self.i = 1
					def __iter__(self):
						return self
					def next(self):
						if self.i:
							self.i = 0
							return 'a'
						raise Exc
				return BogonIter()
			def __getitem__(self, key):
				return key
		self.assertRaises(Exc, d.update, FailingUserDict())

		class FailingUserDict:
			def keys(self):
				class BogonIter:
					def __init__(self):
						self.i = ord('a')
					def __iter__(self):
						return self
					def next(self):
						if self.i <= ord('z'):
							rtn = chr(self.i)
							self.i += 1
							return rtn
						raise StopIteration
				return BogonIter()
			def __getitem__(self, key):
				raise Exc
		self.assertRaises(Exc, d.update, FailingUserDict())

		class badseq(object):
			def __iter__(self):
				return self
			def next(self):
				raise Exc()

		self.assertRaises(Exc, securedict().update, badseq())

		self.assertRaises(ValueError, securedict().update, [(1, 2, 3)])


	def test_fromkeys(self):
		self.assertEqual(securedict.fromkeys('abc'), {'a':None, 'b':None, 'c':None})
		d = securedict()
		self.assertIsNot(d.fromkeys('abc'), d)
		self.assertEqual(d.fromkeys('abc'), {'a':None, 'b':None, 'c':None})
		self.assertEqual(d.fromkeys((4,5),0), {4:0, 5:0})
		self.assertEqual(d.fromkeys([]), {})
		def g():
			yield 1
		self.assertEqual(d.fromkeys(g()), {1:None})
		self.assertRaises(TypeError, securedict().fromkeys, 3)
		class dictlike(securedict): pass
		self.assertEqual(dictlike.fromkeys('a'), {'a':None})
		self.assertEqual(dictlike().fromkeys('a'), {'a':None})
		self.assertIsInstance(dictlike.fromkeys('a'), dictlike)
		self.assertIsInstance(dictlike().fromkeys('a'), dictlike)
		class mydict(securedict):
			def __new__(cls):
				return UserDict.UserDict()
		ud = mydict.fromkeys('ab')
		self.assertEqual(ud, {'a':None, 'b':None})
		self.assertIsInstance(ud, UserDict.UserDict)
		self.assertRaises(TypeError, dict.fromkeys)

		class Exc(Exception): pass

		class baddict1(securedict):
			def __init__(self):
				raise Exc()

		self.assertRaises(Exc, baddict1.fromkeys, [1])

		class BadSeq(object):
			def __iter__(self):
				return self
			def next(self):
				raise Exc()

		self.assertRaises(Exc, securedict.fromkeys, BadSeq())

		class baddict2(securedict):
			def __setitem__(self, key, value):
				raise Exc()

		self.assertRaises(Exc, baddict2.fromkeys, [1])

		# test fast path for dictionary inputs
		d = securedict(zip(range(6), range(6)))
		self.assertEqual(securedict.fromkeys(d, 0), securedict(zip(range(6), [0]*6)))


	def test_copy(self):
		d = securedict({1:1, 2:2, 3:3})
		self.assertEqual(d.copy(), {1:1, 2:2, 3:3})
		self.assertIsInstance(d.copy(), securedict)
		self.assertEqual(securedict().copy(), {})
		self.assertIsInstance(securedict().copy(), securedict)
		self.assertRaises(TypeError, d.copy, None)


	def test_get(self):
		d = securedict()
		self.assertIs(d.get('c'), None)
		self.assertEqual(d.get('c', 3), 3)
		d = securedict({'a': 1, 'b': 2})
		self.assertIs(d.get('c'), None)
		self.assertEqual(d.get('c', 3), 3)
		self.assertEqual(d.get('a'), 1)
		self.assertEqual(d.get('a', 3), 1)
		self.assertRaises(TypeError, d.get)
		self.assertRaises(TypeError, d.get, None, None, None)


	def test_setdefault(self):
		# dict.setdefault()
		d = securedict()
		self.assertIs(d.setdefault('key0'), None)
		d.setdefault('key0', [])
		self.assertIs(d.setdefault('key0'), None)
		d.setdefault('key', []).append(3)
		self.assertEqual(d['key'][0], 3)
		d.setdefault('key', []).append(4)
		self.assertEqual(len(d['key']), 2)
		self.assertRaises(TypeError, d.setdefault)

		class Exc(Exception): pass

		class BadHash(object):
			fail = False
			def __hash__(self):
				if self.fail:
					raise Exc()
				else:
					return 42

		x = BadHash()
		d[x] = 42
		x.fail = True
		self.assertRaises(Exc, d.setdefault, x, [])


	def test_popitem(self):
		# dict.popitem()
		for copymode in -1, +1:
			# -1: b has same structure as a
			# +1: b is a.copy()
			for log2size in range(12):
				size = 2**log2size
				a = securedict()
				b = securedict()
				for i in range(size):
					a[repr(i)] = i
					if copymode < 0:
						b[repr(i)] = i
				if copymode > 0:
					b = a.copy()
				for i in range(size):
					ka, va = ta = a.popitem()
					self.assertEqual(va, int(ka))
					kb, vb = tb = b.popitem()
					self.assertEqual(vb, int(kb))
					self.assertFalse(copymode < 0 and ta != tb)
				self.assertFalse(a)
				self.assertFalse(b)

		d = securedict()
		self.assertRaises(KeyError, d.popitem)

	test_popitem.todo = 'What in the world is this testing?'


	def test_pop(self):
		# Tests for pop with specified key
		d = securedict()
		k, v = 'abc', 'def'
		d[k] = v
		self.assertRaises(KeyError, d.pop, 'ghi')

		self.assertEqual(d.pop(k), v)
		self.assertEqual(len(d), 0)

		self.assertRaises(KeyError, d.pop, k)

		# verify longs/ints get same value when key > 32 bits
		# (for 64-bit archs).  See SF bug #689659.
		x = 4503599627370496L
		y = 4503599627370496
		h = securedict({x: 'anything', y: 'something else'})
		self.assertEqual(h[x], h[y])

		self.assertEqual(d.pop(k, v), v)
		d[k] = v
		self.assertEqual(d.pop(k, 1), v)

		self.assertRaises(TypeError, d.pop)

		class Exc(Exception): pass

		class BadHash(object):
			fail = False
			def __hash__(self):
				if self.fail:
					raise Exc()
				else:
					return 42

		x = BadHash()
		d[x] = 42
		x.fail = True
		self.assertRaises(Exc, d.pop, x)


	def test_mutatingiteration(self):
		# changing dict size during iteration
		d = securedict()
		d[1] = 1
		def mutate():
			for i in d:
				d[i+1] = 1
		self.assertRaises(RuntimeError, mutate)


	def test_repr(self):
		d = securedict()
		self.assertEqual(repr(d), 'securedict({})')
		d[1] = 2
		self.assertEqual(repr(d), 'securedict({1: 2})')
		d = securedict()
		d[1] = d
		self.assertEqual(repr(d), 'securedict({1: securedict({...})})')

		class Exc(Exception): pass

		class BadRepr(object):
			def __repr__(self):
				raise Exc()

		d = securedict({1: BadRepr()})
		self.assertRaises(Exc, repr, d)


	def test_reprLikeDict(self):
		d = securedict()
		d[1] = 2
		self.assertEqual(d.reprLikeDict(), '{1: 2}')


	def test_reprOtherRecursions(self):
		d = securedict({1: []})
		d[1].append(d)
		self.assertEqual(repr(d), 'securedict({1: [securedict({...})]})')

		d = [securedict({1: None})]
		d[0][1] = d
		self.assertEqual(repr(d), '[securedict({1: [...]})]')


	def test_le(self):
		self.assertFalse(securedict() < securedict())
		self.assertFalse(securedict({1: 2}) < securedict({1L: 2L}))

		class Exc(Exception): pass

		class BadCmp(object):
			def __eq__(self, other):
				raise Exc()
			def __hash__(self):
				return 42

		d1 = securedict({BadCmp(): 1})
		d2 = securedict({1: 1})

		self.assertRaises(Exc, lambda: d1 < d2)

	test_le.todo = "The behavior of > and < on a securedict is undefined"


	def test_missing(self):
		# Make sure securedict doesn't have a __missing__ method
		self.assertFalse(hasattr(securedict, "__missing__"))
		self.assertFalse(hasattr(securedict(), "__missing__"))
		# Test several cases:
		# (D) subclass defines __missing__ method returning a value
		# (E) subclass defines __missing__ method raising RuntimeError
		# (F) subclass sets __missing__ instance variable (no effect)
		# (G) subclass doesn't define __missing__ at a all
		class D(securedict):
			def __missing__(self, key):
				return 42
		d = D({1: 2, 3: 4})
		self.assertEqual(d[1], 2)
		self.assertEqual(d[3], 4)
		self.assertNotIn(2, d)
		self.assertNotIn(2, d.keys())
		self.assertEqual(d[2], 42)

		class E(securedict):
			def __missing__(self, key):
				raise RuntimeError(key)

		def get(obj, key):
			obj[key]

		e = E()
		ex = self.assertRaises(RuntimeError, get, e, 42)
		self.assertEqual(ex.args, (42,))

		class F(securedict):
			def __init__(self):
				# An instance variable __missing__ should have no effect
				self.__missing__ = lambda key: None
		f = F()
		ex = self.assertRaises(KeyError, get, f, 42)
		self.assertEqual(ex.args, (42,))

		class G(securedict):
			pass
		g = G()
		ex = self.assertRaises(KeyError, get, g, 42)
		self.assertEqual(ex.args, (42,))


	def test_tuple_keyerror(self):
		def get(obj, key):
			obj[key]

		# SF #1576657
		d = securedict()
		ex = self.assertRaises(KeyError, get, d, (1,))
		self.assertEqual(ex.args, ((1,),))


	def test_bad_key(self):
		# Dictionary lookups should fail if __cmp__() raises an exception.
		class CustomException(Exception):
			pass

		class BadDictKey:
			def __hash__(self):
				return hash(self.__class__)

			def __cmp__(self, other):
				if isinstance(other, self.__class__):
					raise CustomException
				return other

		d = securedict()
		x1 = BadDictKey()
		x2 = BadDictKey()
		d[x1] = 1
		def execstmt(stmt, loc):
			exec stmt in loc
		for stmt in ['d[x2] = 2',
					 'z = d[x2]',
					 'x2 in d',
					 'd.has_key(x2)',
					 'd.get(x2)',
					 'd.setdefault(x2, 42)',
					 'd.pop(x2)',
					 'd.update({x2: 2})']:
			self.assertRaises(CustomException, execstmt, stmt, locals())


	def test_viewmethods(self):
		if hasattr({}, 'viewitems'): # Python 2.7+
			self.assertRaises(NotImplementedError, lambda: securedict().viewitems())
			self.assertRaises(NotImplementedError, lambda: securedict().viewkeys())
			self.assertEqual(list(securedict({1: 2}).viewvalues()), list({1: 2}.viewvalues()))
		else:
			self.assertRaises((AttributeError, TypeError), lambda: securedict().viewitems())
			self.assertRaises((AttributeError, TypeError), lambda: securedict().viewkeys())
			self.assertRaises((AttributeError, TypeError), lambda: securedict().viewvalues())



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
