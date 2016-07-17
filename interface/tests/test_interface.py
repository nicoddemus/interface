import pytest
from textwrap import dedent

from ..interface import implements, IncompleteImplementation, Interface


def test_valid_implementation():

    class I(Interface):  # pragma: nocover

        def m0(self):
            pass

        def m1(self, x):
            pass

        def m2(self, y):
            pass

    class C(implements(I)):  # pragma: nocover
        def m0(self):
            pass

        def m1(self, x):
            pass

        def m2(self, y):
            pass

    for i in range(10):
        class C(C):
            pass


def test_implement_multiple_interfaces_correctly():

    class I1(Interface):  # pragma: nocover
        def i1_method(self, arg1):
            pass

        def shared(self, a, b, c):
            pass

    class I2(Interface):  # pragma: nocover
        def i2_method(self, arg2):
            pass

        def shared(self, a, b, c):
            pass

    class C(implements(I1), implements(I2)):  # pragma: nocover
        def i1_method(self, arg1):
            pass

        def i2_method(self, arg2):
            pass

        def shared(self, a, b, c):
            pass

    assert set(C.interfaces()) == set([I1, I2])


def generative_fixture(g):
    """
    Decorator for turning a generator into a "parameterized" fixture that emits
    the generated values.
    """
    fixture_values = list(g())

    @pytest.fixture(params=fixture_values)
    def _fixture(request):
        return request.param

    return _fixture


@generative_fixture
def combine_interfaces():

    def combine_with_multiple_types(*interfaces):
        return list(map(implements, interfaces))

    def combine_with_single_type(*interfaces):
        return [implements(*interfaces)]

    yield combine_with_multiple_types
    yield combine_with_single_type


def test_require_implement_all_interfaces(combine_interfaces):

    class I1(Interface):  # pragma: nocover
        def i1_method(self, arg1):
            pass

        def shared(self, a, b, c):
            pass

    class I2(Interface):  # pragma: nocover
        def i2_method(self, arg2):
            pass

        def shared(self, a, b, c):
            pass

    bases = combine_interfaces(I1, I2)

    with pytest.raises(IncompleteImplementation):
        class C(*bases):  # pragma: nocover
            def i1_method(self, arg1):
                pass

            def i2_method(self, arg2):
                pass

    with pytest.raises(IncompleteImplementation):
        class C(*bases):  # pragma: nocover

            def i1_method(self, arg1):
                pass

            def shared(self, a, b, c):
                pass

    with pytest.raises(IncompleteImplementation):
        class C(*bases):  # pragma: nocover

            def i2_method(self, arg2):
                pass

            def shared(self, a, b, c):
                pass


def test_missing_methods():

    class I(Interface):  # pragma: nocover

        def m0(self):
            pass

        def m1(self):
            pass

        def m2(self, x):
            pass

    try:
        class C(implements(I)):
            def m0(self):  # pragma: nocover
                pass
    except IncompleteImplementation as e:
        actual = str(e)
        expected = dedent(
            """
            class C failed to implement interface I:

            The following methods of I were not implemented:
              - m1(self)
              - m2(self, x)"""
        )
        assert actual == expected
    else:
        pytest.fail("Should have raised IncompleteImplementation.")  # pragma: nocover


def test_incompatible_methods():

    class I(Interface):  # pragma: nocover

        def m0(self):
            pass

        def m1(self, x):
            pass

        def m2(self, x):
            pass

    try:
        class C(implements(I)):  # pragma: nocover
            def m0(self):
                pass

            def m1(self, y):
                pass

            def m2(self, x, y):
                pass

    except IncompleteImplementation as e:
        actual = str(e)
        expected = dedent(
            """
            class C failed to implement interface I:

            The following methods of I were implemented with invalid signatures:
              - m1(self, y) != m1(self, x)
              - m2(self, x, y) != m2(self, x)"""
        )
        assert actual == expected
    else:
        pytest.fail("Should have raised IncompleteImplementation.")  # pragma: nocover


def test_fail_multiple_interfaces():

    class I(Interface):  # pragma: nocover
        def m0(self, a):
            pass

    class J(Interface):  # pragma: nocover
        def m1(self, a):
            pass

    try:
        class D(implements(I, J)):  # pragma: nocover
            def m1(self, z):  # incorrect signature
                pass
    except IncompleteImplementation as e:
        actual = str(e)
        expected = dedent(
            """
            class D failed to implement interface I:

            The following methods of I were not implemented:
              - m0(self, a)

            class D failed to implemente interface J:

            The following methods of J were implemented with invalid signatures:
            - m1(self, z) != m1(self, a)
            """
        )


def test_implements_memoization():

    class I(Interface):
        pass

    class OtherI(Interface):
        pass

    assert implements(I) is implements(I)
    assert implements(I) is not implements(OtherI)


def test_reject_invalid_interface():

    with pytest.raises(TypeError):
        implements()

    class NotAnInterface:
        pass

    with pytest.raises(TypeError):
        implements(NotAnInterface)


def test_generated_attributes():

    class IFace(Interface):  # pragma: nocover
        def method(self, a, b):
            pass

        def method2(self, a, b, c):
            pass

    class OtherIFace(Interface):  # pragma: nocover

        def method3(self, a, b, c):
            pass

    impl = implements(IFace, OtherIFace)
    assert impl.__name__ == "ImplementsIFace_OtherIFace"

    expected_doc = dedent(
        """\
        Implementation of IFace, OtherIFace.

        Methods
        -------
        IFace.method(self, a, b)
        IFace.method2(self, a, b, c)
        OtherIFace.method3(self, a, b, c)"""
    )
    assert impl.__doc__ == expected_doc


def test_cant_instantiate_interface():

    class I(Interface):  # pragma: nocover
        pass

    with pytest.raises(TypeError):
        I()
