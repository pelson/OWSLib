from unittest import TestCase
from owslib.gml import _SubclassTagTracking


class A(object):
    __metaclass__ = _SubclassTagTracking
    TAGS = ['a']


class B(A):
    TAGS = ['b']


class B_plus(B):
    TAGS = ['b']


class C(A):
    TAGS = ['c', 'c+']


class D(A):
    TAGS = None


class TestSubclassTags(TestCase):
    def test_subclasses(self):
        self.assertEqual(A._SUBCLASS_TAGS, set(['a', 'c', 'b', 'c+']))
        self.assertEqual(B._SUBCLASS_TAGS, set(['b']))
        self.assertEqual(B_plus._SUBCLASS_TAGS, set(['b']))
        self.assertEqual(C._SUBCLASS_TAGS, set(['c', 'c+']))
        self.assertEqual(D._SUBCLASS_TAGS, set([]))


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=['-s', '--with-doctest'], exit=False)