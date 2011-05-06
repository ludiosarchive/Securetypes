import sys
import UserDict

from twisted.python import log
from twisted.trial import unittest

from securetypes import _securehash, is_dict_update_broken, securedict


# Copied from mypy.testhelpers
class ReallyEqualMixin(object):
	"""
	A mixin for your L{unittest.TestCase}s to better test object equality
	and inequality.  Details at:

	http://ludios.org/ivank/2010/10/testing-your-eq-ne-cmp/
	"""
	def assertReallyEqual(self, a, b):
		# assertEqual first, because it will have a good message if the
		# assertion fails.
		self.assertEqual(a, b)
		self.assertEqual(b, a)
		self.assertTrue(a == b)
		self.assertTrue(b == a)
		self.assertFalse(a != b)
		self.assertFalse(b != a)
		self.assertEqual(0, cmp(a, b))
		self.assertEqual(0, cmp(b, a))


	def assertReallyNotEqual(self, a, b):
		# assertNotEqual first, because it will have a good message if the
		# assertion fails.
		self.assertNotEqual(a, b)
		self.assertNotEqual(b, a)
		self.assertFalse(a == b)
		self.assertFalse(b == a)
		self.assertTrue(a != b)
		self.assertTrue(b != a)
		self.assertNotEqual(0, cmp(a, b))
		self.assertNotEqual(0, cmp(b, a))



