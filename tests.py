import unittest
from testing_helpers import BaseTestCase
from oproperty import *

# Generic base class
class BaseClass(object):
    def __init__(self):
        self.val = 123

    @property
    def prop(self):
        return self.val

    @prop.setter
    def prop(self, val):
        self.val = val

    @prop.deleter
    def prop(self):
        self.val = 0


class TestBasicImplementation(BaseTestCase):
    def setup(self):
        @property_overriding
        class DerivedClass(BaseClass):
            @oproperty
            def prop(self, orig):
                return orig() + 1

            @prop.setter
            def prop(self, val, orig):
                orig(val - 10)

        self.BaseClass = BaseClass
        self.DerivedClass = DerivedClass
        self.b = BaseClass()
        self.d = DerivedClass()

    def test_simple_get(self):
        self.assert_equal(self.d.prop, self.d.val + 1)

    def test_simple_set(self):
        self.d.prop = 555
        self.assert_equal(self.d.val, 555 - 10)

    def test_base_can_be_called(self):
        self.assert_equal(self.BaseClass.prop.__get__(self.d), self.d.val)
        self.BaseClass.prop.__set__(self.d, 444)
        self.assert_equal(self.d.val, 444)


class TestNamings(BaseTestCase):
    def build_class(self, **kwargs):
        class BaseClass(object):
            @property
            def prop1(self):
                return 123

            @property
            def prop2(self):
                return 456

        @property_overriding
        class DerivedClass(BaseClass):
            prop = oproperty(**kwargs)

        return DerivedClass()

    def test_fget_name(self):
        def prop1(self, orig):
            return orig()

        o = self.build_class(fget=prop1)
        self.assert_equal(o.prop, 123)

    def test_fset_name(self):
        def prop1(): pass
        o = self.build_class(fset=prop1)
        self.assert_equal(o.prop, 123)

    def test_fdel_name(self):
        def prop1(): pass
        o = self.build_class(fdel=prop1)
        self.assert_equal(o.prop, 123)

    def test_name_override(self):
        def not_a_prop(self, orig):
            return orig()

        o = self.build_class(name='prop2')
        self.assert_equal(o.prop, 456)

    def test_fails_if_no_name(self):
        with self.assert_raises(RuntimeError):
            o = self.build_class()


class TestMiscellaneous(BaseTestCase):
    def test_with_mixin(self):
        class BaseClass1(object):
            @property
            def prop(self):
                return 123

        class BaseClass2(object):
            @property
            def prop(self):
                return 456

        @property_overriding
        class MyMixin(object):
            @oproperty
            def prop(self, orig):
                return orig() + 5

        class MixedIn1(MyMixin, BaseClass1):
            pass

        class MixedIn2(MyMixin, BaseClass2):
            pass

        m1 = MixedIn1()
        m2 = MixedIn2()

        self.assert_equal(m1.prop, 123 + 5)
        self.assert_equal(m2.prop, 456 + 5)

    def test_multiple_overriding(self):
        @property_overriding
        class Derived1(BaseClass):
            @oproperty
            def prop(self, orig):
                return orig() + 1

        @property_overriding
        class Derived2(Derived1):
            @oproperty
            def prop(self, orig):
                return orig() + 5

        d1 = Derived1()
        d2 = Derived2()

        self.assert_equal(d1.prop, 123 + 1)
        self.assert_equal(d2.prop, 123 + 1 + 5)

    def test_with_other_overriding(self):
        @property_overriding
        class Derived1(BaseClass):
            @oproperty
            def prop(self, orig):
                return orig() + 1

        class Derived2(Derived1):
            pass

        d2 = Derived2()
        self.assert_equal(d2.prop, 123 + 1)

    def test_readonly(self):
        @property_overriding
        class Derived(BaseClass):
            @oproperty
            def readonly(self, orig):
                return orig() + 1

        d = Derived()
        with self.assert_raises(AttributeError):
            d.readonly = 'moo'

    def test_without_decorator(self):
        # @property_overriding      # NOTE: left out deliberately
        class Derived(BaseClass):
            @oproperty
            def prop(self, orig):
                return orig() + 1

        d = Derived()
        with self.assert_raises(RuntimeError):
            v = d.prop

    def test_classmethods(self):
        @property_overriding
        class Derived1(BaseClass):
            @oproperty.override_setter
            def prop(self, val, orig):
                orig(val + 100)

        @property_overriding
        class Derived2(BaseClass):
            @oproperty.override_deleter
            def prop(self, orig):
                orig()
                self.prop = 99

        d1 = Derived1()
        d2 = Derived2()

        d1.prop = 444
        self.assert_equal(d1.prop, 544)

        del d2.prop
        self.assert_equal(d2.prop, 99)

    # NOTE: This fails, since I haven't decided what to do in this case yet.
    # def test_with_no_base(self):
    #     class BaseClass(object):
    #         pass
    #
    #     @property_overriding
    #     class Derived(BaseClass):
    #         @oproperty
    #         def prop(self, orig):
    #             print(repr(orig))
    #             return orig() + 1
    #
    #     d = Derived()
    #     print(d.prop)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBasicImplementation))
    suite.addTest(unittest.makeSuite(TestNamings))
    suite.addTest(unittest.makeSuite(TestMiscellaneous))

    return suite

def main():
    unittest.main(defaultTest='suite', exit=False)
    print("Number of assertions: {0}".format(BaseTestCase.number_of_assertions))
    print("")

if __name__ == '__main__':
    main()

