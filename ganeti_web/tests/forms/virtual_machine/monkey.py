# Copyright (c) 2008-2011 Jonathan M. Lange <jml@mumak.net> and the testtools
# authors. See AUTHORS for details.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Helpers for monkey-patching Python code."""

__all__ = [
    'MonkeyPatcher',
    'patch',
]


class MonkeyPatcher(object):
    """A set of monkey-patches that can be applied and removed all together.

    Use this to cover up attributes with new objects. Particularly useful for
    testing difficult code.
    """

    # Marker used to indicate that the patched attribute did not exist on the
    # object before we patched it.
    _NO_SUCH_ATTRIBUTE = object()

    def __init__(self, *patches):
        """Construct a `MonkeyPatcher`.

        :param patches: The patches to apply, each should be (obj, name,
            new_value). Providing patches here is equivalent to calling
            `add_patch`.
        """
        # List of patches to apply in (obj, name, value).
        self._patches_to_apply = []
        # List of the original values for things that have been patched.
        # (obj, name, value) format.
        self._originals = []
        for patch in patches:
            self.add_patch(*patch)

    def add_patch(self, obj, name, value):
        """Add a patch to overwrite 'name' on 'obj' with 'value'.

        The attribute C{name} on C{obj} will be assigned to C{value} when
        C{patch} is called or during C{run_with_patches}.

        You can restore the original values with a call to restore().
        """
        self._patches_to_apply.append((obj, name, value))

    def patch(self):
        """Apply all of the patches that have been specified with `add_patch`.

        Reverse this operation using L{restore}.
        """
        for obj, name, value in self._patches_to_apply:
            original_value = getattr(obj, name, self._NO_SUCH_ATTRIBUTE)
            self._originals.append((obj, name, original_value))
            setattr(obj, name, value)

    def restore(self):
        """Restore all original values to any patched objects.

        If the patched attribute did not exist on an object before it was
        patched, `restore` will delete the attribute so as to return the
        object to its original state.
        """
        while self._originals:
            obj, name, value = self._originals.pop()
            if value is self._NO_SUCH_ATTRIBUTE:
                delattr(obj, name)
            else:
                setattr(obj, name, value)

    def run_with_patches(self, f, *args, **kw):
        """Run 'f' with the given args and kwargs with all patches applied.

        Restores all objects to their original state when finished.
        """
        self.patch()
        try:
            return f(*args, **kw)
        finally:
            self.restore()


def patch(obj, attribute, value):
    """Set 'obj.attribute' to 'value' and return a callable to restore 'obj'.

    If 'attribute' is not set on 'obj' already, then the returned callable
    will delete the attribute when called.

    :param obj: An object to monkey-patch.
    :param attribute: The name of the attribute to patch.
    :param value: The value to set 'obj.attribute' to.
    :return: A nullary callable that, when run, will restore 'obj' to its
        original state.
    """
    patcher = MonkeyPatcher((obj, attribute, value))
    patcher.patch()
    return patcher.restore