class SecureHashTests(unittest.TestCase):
	"""
	Tests for L{securetypes._securehash}
	"""
	def test_strUnicode(self):
		self.assertNotEqual(_securehash("abc"), _securehash("123"))
		self.assertNotEqual(_securehash(""), _securehash("abc"))

		self.assertNotEqual(_securehash(u"abc"), _securehash(u"123"))
		self.assertNotEqual(_securehash(u""), _securehash(u"abc"))

		self.assertEqual(_securehash("abc"), _securehash(u"abc"))
		self.assertEqual(_securehash(""), _securehash(u""))
		self.assertNotEqual(_securehash("\xff"), _securehash(u"\xff"))

		# Test that bad implementation ideas weren't implemented
		self.assertNotEqual(_securehash("\xec\xb3\x8c"), _securehash(u"\ucccc"))
		self.assertNotEqual(_securehash("\xcc\x00"), _securehash(u"\u00cc"))
		self.assertNotEqual(_securehash("\xcc\x00\x00\x00"), _securehash(u"\u00cc"))


	def test_intLong(self):
		self.assertEqual(_securehash(123), _securehash(123L))
		self.assertEqual(_securehash(123), _securehash(123))
		self.assertEqual(_securehash(5), _securehash(5.0))
		self.assertEqual(_securehash(5L), _securehash(5.0))

		self.assertNotEqual(_securehash(5.0), _securehash(5.4))
		self.assertNotEqual(_securehash(5.0), _securehash(5.0000000000001))
		self.assertNotEqual(_securehash(0), _securehash(1))
		self.assertNotEqual(_securehash(-1), _securehash(0))

		# Test that bad implementation ideas weren't implemented
		self.assertNotEqual(_securehash(123), _securehash("123"))
		self.assertNotEqual(_securehash(123L), _securehash("123"))
		self.assertNotEqual(_securehash(123L), _securehash("123L"))


	def test_problematicFloats(self):
		self.assertEqual(_securehash(0.0), _securehash(-0.0))
		self.assertEqual(_securehash(0), _securehash(float('nan')))

		self.assertEqual(_securehash(314159), _securehash(float('inf')))
		self.assertEqual(_securehash(-271828), _securehash(float('-inf')))


	def test_boolInt(self):
		self.assertEqual(_securehash(True), _securehash(1))
		self.assertEqual(_securehash(False), _securehash(0))
		self.assertEqual(_securehash(False), _securehash(0.0))
		self.assertNotEqual(_securehash(True), _securehash(False))


	def test_noneType(self):
		self.assertNotEqual(_securehash(None), _securehash(False))
		self.assertNotEqual(_securehash(None), _securehash(True))
		self.assertNotEqual(_securehash(None), _securehash(0))


	def test_notSupportedYet(self):
		self.assertRaises(TypeError, lambda: _securehash((1, 2, 3)))



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
		self.assertNotIdentical(securedict(), {})

		self.assertEqual(securedict(one=1, two=2), {'one': 1, 'two': 2})

		# Test for some regressions caused by having a variable name in
		# the arglist of __new__ and update.
		self.assertEqual(
			securedict(x=1, y=2, z=3, k=4, v=5),
			{'x': 1, 'y': 2, 'z': 3, 'k': 4, 'v': 5})

		self.assertEqual(
			securedict({}, x=1, y=2, z=3, k=4, v=5),
			{'x': 1, 'y': 2, 'z': 3, 'k': 4, 'v': 5})


	def test_constructorUsesUpdate(self):
		s = SimpleUserDict()
		self.assertEqual(securedict(s), {1:1, 2:2, 3:3})


	def test_initDoesUpdate(self):
		"""
		You can use securedict.__init__ to update a securedict, just like
		you can use dict.__init__ to update a dict.
		"""
		d = securedict()
		d.__init__({1: 2})
		self.assertEqual(d, {1: 2})


	def test_equality(self):
		for a, b in [
			(securedict(), securedict()),
			(securedict({'one': 2}), securedict({'one': 2})),
			(securedict({'one': 2}), securedict(one=2)),
		]:
			self.assertReallyEqual(a, b)
			# If it is ==, it should also be also be <= and >=.
			self.assertTrue(a <= b)
			self.assertTrue(b <= a)
			self.assertTrue(a >= b)
			self.assertTrue(b >= a)

		for a, b in [
			(securedict({1: 2}), securedict({1: 3})),
			(securedict({1: 2}), securedict({1: 2, 3: 4})),
			(securedict({1: 2, 3: 4}), securedict({1: 2})),
			(securedict({1: 2}), None),
		]:
			self.assertReallyNotEqual(a, b)


	def test_bool(self):
		self.assertIdentical(not securedict(), True)
		self.assertTrue(securedict({1: 2}))
		self.assertIdentical(bool(securedict()), False)
		self.assertIdentical(bool(securedict({1: 2})), True)


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


	def test_getitem_bad_eq_hash(self):
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

	test_getitem_bad_eq_hash.todo = "securedict can only use built-ins as keys"


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


	def test_updateWithSecureDict(self):
		"""
		Updating a securedict with another securedict works.
		"""
		d = securedict()
		d.update(securedict({1:100}))
		self.assertEqual(d, {1:100})


	def test_updateAlgorithmNotBroken(self):
		"""
		securedict.update (and __init__) use pypy's dict update algorithm
		instead of the broken CPython algorithm.
		"""
		class DictSubclass(dict):
			def keys(self):
				return ['a']
			def __iter__(self):
				return ['b']

		special = DictSubclass(a=1, b=2, c=3)
		d = securedict()
		d.update(special)
		self.assertEqual(d, dict(a=1))


	def test_updateTooManyArgs(self):
		d = securedict()
		exc = self.assertRaises(TypeError, lambda: d.update({}, {}))
		self.assertEqual("update expected at most 1 arguments, got 2", str(exc))


	def test_dictASecureDict(self):
		dictedSecureDict = dict(securedict(a=1, b=2))
		if not is_dict_update_broken():
			self.assertEqual(dictedSecureDict, dict(a=1, b=2))
		else:
			self.assertNotEqual(dictedSecureDict, dict(a=1, b=2))


	def test_fromkeys(self):
		self.assertEqual(securedict.fromkeys('abc'), {'a':None, 'b':None, 'c':None})
		d = securedict()
		self.assertNotIdentical(d.fromkeys('abc'), d)
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
		self.assertIdentical(d.get('c'), None)
		self.assertEqual(d.get('c', 3), 3)
		d = securedict({'a': 1, 'b': 2})
		self.assertIdentical(d.get('c'), None)
		self.assertEqual(d.get('c', 3), 3)
		self.assertEqual(d.get('a'), 1)
		self.assertEqual(d.get('a', 3), 1)
		self.assertRaises(TypeError, d.get)
		self.assertRaises(TypeError, d.get, None, None, None)


	def test_setdefault(self):
		# dict.setdefault()
		d = securedict()
		self.assertIdentical(d.setdefault('key0'), None)
		d.setdefault('key0', [])
		self.assertIdentical(d.setdefault('key0'), None)
		d.setdefault('key', []).append(3)
		self.assertEqual(d['key'][0], 3)
		d.setdefault('key', []).append(4)
		self.assertEqual(len(d['key']), 2)
		self.assertRaises(TypeError, d.setdefault)


	def test_setdefault_bad_hash(self):
		d = securedict()

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

	test_setdefault_bad_hash.todo = "securedict can only use built-ins as keys"


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

	test_popitem.skip = "This test now passes, but it's probably just a fluke."


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


	def test_pop_bad_hash(self):
		d = securedict()

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

	test_pop_bad_hash.todo = "securedict can only use built-ins as keys"


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


	def test_str(self):
		"""
		str()ing a securedict should return the same thing repr() does
		"""
		d = securedict({1: 2})
		self.assertEqual(str(d), 'securedict({1: 2})')


	def test_repr_like_dict(self):
		d = securedict()
		d[1] = 2
		self.assertEqual(d.repr_like_dict(), '{1: 2}')


	def test_reprOtherRecursions(self):
		d = securedict({1: []})
		d[1].append(d)
		self.assertEqual(repr(d), 'securedict({1: [securedict({...})]})')

		d = [securedict({1: None})]
		d[0][1] = d
		self.assertEqual(repr(d), '[securedict({1: [...]})]')


	def test_lt_gt(self):
		"""
		< and > on a securedict compares the securedict's id(...).
		"""
		one = securedict({1: 2})
		two = securedict({3: 4})
		compares = [(one, two), (two, one)]
		for a, b in compares:
			assert id(a) != id(b)
			if id(a) < id(b):
				a, b = b, a
			self.assertTrue(a > b)
			self.assertTrue(a >= b)
			self.assertTrue(b < a)
			self.assertTrue(b <= a)
			self.assertFalse(a < b)
			self.assertFalse(a <= b)
			self.assertFalse(b > a)
			self.assertFalse(b >= a)
			self.assertEqual(1, cmp(a, b))
			self.assertEqual(-1, cmp(b, a))


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

	test_tuple_keyerror.todo = "securedict doesn't support tuple keys yet"


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

	if sys.version_info < (2, 5):
		test_bad_key.skip = "Python < 2.5 doesn't support this behavior"
	test_bad_key.todo = "securedict can only use built-ins as keys"


	def test_viewmethods(self):
		if hasattr({}, 'viewitems'): # Python 2.7+
			self.assertRaises(NotImplementedError, lambda: securedict().viewitems())
			self.assertRaises(NotImplementedError, lambda: securedict().viewkeys())
			self.assertEqual(list(securedict({1: 2}).viewvalues()), list({1: 2}.viewvalues()))
		else:
			self.assertRaises((AttributeError, TypeError), lambda: securedict().viewitems())
			self.assertRaises((AttributeError, TypeError), lambda: securedict().viewkeys())
			self.assertRaises((AttributeError, TypeError), lambda: securedict().viewvalues())


	def test_protectsAgainstCollisions(self):
		log.msg("If this test hangs, securedict is broken")

		hashWrapsAt = (sys.maxint + 1) * 2
		if hashWrapsAt not in (2**32, 2**64):
			log.msg("Warning: hashWrapsAt is an unusual %r" % (hashWrapsAt,))

		d = securedict()

		for n in xrange(100000):
			collider = 1 + n * (hashWrapsAt - 1)
			# In Python < 2.6, big longs sometimes hash to 0 instead
			# of 1 in this case.  This doesn't affect the test, because we
			# still gets tons of colliding keys.
			self.assertTrue(hash(collider) in (0, 1),
				"hash(%r) == %r" % (collider, hash(collider),))
			d[collider] = True

		# If the test doesn't hang for a long time, it passed.  We don't check
		# test duration because it will flake on someone.
