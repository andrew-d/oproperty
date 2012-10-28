
class oproperty(object):
    """
    This class implements a property-like class that is designed to allow for
    easy overriding of a base class's property.  This is especially useful for
    things like mixins, where you don't necessarily know what the base class's
    type is, and thus can't simply call BaseClass.prop.__set__.  And, since
    super() doesn't proxy the __set__ function, it can be quite difficult to
    override a base class's property while still conforming to DRY.

    Usage:
        class BaseClass(object):
            @property
            def prop(self):
                return 1234

        @property_overriding
        class DerivedClass(object):
            @oproperty
            def prop(self, orig):
                return orig() + 1


    FAQ:
        Q: Why is this necessary?
        A: I like mixins, conceptually, but Python makes it a bit tricky to do
           stuff like overriding a base class's property setter without
           explicitly knowing what that class is.  I wrote this to simplify
           things for me.

        Q: How does it work?
        A: In short, we pretend to be a property-like object, and instead of
           raising an error if the get/set/delete method doesn't exist, we call
           the next implementation found in a base class.  If the method *does*
           exist, we call it, but also pass along a pointer to the original
           method, so our overriding method can make use of the original
           method, if it's necessary.

        Q: Are there any caveats?
        A: Maybe.  I haven't properly tested this with things like abstract
           base classes (though I plan on doing so), and anything else that
           might rely on something actually being a property object.  I'm
           thinking of making this class derive from property, but I'm not sure
           that's necessarily a great idea.  Testing will continue :-)

        Q: What versions of Python does this work on?
        A: This should work on Python 2.6+, including Python 3.

    TODO:
        - Unsure what I want to do to deal with the case where the base
          property doesn't actually exist.  Options are currently:
            - Make the orig parameter a kwarg, and only pass it if the base
              property actually exists
            - The orig lambda can return a None if the base prop doesn't exist
            - Verify when the class type is set that there is an attribute
              with the appropriate name somewhere in the __mro__.  This would
              throw a RuntimeError(?) if we then try and override a property
              that doesn't already exist.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = doc

        # If we're not explicitly given a name to override, we try and
        # determine it by inspecting the names of any given functions.  If we
        # can't do this, we raise an error, since we don't know what to
        # override at all.
        if name is None:
            if fget is not None:
                name = fget.__name__
            elif fset is not None:
                name = fset.__name__
            elif fdel is not None:
                name = fdel.__name__
            else:
                raise RuntimeError("Can't create a property with no functions!")

        self._prop_name = name
        self.__class_type = None

    def __get__(self, obj, type=None):
        # If we have no object, return ourself.
        if obj is None:
            return self

        # Get the superclass's attribute.
        super_attr = self._get_super_attribute(obj, self._prop_name)

        # If we have an attribute, call and return it.  Otherwise, we simply
        # call the base property's __get__ function.
        if self.fget is not None:
            return self.fget(obj, lambda: super_attr.__get__(obj))
        else:
            return super_attr.__get__(obj)

    def __set__(self, obj, value):
        # Get the superclass's attribute.
        super_attr = self._get_super_attribute(obj, self._prop_name)

        # If we have an attribute, call and return it.  Otherwise, we simply
        # call the base property's __set__ function.
        if self.fset is not None:
            return self.fset(obj, value, lambda val: super_attr.__set__(obj, val))
        else:
            return super_attr.__set__(obj, value)

    def __delete__(self, obj):
        # Get the superclass's attribute.
        super_attr = self._get_super_attribute(obj, self._prop_name)

        # If we have an attribute, call and return it.  Otherwise, we simply
        # call the base property's __delete__ function.
        if self.fdel is not None:
            return self.fdel(obj, lambda: super_attr.__delete__(obj))
        else:
            return super_attr.__delete__(obj)

    def set_class_type(self, klass):
        """
        This function is called by our decorator, below, to tell this class
        where to start searching in the __mro__ list.
        """
        self.__class_type = klass

    def _get_super_attribute(self, obj, name):
        if self.__class_type is None:
            raise RuntimeError("You must decorate class!")

        # Get the MRO for the object
        if isinstance(obj, type):
            mro = obj.__mro__
        else:
            mro = obj.__class__.__mro__

        # Find this class in the MRO.
        for pos in range(len(mro)):
            if mro[pos] == self.__class_type:
                break

        # Look through classes higher in the MRO for this attribute.
        for pos in range(pos + 1, len(mro)):
            tmp = mro[pos]

            if isinstance(tmp, type) and name in tmp.__dict__:
                return tmp.__dict__[name]

        return None

    def getter(self, fget):
        self.fget = fget
        return self

    def setter(self, fset):
        self.fset = fset
        return self

    def deleter(self, fdel):
        self.fdel = fdel
        return self

    @classmethod
    def override_setter(klass, fset, **kwargs):
        """
        This is a convenience classmethod that lets you quickly override just
        the setter of a property, like so:
            class Derived(BaseClass):
                @oproperty.override_setter
                def prop(self, val, orig):
                    # Do new setter work...
                    pass
        """
        return klass(fset=fset, **kwargs)

    @classmethod
    def override_deleter(klass, fdel, **kwargs):
        """
        This is a convenience classmethod that lets you quickly override just
        the deleter of a property, like so:
            class Derived(BaseClass):
                @oproperty.override_deleter
                def prop(self, orig):
                    # Do new deleter work...
                    pass
        """
        return klass(fdel=fdel, **kwargs)



def property_overriding(klass):
    for name, val in klass.__dict__.items():
        if isinstance(val, oproperty):
            val.set_class_type(klass)

    return klass

