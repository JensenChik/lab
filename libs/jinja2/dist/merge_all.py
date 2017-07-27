# -*- coding: utf-8 -*-



"""
    jinja2._compat
    ~~~~~~~~~~~~~~

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys

PY2 = sys.version_info[0] == 2
PYPY = hasattr(sys, 'pypy_translation_info')
_identity = lambda x: x


if not PY2:
    unichr = chr
    range_type = range
    text_type = str
    string_types = (str,)
    integer_types = (int,)

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    import pickle
    from io import BytesIO, StringIO
    NativeStringIO = StringIO

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    ifilter = filter
    imap = map
    izip = zip
    intern = sys.intern

    implements_iterator = _identity
    implements_to_string = _identity
    encode_filename = _identity

else:
    unichr = unichr
    text_type = unicode
    range_type = xrange
    string_types = (str, unicode)
    integer_types = (int, long)

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    import cPickle as pickle
    from cStringIO import StringIO as BytesIO, StringIO
    NativeStringIO = BytesIO

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    from itertools import imap, izip, ifilter
    intern = intern

    def implements_iterator(cls):
        cls.next = cls.__next__
        del cls.__next__
        return cls

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls

    def encode_filename(filename):
        if isinstance(filename, unicode):
            return filename.encode('utf-8')
        return filename


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.
    class metaclass(type):
        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})


try:
    from urllib.parse import quote_from_bytes as url_quote
except ImportError:
    from urllib import quote as url_quote

"""
    jinja2.utils
    ~~~~~~~~~~~~

    Utility functions.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import re
import json
import errno
from collections import deque
from threading import Lock
# from jinja2._compat import text_type, string_types, implements_iterator, \
#     url_quote


_word_split_re = re.compile(r'(\s+)')
_punctuation_re = re.compile(
    '^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % (
        '|'.join(map(re.escape, ('(', '<', '&lt;'))),
        '|'.join(map(re.escape, ('.', ',', ')', '>', '\n', '&gt;')))
    )
)
_simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
_striptags_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
_entity_re = re.compile(r'&([^;]+);')
_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
_digits = '0123456789'

# special singleton representing missing values for the runtime
missing = type('MissingType', (), {'__repr__': lambda x: 'missing'})()

# internal code
internal_code = set()

concat = u''.join

_slash_escape = '\\/' not in json.dumps('/')


def contextfunction(f):
    """This decorator can be used to mark a function or method context callable.
    A context callable is passed the active :class:`Context` as first argument when
    called from the template.  This is useful if a function wants to get access
    to the context or functions provided on the context object.  For example
    a function that returns a sorted list of template variables the current
    template exports could look like this::

        @contextfunction
        def get_exported_names(context):
            return sorted(context.exported_vars)
    """
    f.contextfunction = True
    return f


def evalcontextfunction(f):
    """This decorator can be used to mark a function or method as an eval
    context callable.  This is similar to the :func:`contextfunction`
    but instead of passing the context, an evaluation context object is
    passed.  For more information about the eval context, see
    :ref:`eval-context`.

    .. versionadded:: 2.4
    """
    f.evalcontextfunction = True
    return f


def environmentfunction(f):
    """This decorator can be used to mark a function or method as environment
    callable.  This decorator works exactly like the :func:`contextfunction`
    decorator just that the first argument is the active :class:`Environment`
    and not context.
    """
    f.environmentfunction = True
    return f


def internalcode(f):
    """Marks the function as internally used"""
    internal_code.add(f.__code__)
    return f


def is_undefined(obj):
    """Check if the object passed is undefined.  This does nothing more than
    performing an instance check against :class:`Undefined` but looks nicer.
    This can be used for custom filters or tests that want to react to
    undefined variables.  For example a custom default filter can look like
    this::

        def default(var, default=''):
            if is_undefined(var):
                return default
            return var
    """
    from jinja2.runtime import Undefined
    return isinstance(obj, Undefined)


def consume(iterable):
    """Consumes an iterable without doing anything with it."""
    for event in iterable:
        pass


def clear_caches():
    """Jinja2 keeps internal caches for environments and lexers.  These are
    used so that Jinja2 doesn't have to recreate environments and lexers all
    the time.  Normally you don't have to care about that but if you are
    measuring memory consumption you may want to clean the caches.
    """
    from jinja2.environment import _spontaneous_environments
    from jinja2.lexer import _lexer_cache
    _spontaneous_environments.clear()
    _lexer_cache.clear()


def import_string(import_name, silent=False):
    """Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).

    If the `silent` is True the return value will be `None` if the import
    fails.

    :return: imported object
    """
    try:
        if ':' in import_name:
            module, obj = import_name.split(':', 1)
        elif '.' in import_name:
            items = import_name.split('.')
            module = '.'.join(items[:-1])
            obj = items[-1]
        else:
            return __import__(import_name)
        return getattr(__import__(module, None, None, [obj]), obj)
    except (ImportError, AttributeError):
        if not silent:
            raise


def open_if_exists(filename, mode='rb'):
    """Returns a file descriptor for the filename if that file exists,
    otherwise `None`.
    """
    try:
        return open(filename, mode)
    except IOError as e:
        if e.errno not in (errno.ENOENT, errno.EISDIR, errno.EINVAL):
            raise


def object_type_repr(obj):
    """Returns the name of the object's type.  For some recognized
    singletons the name of the object is returned instead. (For
    example for `None` and `Ellipsis`).
    """
    if obj is None:
        return 'None'
    elif obj is Ellipsis:
        return 'Ellipsis'
    # __builtin__ in 2.x, builtins in 3.x
    if obj.__class__.__module__ in ('__builtin__', 'builtins'):
        name = obj.__class__.__name__
    else:
        name = obj.__class__.__module__ + '.' + obj.__class__.__name__
    return '%s object' % name


def pformat(obj, verbose=False):
    """Prettyprint an object.  Either use the `pretty` library or the
    builtin `pprint`.
    """
    try:
        from pretty import pretty
        return pretty(obj, verbose=verbose)
    except ImportError:
        from pprint import pformat
        return pformat(obj)


def urlize(text, trim_url_limit=None, rel=None, target=None):
    """Converts any URLs in text into clickable links. Works on http://,
    https:// and www. links. Links can have trailing punctuation (periods,
    commas, close-parens) and leading punctuation (opening parens) and
    it'll still do the right thing.

    If trim_url_limit is not None, the URLs in link text will be limited
    to trim_url_limit characters.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If target is not None, a target attribute will be added to the link.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None \
                                               and (x[:limit] + (len(x) >=limit and '...'
                                                                 or '')) or x
    words = _word_split_re.split(text_type(escape(text)))
    rel_attr = rel and ' rel="%s"' % text_type(escape(rel)) or ''
    target_attr = target and ' target="%s"' % escape(target) or ''

    for i, word in enumerate(words):
        match = _punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            if middle.startswith('www.') or (
                                            '@' not in middle and
                                        not middle.startswith('http://') and
                                    not middle.startswith('https://') and
                                    len(middle) > 0 and
                                middle[0] in _letters + _digits and (
                                    middle.endswith('.org') or
                                    middle.endswith('.net') or
                                middle.endswith('.com')
                    )):
                middle = '<a href="http://%s"%s%s>%s</a>' % (middle,
                                                             rel_attr, target_attr, trim_url(middle))
            if middle.startswith('http://') or \
                    middle.startswith('https://'):
                middle = '<a href="%s"%s%s>%s</a>' % (middle,
                                                      rel_attr, target_attr, trim_url(middle))
            if '@' in middle and not middle.startswith('www.') and \
                    not ':' in middle and _simple_email_re.match(middle):
                middle = '<a href="mailto:%s">%s</a>' % (middle, middle)
            if lead + middle + trail != word:
                words[i] = lead + middle + trail
    return u''.join(words)


def generate_lorem_ipsum(n=5, html=True, min=20, max=100):
    """Generate some lorem ipsum for the template."""
    from jinja2.constants import LOREM_IPSUM_WORDS
    from random import choice, randrange
    words = LOREM_IPSUM_WORDS.split()
    result = []

    for _ in range(n):
        next_capitalized = True
        last_comma = last_fullstop = 0
        word = None
        last = None
        p = []

        # each paragraph contains out of 20 to 100 words.
        for idx, _ in enumerate(range(randrange(min, max))):
            while True:
                word = choice(words)
                if word != last:
                    last = word
                    break
            if next_capitalized:
                word = word.capitalize()
                next_capitalized = False
            # add commas
            if idx - randrange(3, 8) > last_comma:
                last_comma = idx
                last_fullstop += 2
                word += ','
            # add end of sentences
            if idx - randrange(10, 20) > last_fullstop:
                last_comma = last_fullstop = idx
                word += '.'
                next_capitalized = True
            p.append(word)

        # ensure that the paragraph ends with a dot.
        p = u' '.join(p)
        if p.endswith(','):
            p = p[:-1] + '.'
        elif not p.endswith('.'):
            p += '.'
        result.append(p)

    if not html:
        return u'\n\n'.join(result)
    return Markup(u'\n'.join(u'<p>%s</p>' % escape(x) for x in result))


def unicode_urlencode(obj, charset='utf-8', for_qs=False):
    """URL escapes a single bytestring or unicode string with the
    given charset if applicable to URL safe quoting under all rules
    that need to be considered under all supported Python versions.

    If non strings are provided they are converted to their unicode
    representation first.
    """
    if not isinstance(obj, string_types):
        obj = text_type(obj)
    if isinstance(obj, text_type):
        obj = obj.encode(charset)
    safe = not for_qs and b'/' or b''
    rv = text_type(url_quote(obj, safe))
    if for_qs:
        rv = rv.replace('%20', '+')
    return rv


class LRUCache(object):
    """A simple LRU Cache implementation."""

    # this is fast for small capacities (something below 1000) but doesn't
    # scale.  But as long as it's only used as storage for templates this
    # won't do any harm.

    def __init__(self, capacity):
        self.capacity = capacity
        self._mapping = {}
        self._queue = deque()
        self._postinit()

    def _postinit(self):
        # alias all queue methods for faster lookup
        self._popleft = self._queue.popleft
        self._pop = self._queue.pop
        self._remove = self._queue.remove
        self._wlock = Lock()
        self._append = self._queue.append

    def __getstate__(self):
        return {
            'capacity':     self.capacity,
            '_mapping':     self._mapping,
            '_queue':       self._queue
        }

    def __setstate__(self, d):
        self.__dict__.update(d)
        self._postinit()

    def __getnewargs__(self):
        return (self.capacity,)

    def copy(self):
        """Return a shallow copy of the instance."""
        rv = self.__class__(self.capacity)
        rv._mapping.update(self._mapping)
        rv._queue = deque(self._queue)
        return rv

    def get(self, key, default=None):
        """Return an item from the cache dict or `default`"""
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        """Set `default` if the key is not in the cache otherwise
        leave unchanged. Return the value of this key.
        """
        self._wlock.acquire()
        try:
            try:
                return self[key]
            except KeyError:
                self[key] = default
                return default
        finally:
            self._wlock.release()

    def clear(self):
        """Clear the cache."""
        self._wlock.acquire()
        try:
            self._mapping.clear()
            self._queue.clear()
        finally:
            self._wlock.release()

    def __contains__(self, key):
        """Check if a key exists in this cache."""
        return key in self._mapping

    def __len__(self):
        """Return the current size of the cache."""
        return len(self._mapping)

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self._mapping
        )

    def __getitem__(self, key):
        """Get an item from the cache. Moves the item up so that it has the
        highest priority then.

        Raise a `KeyError` if it does not exist.
        """
        self._wlock.acquire()
        try:
            rv = self._mapping[key]
            if self._queue[-1] != key:
                try:
                    self._remove(key)
                except ValueError:
                    # if something removed the key from the container
                    # when we read, ignore the ValueError that we would
                    # get otherwise.
                    pass
                self._append(key)
            return rv
        finally:
            self._wlock.release()

    def __setitem__(self, key, value):
        """Sets the value for an item. Moves the item up so that it
        has the highest priority then.
        """
        self._wlock.acquire()
        try:
            if key in self._mapping:
                self._remove(key)
            elif len(self._mapping) == self.capacity:
                del self._mapping[self._popleft()]
            self._append(key)
            self._mapping[key] = value
        finally:
            self._wlock.release()

    def __delitem__(self, key):
        """Remove an item from the cache dict.
        Raise a `KeyError` if it does not exist.
        """
        self._wlock.acquire()
        try:
            del self._mapping[key]
            try:
                self._remove(key)
            except ValueError:
                # __getitem__ is not locked, it might happen
                pass
        finally:
            self._wlock.release()

    def items(self):
        """Return a list of items."""
        result = [(key, self._mapping[key]) for key in list(self._queue)]
        result.reverse()
        return result

    def iteritems(self):
        """Iterate over all items."""
        return iter(self.items())

    def values(self):
        """Return a list of all values."""
        return [x[1] for x in self.items()]

    def itervalue(self):
        """Iterate over all values."""
        return iter(self.values())

    def keys(self):
        """Return a list of all keys ordered by most recent usage."""
        return list(self)

    def iterkeys(self):
        """Iterate over all keys in the cache dict, ordered by
        the most recent usage.
        """
        return reversed(tuple(self._queue))

    __iter__ = iterkeys

    def __reversed__(self):
        """Iterate over the values in the cache dict, oldest items
        coming first.
        """
        return iter(tuple(self._queue))

    __copy__ = copy


# register the LRU cache as mutable mapping if possible
try:
    from collections import MutableMapping
    MutableMapping.register(LRUCache)
except ImportError:
    pass


def select_autoescape(enabled_extensions=('html', 'htm', 'xml'),
                      disabled_extensions=(),
                      default_for_string=True,
                      default=False):
    """Intelligently sets the initial value of autoescaping based on the
    filename of the template.  This is the recommended way to configure
    autoescaping if you do not want to write a custom function yourself.

    If you want to enable it for all templates created from strings or
    for all templates with `.html` and `.xml` extensions::

        from jinja2 import Environment, select_autoescape
        env = Environment(autoescape=select_autoescape(
            enabled_extensions=('html', 'xml'),
            default_for_string=True,
        ))

    Example configuration to turn it on at all times except if the template
    ends with `.txt`::

        from jinja2 import Environment, select_autoescape
        env = Environment(autoescape=select_autoescape(
            disabled_extensions=('txt',),
            default_for_string=True,
            default=True,
        ))

    The `enabled_extensions` is an iterable of all the extensions that
    autoescaping should be enabled for.  Likewise `disabled_extensions` is
    a list of all templates it should be disabled for.  If a template is
    loaded from a string then the default from `default_for_string` is used.
    If nothing matches then the initial value of autoescaping is set to the
    value of `default`.

    For security reasons this function operates case insensitive.

    .. versionadded:: 2.9
    """
    enabled_patterns = tuple('.' + x.lstrip('.').lower()
                             for x in enabled_extensions)
    disabled_patterns = tuple('.' + x.lstrip('.').lower()
                              for x in disabled_extensions)
    def autoescape(template_name):
        if template_name is None:
            return default_for_string
        template_name = template_name.lower()
        if template_name.endswith(enabled_patterns):
            return True
        if template_name.endswith(disabled_patterns):
            return False
        return default
    return autoescape


def htmlsafe_json_dumps(obj, dumper=None, **kwargs):
    """Works exactly like :func:`dumps` but is safe for use in ``<script>``
    tags.  It accepts the same arguments and returns a JSON string.  Note that
    this is available in templates through the ``|tojson`` filter which will
    also mark the result as safe.  Due to how this function escapes certain
    characters this is safe even if used outside of ``<script>`` tags.

    The following characters are escaped in strings:

    -   ``<``
    -   ``>``
    -   ``&``
    -   ``'``

    This makes it safe to embed such strings in any place in HTML with the
    notable exception of double quoted attributes.  In that case single
    quote your attributes or HTML escape it in addition.
    """
    if dumper is None:
        dumper = json.dumps
    rv = dumper(obj, **kwargs) \
        .replace(u'<', u'\\u003c') \
        .replace(u'>', u'\\u003e') \
        .replace(u'&', u'\\u0026') \
        .replace(u"'", u'\\u0027')
    return rv


@implements_iterator
class Cycler(object):
    """A cycle helper for templates."""

    def __init__(self, *items):
        if not items:
            raise RuntimeError('at least one item has to be provided')
        self.items = items
        self.reset()

    def reset(self):
        """Resets the cycle."""
        self.pos = 0

    @property
    def current(self):
        """Returns the current item."""
        return self.items[self.pos]

    def next(self):
        """Goes one item ahead and returns it."""
        rv = self.current
        self.pos = (self.pos + 1) % len(self.items)
        return rv

    __next__ = next


class Joiner(object):
    """A joining helper for templates."""

    def __init__(self, sep=u', '):
        self.sep = sep
        self.used = False

    def __call__(self):
        if not self.used:
            self.used = True
            return u''
        return self.sep


# does this python version support async for in and async generators?
try:
    exec('async def _():\n async for _ in ():\n  yield _')
    have_async_gen = True
except SyntaxError:
    have_async_gen = False


# Imported here because that's where it was in the past
from markupsafe import Markup, escape, soft_unicode




"""
    jinja2.defaults
    ~~~~~~~~~~~~~~~

    Jinja default filters and tags.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
# from jinja2._compat import range_type
# from jinja2.utils import generate_lorem_ipsum, Cycler, Joiner


# defaults for the parser / lexer
BLOCK_START_STRING = '{%'
BLOCK_END_STRING = '%}'
VARIABLE_START_STRING = '{{'
VARIABLE_END_STRING = '}}'
COMMENT_START_STRING = '{#'
COMMENT_END_STRING = '#}'
LINE_STATEMENT_PREFIX = None
LINE_COMMENT_PREFIX = None
TRIM_BLOCKS = False
LSTRIP_BLOCKS = False
NEWLINE_SEQUENCE = '\n'
KEEP_TRAILING_NEWLINE = False


# default filters, tests and namespace
from jinja2.filters import FILTERS as DEFAULT_FILTERS
from jinja2.tests import TESTS as DEFAULT_TESTS
DEFAULT_NAMESPACE = {
    'range':        range_type,
    'dict':         dict,
    'lipsum':       generate_lorem_ipsum,
    'cycler':       Cycler,
    'joiner':       Joiner
}


# default policies
DEFAULT_POLICIES = {
    'compiler.ascii_str':   True,
    'urlize.rel':           'noopener',
    'urlize.target':        None,
    'truncate.leeway':      5,
    'json.dumps_function':  None,
    'json.dumps_kwargs':    {'sort_keys': True},
}


# export all constants
__all__ = tuple(x for x in locals().keys() if x.isupper())




"""
    jinja2.visitor
    ~~~~~~~~~~~~~~

    This module implements a visitor for the nodes.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD.
"""
# from jinja2.nodes import Node


class NodeVisitor(object):
    """Walks the abstract syntax tree and call visitor functions for every
    node found.  The visitor functions may return values which will be
    forwarded by the `visit` method.

    Per default the visitor functions for the nodes are ``'visit_'`` +
    class name of the node.  So a `TryFinally` node visit function would
    be `visit_TryFinally`.  This behavior can be changed by overriding
    the `get_visitor` function.  If no visitor function exists for a node
    (return value `None`) the `generic_visit` visitor is used instead.
    """

    def get_visitor(self, node):
        """Return the visitor function for this node or `None` if no visitor
        exists for this node.  In that case the generic visit function is
        used instead.
        """
        method = 'visit_' + node.__class__.__name__
        return getattr(self, method, None)

    def visit(self, node, *args, **kwargs):
        """Visit a node."""
        f = self.get_visitor(node)
        if f is not None:
            return f(node, *args, **kwargs)
        return self.generic_visit(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        """Called if no explicit visitor function exists for a node."""
        for node in node.iter_child_nodes():
            self.visit(node, *args, **kwargs)


class NodeTransformer(NodeVisitor):
    """Walks the abstract syntax tree and allows modifications of nodes.

    The `NodeTransformer` will walk the AST and use the return value of the
    visitor functions to replace or remove the old node.  If the return
    value of the visitor function is `None` the node will be removed
    from the previous location otherwise it's replaced with the return
    value.  The return value may be the original node in which case no
    replacement takes place.
    """

    def generic_visit(self, node, *args, **kwargs):
        for field, old_value in node.iter_fields():
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, Node):
                        value = self.visit(value, *args, **kwargs)
                        if value is None:
                            continue
                        elif not isinstance(value, Node):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, Node):
                new_node = self.visit(old_value, *args, **kwargs)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node

    def visit_list(self, node, *args, **kwargs):
        """As transformers may return lists in some places this method
        can be used to enforce a list as return value.
        """
        rv = self.visit(node, *args, **kwargs)
        if not isinstance(rv, list):
            rv = [rv]
        return rv





"""
    jinja2.optimizer
    ~~~~~~~~~~~~~~~~

    The jinja optimizer is currently trying to constant fold a few expressions
    and modify the AST in place so that it should be easier to evaluate it.

    Because the AST does not contain all the scoping information and the
    compiler has to find that out, we cannot do all the optimizations we
    want.  For example loop unrolling doesn't work because unrolled loops would
    have a different scoping.

    The solution would be a second syntax tree that has the scoping rules stored.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD.
"""
# from jinja2 import nodes
# from jinja2.visitor import NodeTransformer


def optimize(node, environment):
    """The context hint can be used to perform an static optimization
    based on the context given."""
    optimizer = Optimizer(environment)
    return optimizer.visit(node)


class Optimizer(NodeTransformer):

    def __init__(self, environment):
        self.environment = environment

    def fold(self, node, eval_ctx=None):
        """Do constant folding."""
        node = self.generic_visit(node)
        try:
            return nodes.Const.from_untrusted(node.as_const(eval_ctx),
                                              lineno=node.lineno,
                                              environment=self.environment)
        except nodes.Impossible:
            return node

    visit_Add = visit_Sub = visit_Mul = visit_Div = visit_FloorDiv = \
        visit_Pow = visit_Mod = visit_And = visit_Or = visit_Pos = visit_Neg = \
        visit_Not = visit_Compare = visit_Getitem = visit_Getattr = visit_Call = \
        visit_Filter = visit_Test = visit_CondExpr = fold
    del fold




"""
    jinja2.exceptions
    ~~~~~~~~~~~~~~~~~

    Jinja exceptions.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
# from jinja2._compat import imap, text_type, PY2, implements_to_string


class TemplateError(Exception):
    """Baseclass for all template errors."""

    if PY2:
        def __init__(self, message=None):
            if message is not None:
                message = text_type(message).encode('utf-8')
            Exception.__init__(self, message)

        @property
        def message(self):
            if self.args:
                message = self.args[0]
                if message is not None:
                    return message.decode('utf-8', 'replace')

        def __unicode__(self):
            return self.message or u''
    else:
        def __init__(self, message=None):
            Exception.__init__(self, message)

        @property
        def message(self):
            if self.args:
                message = self.args[0]
                if message is not None:
                    return message


@implements_to_string
class TemplateNotFound(IOError, LookupError, TemplateError):
    """Raised if a template does not exist."""

    # looks weird, but removes the warning descriptor that just
    # bogusly warns us about message being deprecated
    message = None

    def __init__(self, name, message=None):
        IOError.__init__(self)
        if message is None:
            message = name
        self.message = message
        self.name = name
        self.templates = [name]

    def __str__(self):
        return self.message


class TemplatesNotFound(TemplateNotFound):
    """Like :class:`TemplateNotFound` but raised if multiple templates
    are selected.  This is a subclass of :class:`TemplateNotFound`
    exception, so just catching the base exception will catch both.

    .. versionadded:: 2.2
    """

    def __init__(self, names=(), message=None):
        if message is None:
            message = u'none of the templates given were found: ' + \
                      u', '.join(imap(text_type, names))
        TemplateNotFound.__init__(self, names and names[-1] or None, message)
        self.templates = list(names)


@implements_to_string
class TemplateSyntaxError(TemplateError):
    """Raised to tell the user that there is a problem with the template."""

    def __init__(self, message, lineno, name=None, filename=None):
        TemplateError.__init__(self, message)
        self.lineno = lineno
        self.name = name
        self.filename = filename
        self.source = None

        # this is set to True if the debug.translate_syntax_error
        # function translated the syntax error into a new traceback
        self.translated = False

    def __str__(self):
        # for translated errors we only return the message
        if self.translated:
            return self.message

        # otherwise attach some stuff
        location = 'line %d' % self.lineno
        name = self.filename or self.name
        if name:
            location = 'File "%s", %s' % (name, location)
        lines = [self.message, '  ' + location]

        # if the source is set, add the line to the output
        if self.source is not None:
            try:
                line = self.source.splitlines()[self.lineno - 1]
            except IndexError:
                line = None
            if line:
                lines.append('    ' + line.strip())

        return u'\n'.join(lines)


class TemplateAssertionError(TemplateSyntaxError):
    """Like a template syntax error, but covers cases where something in the
    template caused an error at compile time that wasn't necessarily caused
    by a syntax error.  However it's a direct subclass of
    :exc:`TemplateSyntaxError` and has the same attributes.
    """


class TemplateRuntimeError(TemplateError):
    """A generic runtime error in the template engine.  Under some situations
    Jinja may raise this exception.
    """


class UndefinedError(TemplateRuntimeError):
    """Raised if a template tries to operate on :class:`Undefined`."""


class SecurityError(TemplateRuntimeError):
    """Raised if a template tries to do something insecure if the
    sandbox is enabled.
    """


class FilterArgumentError(TemplateRuntimeError):
    """This error is raised if a filter was called with inappropriate
    arguments
    """



"""
    jinja2.idtracking
    ~~~~~~~~~~~~~~~~~

    Jinja idtracking.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""

# from jinja2.visitor import NodeVisitor
# from jinja2._compat import iteritems


VAR_LOAD_PARAMETER = 'param'
VAR_LOAD_RESOLVE = 'resolve'
VAR_LOAD_ALIAS = 'alias'
VAR_LOAD_UNDEFINED = 'undefined'


def find_symbols(nodes, parent_symbols=None):
    sym = Symbols(parent=parent_symbols)
    visitor = FrameSymbolVisitor(sym)
    for node in nodes:
        visitor.visit(node)
    return sym


def symbols_for_node(node, parent_symbols=None):
    sym = Symbols(parent=parent_symbols)
    sym.analyze_node(node)
    return sym


class Symbols(object):

    def __init__(self, parent=None):
        if parent is None:
            self.level = 0
        else:
            self.level = parent.level + 1
        self.parent = parent
        self.refs = {}
        self.loads = {}
        self.stores = set()

    def analyze_node(self, node, **kwargs):
        visitor = RootVisitor(self)
        visitor.visit(node, **kwargs)

    def _define_ref(self, name, load=None):
        ident = 'l_%d_%s' % (self.level, name)
        self.refs[name] = ident
        if load is not None:
            self.loads[ident] = load
        return ident

    def find_load(self, target):
        if target in self.loads:
            return self.loads[target]
        if self.parent is not None:
            return self.parent.find_load(target)

    def find_ref(self, name):
        if name in self.refs:
            return self.refs[name]
        if self.parent is not None:
            return self.parent.find_ref(name)

    def ref(self, name):
        rv = self.find_ref(name)
        if rv is None:
            raise AssertionError('Tried to resolve a name to a reference that '
                                 'was unknown to the frame (%r)' % name)
        return rv

    def copy(self):
        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.refs = self.refs.copy()
        rv.loads = self.loads.copy()
        rv.stores = self.stores.copy()
        return rv

    def store(self, name):
        self.stores.add(name)

        # If we have not see the name referenced yet, we need to figure
        # out what to set it to.
        if name not in self.refs:
            # If there is a parent scope we check if the name has a
            # reference there.  If it does it means we might have to alias
            # to a variable there.
            if self.parent is not None:
                outer_ref = self.parent.find_ref(name)
                if outer_ref is not None:
                    self._define_ref(name, load=(VAR_LOAD_ALIAS, outer_ref))
                    return

            # Otherwise we can just set it to undefined.
            self._define_ref(name, load=(VAR_LOAD_UNDEFINED, None))

    def declare_parameter(self, name):
        self.stores.add(name)
        return self._define_ref(name, load=(VAR_LOAD_PARAMETER, None))

    def load(self, name):
        target = self.find_ref(name)
        if target is None:
            self._define_ref(name, load=(VAR_LOAD_RESOLVE, name))

    def branch_update(self, branch_symbols):
        stores = {}
        for branch in branch_symbols:
            for target in branch.stores:
                if target in self.stores:
                    continue
                stores[target] = stores.get(target, 0) + 1

        for sym in branch_symbols:
            self.refs.update(sym.refs)
            self.loads.update(sym.loads)
            self.stores.update(sym.stores)

        for name, branch_count in iteritems(stores):
            if branch_count == len(branch_symbols):
                continue
            target = self.find_ref(name)
            assert target is not None, 'should not happen'

            if self.parent is not None:
                outer_target = self.parent.find_ref(name)
                if outer_target is not None:
                    self.loads[target] = (VAR_LOAD_ALIAS, outer_target)
                    continue
            self.loads[target] = (VAR_LOAD_RESOLVE, name)

    def dump_stores(self):
        rv = {}
        node = self
        while node is not None:
            for name in node.stores:
                if name not in rv:
                    rv[name] = self.find_ref(name)
            node = node.parent
        return rv

    def dump_param_targets(self):
        rv = set()
        node = self
        while node is not None:
            for target, (instr, _) in iteritems(self.loads):
                if instr == VAR_LOAD_PARAMETER:
                    rv.add(target)
            node = node.parent
        return rv


class RootVisitor(NodeVisitor):

    def __init__(self, symbols):
        self.sym_visitor = FrameSymbolVisitor(symbols)

    def _simple_visit(self, node, **kwargs):
        for child in node.iter_child_nodes():
            self.sym_visitor.visit(child)

    visit_Template = visit_Block = visit_Macro = visit_FilterBlock = \
        visit_Scope = visit_If = visit_ScopedEvalContextModifier = \
        _simple_visit

    def visit_AssignBlock(self, node, **kwargs):
        for child in node.body:
            self.sym_visitor.visit(child)

    def visit_CallBlock(self, node, **kwargs):
        for child in node.iter_child_nodes(exclude=('call',)):
            self.sym_visitor.visit(child)

    def visit_For(self, node, for_branch='body', **kwargs):
        if for_branch == 'body':
            self.sym_visitor.visit(node.target, store_as_param=True)
            branch = node.body
        elif for_branch == 'else':
            branch = node.else_
        elif for_branch == 'test':
            self.sym_visitor.visit(node.target, store_as_param=True)
            if node.test is not None:
                self.sym_visitor.visit(node.test)
            return
        else:
            raise RuntimeError('Unknown for branch')
        for item in branch or ():
            self.sym_visitor.visit(item)

    def visit_With(self, node, **kwargs):
        for target in node.targets:
            self.sym_visitor.visit(target)
        for child in node.body:
            self.sym_visitor.visit(child)

    def generic_visit(self, node, *args, **kwargs):
        raise NotImplementedError('Cannot find symbols for %r' %
                                  node.__class__.__name__)


class FrameSymbolVisitor(NodeVisitor):
    """A visitor for `Frame.inspect`."""

    def __init__(self, symbols):
        self.symbols = symbols

    def visit_Name(self, node, store_as_param=False, **kwargs):
        """All assignments to names go through this function."""
        if store_as_param or node.ctx == 'param':
            self.symbols.declare_parameter(node.name)
        elif node.ctx == 'store':
            self.symbols.store(node.name)
        elif node.ctx == 'load':
            self.symbols.load(node.name)

    def visit_If(self, node, **kwargs):
        self.visit(node.test, **kwargs)

        original_symbols = self.symbols

        def inner_visit(nodes):
            self.symbols = rv = original_symbols.copy()
            for subnode in nodes:
                self.visit(subnode, **kwargs)
            self.symbols = original_symbols
            return rv

        body_symbols = inner_visit(node.body)
        else_symbols = inner_visit(node.else_ or ())

        self.symbols.branch_update([body_symbols, else_symbols])

    def visit_Macro(self, node, **kwargs):
        self.symbols.store(node.name)

    def visit_Import(self, node, **kwargs):
        self.generic_visit(node, **kwargs)
        self.symbols.store(node.target)

    def visit_FromImport(self, node, **kwargs):
        self.generic_visit(node, **kwargs)
        for name in node.names:
            if isinstance(name, tuple):
                self.symbols.store(name[1])
            else:
                self.symbols.store(name)

    def visit_Assign(self, node, **kwargs):
        """Visit assignments in the correct order."""
        self.visit(node.node, **kwargs)
        self.visit(node.target, **kwargs)

    def visit_For(self, node, **kwargs):
        """Visiting stops at for blocks.  However the block sequence
        is visited as part of the outer scope.
        """
        self.visit(node.iter, **kwargs)

    def visit_CallBlock(self, node, **kwargs):
        self.visit(node.call, **kwargs)

    def visit_FilterBlock(self, node, **kwargs):
        self.visit(node.filter, **kwargs)

    def visit_With(self, node, **kwargs):
        for target in node.values:
            self.visit(target)

    def visit_AssignBlock(self, node, **kwargs):
        """Stop visiting at block assigns."""
        self.visit(node.target, **kwargs)

    def visit_Scope(self, node, **kwargs):
        """Stop visiting at scopes."""

    def visit_Block(self, node, **kwargs):
        """Stop visiting at blocks."""





"""
    jinja2.compiler
    ~~~~~~~~~~~~~~~

    Compiles nodes into python code.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from itertools import chain
from copy import deepcopy
from keyword import iskeyword as is_python_keyword
from functools import update_wrapper
# from jinja2 import nodes
# from jinja2.nodes import EvalContext
# from jinja2.visitor import NodeVisitor
# from jinja2.optimizer import Optimizer
# from jinja2.exceptions import TemplateAssertionError
# from jinja2.utils import Markup, concat, escape
# from jinja2._compat import range_type, text_type, string_types, \
#     iteritems, NativeStringIO, imap, izip
# from jinja2.idtracking import Symbols, VAR_LOAD_PARAMETER, \
#     VAR_LOAD_RESOLVE, VAR_LOAD_ALIAS, VAR_LOAD_UNDEFINED


operators = {
    'eq':       '==',
    'ne':       '!=',
    'gt':       '>',
    'gteq':     '>=',
    'lt':       '<',
    'lteq':     '<=',
    'in':       'in',
    'notin':    'not in'
}

# what method to iterate over items do we want to use for dict iteration
# in generated code?  on 2.x let's go with iteritems, on 3.x with items
if hasattr(dict, 'iteritems'):
    dict_item_iter = 'iteritems'
else:
    dict_item_iter = 'items'

code_features = ['division']

# does this python version support generator stops? (PEP 0479)
try:
    exec('from __future__ import generator_stop')
    code_features.append('generator_stop')
except SyntaxError:
    pass

# does this python version support yield from?
try:
    exec('def f(): yield from x()')
except SyntaxError:
    supports_yield_from = False
else:
    supports_yield_from = True


def optimizeconst(f):
    def new_func(self, node, frame, **kwargs):
        # Only optimize if the frame is not volatile
        if self.optimized and not frame.eval_ctx.volatile:
            new_node = self.optimizer.visit(node, frame.eval_ctx)
            if new_node != node:
                return self.visit(new_node, frame)
        return f(self, node, frame, **kwargs)
    return update_wrapper(new_func, f)


def generate(node, environment, name, filename, stream=None,
             defer_init=False, optimized=True):
    """Generate the python source for a node tree."""
    if not isinstance(node, nodes.Template):
        raise TypeError('Can\'t compile non template nodes')
    generator = environment.code_generator_class(environment, name, filename,
                                                 stream, defer_init,
                                                 optimized)
    generator.visit(node)
    if stream is None:
        return generator.stream.getvalue()


def has_safe_repr(value):
    """Does the node have a safe representation?"""
    if value is None or value is NotImplemented or value is Ellipsis:
        return True
    if type(value) in (bool, int, float, complex, range_type, Markup) + string_types:
        return True
    if type(value) in (tuple, list, set, frozenset):
        for item in value:
            if not has_safe_repr(item):
                return False
        return True
    elif type(value) is dict:
        for key, value in iteritems(value):
            if not has_safe_repr(key):
                return False
            if not has_safe_repr(value):
                return False
        return True
    return False


def find_undeclared(nodes, names):
    """Check if the names passed are accessed undeclared.  The return value
    is a set of all the undeclared names from the sequence of names found.
    """
    visitor = UndeclaredNameVisitor(names)
    try:
        for node in nodes:
            visitor.visit(node)
    except VisitorExit:
        pass
    return visitor.undeclared


class MacroRef(object):

    def __init__(self, node):
        self.node = node
        self.accesses_caller = False
        self.accesses_kwargs = False
        self.accesses_varargs = False


class Frame(object):
    """Holds compile time information for us."""

    def __init__(self, eval_ctx, parent=None):
        self.eval_ctx = eval_ctx
        self.symbols = Symbols(parent and parent.symbols or None)

        # a toplevel frame is the root + soft frames such as if conditions.
        self.toplevel = False

        # the root frame is basically just the outermost frame, so no if
        # conditions.  This information is used to optimize inheritance
        # situations.
        self.rootlevel = False

        # in some dynamic inheritance situations the compiler needs to add
        # write tests around output statements.
        self.require_output_check = parent and parent.require_output_check

        # inside some tags we are using a buffer rather than yield statements.
        # this for example affects {% filter %} or {% macro %}.  If a frame
        # is buffered this variable points to the name of the list used as
        # buffer.
        self.buffer = None

        # the name of the block we're in, otherwise None.
        self.block = parent and parent.block or None

        # the parent of this frame
        self.parent = parent

        if parent is not None:
            self.buffer = parent.buffer

    def copy(self):
        """Create a copy of the current one."""
        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.symbols = self.symbols.copy()
        return rv

    def inner(self):
        """Return an inner frame."""
        return Frame(self.eval_ctx, self)

    def soft(self):
        """Return a soft frame.  A soft frame may not be modified as
        standalone thing as it shares the resources with the frame it
        was created of, but it's not a rootlevel frame any longer.

        This is only used to implement if-statements.
        """
        rv = self.copy()
        rv.rootlevel = False
        return rv

    __copy__ = copy


class VisitorExit(RuntimeError):
    """Exception used by the `UndeclaredNameVisitor` to signal a stop."""


class DependencyFinderVisitor(NodeVisitor):
    """A visitor that collects filter and test calls."""

    def __init__(self):
        self.filters = set()
        self.tests = set()

    def visit_Filter(self, node):
        self.generic_visit(node)
        self.filters.add(node.name)

    def visit_Test(self, node):
        self.generic_visit(node)
        self.tests.add(node.name)

    def visit_Block(self, node):
        """Stop visiting at blocks."""


class UndeclaredNameVisitor(NodeVisitor):
    """A visitor that checks if a name is accessed without being
    declared.  This is different from the frame visitor as it will
    not stop at closure frames.
    """

    def __init__(self, names):
        self.names = set(names)
        self.undeclared = set()

    def visit_Name(self, node):
        if node.ctx == 'load' and node.name in self.names:
            self.undeclared.add(node.name)
            if self.undeclared == self.names:
                raise VisitorExit()
        else:
            self.names.discard(node.name)

    def visit_Block(self, node):
        """Stop visiting a blocks."""


class CompilerExit(Exception):
    """Raised if the compiler encountered a situation where it just
    doesn't make sense to further process the code.  Any block that
    raises such an exception is not further processed.
    """


class CodeGenerator(NodeVisitor):

    def __init__(self, environment, name, filename, stream=None,
                 defer_init=False, optimized=True):
        if stream is None:
            stream = NativeStringIO()
        self.environment = environment
        self.name = name
        self.filename = filename
        self.stream = stream
        self.created_block_context = False
        self.defer_init = defer_init
        self.optimized = optimized
        if optimized:
            self.optimizer = Optimizer(environment)

        # aliases for imports
        self.import_aliases = {}

        # a registry for all blocks.  Because blocks are moved out
        # into the global python scope they are registered here
        self.blocks = {}

        # the number of extends statements so far
        self.extends_so_far = 0

        # some templates have a rootlevel extends.  In this case we
        # can safely assume that we're a child template and do some
        # more optimizations.
        self.has_known_extends = False

        # the current line number
        self.code_lineno = 1

        # registry of all filters and tests (global, not block local)
        self.tests = {}
        self.filters = {}

        # the debug information
        self.debug_info = []
        self._write_debug_info = None

        # the number of new lines before the next write()
        self._new_lines = 0

        # the line number of the last written statement
        self._last_line = 0

        # true if nothing was written so far.
        self._first_write = True

        # used by the `temporary_identifier` method to get new
        # unique, temporary identifier
        self._last_identifier = 0

        # the current indentation
        self._indentation = 0

        # Tracks toplevel assignments
        self._assign_stack = []

        # Tracks parameter definition blocks
        self._param_def_block = []

    # -- Various compilation helpers

    def fail(self, msg, lineno):
        """Fail with a :exc:`TemplateAssertionError`."""
        raise TemplateAssertionError(msg, lineno, self.name, self.filename)

    def temporary_identifier(self):
        """Get a new unique identifier."""
        self._last_identifier += 1
        return 't_%d' % self._last_identifier

    def buffer(self, frame):
        """Enable buffering for the frame from that point onwards."""
        frame.buffer = self.temporary_identifier()
        self.writeline('%s = []' % frame.buffer)

    def return_buffer_contents(self, frame, force_unescaped=False):
        """Return the buffer contents of the frame."""
        if not force_unescaped:
            if frame.eval_ctx.volatile:
                self.writeline('if context.eval_ctx.autoescape:')
                self.indent()
                self.writeline('return Markup(concat(%s))' % frame.buffer)
                self.outdent()
                self.writeline('else:')
                self.indent()
                self.writeline('return concat(%s)' % frame.buffer)
                self.outdent()
                return
            elif frame.eval_ctx.autoescape:
                self.writeline('return Markup(concat(%s))' % frame.buffer)
                return
        self.writeline('return concat(%s)' % frame.buffer)

    def indent(self):
        """Indent by one."""
        self._indentation += 1

    def outdent(self, step=1):
        """Outdent by step."""
        self._indentation -= step

    def start_write(self, frame, node=None):
        """Yield or write into the frame buffer."""
        if frame.buffer is None:
            self.writeline('yield ', node)
        else:
            self.writeline('%s.append(' % frame.buffer, node)

    def end_write(self, frame):
        """End the writing process started by `start_write`."""
        if frame.buffer is not None:
            self.write(')')

    def simple_write(self, s, frame, node=None):
        """Simple shortcut for start_write + write + end_write."""
        self.start_write(frame, node)
        self.write(s)
        self.end_write(frame)

    def blockvisit(self, nodes, frame):
        """Visit a list of nodes as block in a frame.  If the current frame
        is no buffer a dummy ``if 0: yield None`` is written automatically.
        """
        try:
            self.writeline('pass')
            for node in nodes:
                self.visit(node, frame)
        except CompilerExit:
            pass

    def write(self, x):
        """Write a string into the output stream."""
        if self._new_lines:
            if not self._first_write:
                self.stream.write('\n' * self._new_lines)
                self.code_lineno += self._new_lines
                if self._write_debug_info is not None:
                    self.debug_info.append((self._write_debug_info,
                                            self.code_lineno))
                    self._write_debug_info = None
            self._first_write = False
            self.stream.write('    ' * self._indentation)
            self._new_lines = 0
        self.stream.write(x)

    def writeline(self, x, node=None, extra=0):
        """Combination of newline and write."""
        self.newline(node, extra)
        self.write(x)

    def newline(self, node=None, extra=0):
        """Add one or more newlines before the next write."""
        self._new_lines = max(self._new_lines, 1 + extra)
        if node is not None and node.lineno != self._last_line:
            self._write_debug_info = node.lineno
            self._last_line = node.lineno

    def signature(self, node, frame, extra_kwargs=None):
        """Writes a function call to the stream for the current node.
        A leading comma is added automatically.  The extra keyword
        arguments may not include python keywords otherwise a syntax
        error could occour.  The extra keyword arguments should be given
        as python dict.
        """
        # if any of the given keyword arguments is a python keyword
        # we have to make sure that no invalid call is created.
        kwarg_workaround = False
        for kwarg in chain((x.key for x in node.kwargs), extra_kwargs or ()):
            if is_python_keyword(kwarg):
                kwarg_workaround = True
                break

        for arg in node.args:
            self.write(', ')
            self.visit(arg, frame)

        if not kwarg_workaround:
            for kwarg in node.kwargs:
                self.write(', ')
                self.visit(kwarg, frame)
            if extra_kwargs is not None:
                for key, value in iteritems(extra_kwargs):
                    self.write(', %s=%s' % (key, value))
        if node.dyn_args:
            self.write(', *')
            self.visit(node.dyn_args, frame)

        if kwarg_workaround:
            if node.dyn_kwargs is not None:
                self.write(', **dict({')
            else:
                self.write(', **{')
            for kwarg in node.kwargs:
                self.write('%r: ' % kwarg.key)
                self.visit(kwarg.value, frame)
                self.write(', ')
            if extra_kwargs is not None:
                for key, value in iteritems(extra_kwargs):
                    self.write('%r: %s, ' % (key, value))
            if node.dyn_kwargs is not None:
                self.write('}, **')
                self.visit(node.dyn_kwargs, frame)
                self.write(')')
            else:
                self.write('}')

        elif node.dyn_kwargs is not None:
            self.write(', **')
            self.visit(node.dyn_kwargs, frame)

    def pull_dependencies(self, nodes):
        """Pull all the dependencies."""
        visitor = DependencyFinderVisitor()
        for node in nodes:
            visitor.visit(node)
        for dependency in 'filters', 'tests':
            mapping = getattr(self, dependency)
            for name in getattr(visitor, dependency):
                if name not in mapping:
                    mapping[name] = self.temporary_identifier()
                self.writeline('%s = environment.%s[%r]' %
                               (mapping[name], dependency, name))

    def enter_frame(self, frame):
        undefs = []
        for target, (action, param) in iteritems(frame.symbols.loads):
            if action == VAR_LOAD_PARAMETER:
                pass
            elif action == VAR_LOAD_RESOLVE:
                self.writeline('%s = resolve(%r)' %
                               (target, param))
            elif action == VAR_LOAD_ALIAS:
                self.writeline('%s = %s' % (target, param))
            elif action == VAR_LOAD_UNDEFINED:
                undefs.append(target)
            else:
                raise NotImplementedError('unknown load instruction')
        if undefs:
            self.writeline('%s = missing' % ' = '.join(undefs))

    def leave_frame(self, frame, with_python_scope=False):
        if not with_python_scope:
            undefs = []
            for target, _ in iteritems(frame.symbols.loads):
                undefs.append(target)
            if undefs:
                self.writeline('%s = missing' % ' = '.join(undefs))

    def func(self, name):
        if self.environment.is_async:
            return 'async def %s' % name
        return 'def %s' % name

    def macro_body(self, node, frame):
        """Dump the function def of a macro or call block."""
        frame = frame.inner()
        frame.symbols.analyze_node(node)
        macro_ref = MacroRef(node)

        explicit_caller = None
        skip_special_params = set()
        args = []
        for idx, arg in enumerate(node.args):
            if arg.name == 'caller':
                explicit_caller = idx
            if arg.name in ('kwargs', 'varargs'):
                skip_special_params.add(arg.name)
            args.append(frame.symbols.ref(arg.name))

        undeclared = find_undeclared(node.body, ('caller', 'kwargs', 'varargs'))

        if 'caller' in undeclared:
            # In older Jinja2 versions there was a bug that allowed caller
            # to retain the special behavior even if it was mentioned in
            # the argument list.  However thankfully this was only really
            # working if it was the last argument.  So we are explicitly
            # checking this now and error out if it is anywhere else in
            # the argument list.
            if explicit_caller is not None:
                try:
                    node.defaults[explicit_caller - len(node.args)]
                except IndexError:
                    self.fail('When defining macros or call blocks the '
                              'special "caller" argument must be omitted '
                              'or be given a default.', node.lineno)
            else:
                args.append(frame.symbols.declare_parameter('caller'))
            macro_ref.accesses_caller = True
        if 'kwargs' in undeclared and not 'kwargs' in skip_special_params:
            args.append(frame.symbols.declare_parameter('kwargs'))
            macro_ref.accesses_kwargs = True
        if 'varargs' in undeclared and not 'varargs' in skip_special_params:
            args.append(frame.symbols.declare_parameter('varargs'))
            macro_ref.accesses_varargs = True

        # macros are delayed, they never require output checks
        frame.require_output_check = False
        frame.symbols.analyze_node(node)
        self.writeline('%s(%s):' % (self.func('macro'), ', '.join(args)), node)
        self.indent()

        self.buffer(frame)
        self.enter_frame(frame)

        self.push_parameter_definitions(frame)
        for idx, arg in enumerate(node.args):
            ref = frame.symbols.ref(arg.name)
            self.writeline('if %s is missing:' % ref)
            self.indent()
            try:
                default = node.defaults[idx - len(node.args)]
            except IndexError:
                self.writeline('%s = undefined(%r, name=%r)' % (
                    ref,
                    'parameter %r was not provided' % arg.name,
                    arg.name))
            else:
                self.writeline('%s = ' % ref)
                self.visit(default, frame)
            self.mark_parameter_stored(ref)
            self.outdent()
        self.pop_parameter_definitions()

        self.blockvisit(node.body, frame)
        self.return_buffer_contents(frame, force_unescaped=True)
        self.leave_frame(frame, with_python_scope=True)
        self.outdent()

        return frame, macro_ref

    def macro_def(self, macro_ref, frame):
        """Dump the macro definition for the def created by macro_body."""
        arg_tuple = ', '.join(repr(x.name) for x in macro_ref.node.args)
        name = getattr(macro_ref.node, 'name', None)
        if len(macro_ref.node.args) == 1:
            arg_tuple += ','
        self.write('Macro(environment, macro, %r, (%s), %r, %r, %r, '
                   'context.eval_ctx.autoescape)' %
                   (name, arg_tuple, macro_ref.accesses_kwargs,
                    macro_ref.accesses_varargs, macro_ref.accesses_caller))

    def position(self, node):
        """Return a human readable position for the node."""
        rv = 'line %d' % node.lineno
        if self.name is not None:
            rv += ' in ' + repr(self.name)
        return rv

    def dump_local_context(self, frame):
        return '{%s}' % ', '.join(
            '%r: %s' % (name, target) for name, target
            in iteritems(frame.symbols.dump_stores()))

    def write_commons(self):
        """Writes a common preamble that is used by root and block functions.
        Primarily this sets up common local helpers and enforces a generator
        through a dead branch.
        """
        self.writeline('resolve = context.resolve_or_missing')
        self.writeline('undefined = environment.undefined')
        self.writeline('if 0: yield None')

    def push_parameter_definitions(self, frame):
        """Pushes all parameter targets from the given frame into a local
        stack that permits tracking of yet to be assigned parameters.  In
        particular this enables the optimization from `visit_Name` to skip
        undefined expressions for parameters in macros as macros can reference
        otherwise unbound parameters.
        """
        self._param_def_block.append(frame.symbols.dump_param_targets())

    def pop_parameter_definitions(self):
        """Pops the current parameter definitions set."""
        self._param_def_block.pop()

    def mark_parameter_stored(self, target):
        """Marks a parameter in the current parameter definitions as stored.
        This will skip the enforced undefined checks.
        """
        if self._param_def_block:
            self._param_def_block[-1].discard(target)

    def parameter_is_undeclared(self, target):
        """Checks if a given target is an undeclared parameter."""
        if not self._param_def_block:
            return False
        return target in self._param_def_block[-1]

    def push_assign_tracking(self):
        """Pushes a new layer for assignment tracking."""
        self._assign_stack.append(set())

    def pop_assign_tracking(self, frame):
        """Pops the topmost level for assignment tracking and updates the
        context variables if necessary.
        """
        vars = self._assign_stack.pop()
        if not frame.toplevel or not vars:
            return
        public_names = [x for x in vars if x[:1] != '_']
        if len(vars) == 1:
            name = next(iter(vars))
            ref = frame.symbols.ref(name)
            self.writeline('context.vars[%r] = %s' % (name, ref))
        else:
            self.writeline('context.vars.update({')
            for idx, name in enumerate(vars):
                if idx:
                    self.write(', ')
                ref = frame.symbols.ref(name)
                self.write('%r: %s' % (name, ref))
            self.write('})')
        if public_names:
            if len(public_names) == 1:
                self.writeline('context.exported_vars.add(%r)' %
                               public_names[0])
            else:
                self.writeline('context.exported_vars.update((%s))' %
                               ', '.join(imap(repr, public_names)))

    # -- Statement Visitors

    def visit_Template(self, node, frame=None):
        assert frame is None, 'no root frame allowed'
        eval_ctx = EvalContext(self.environment, self.name)

        from jinja2.runtime import __all__ as exported
        self.writeline('from __future__ import %s' % ', '.join(code_features))
        self.writeline('from jinja2.runtime import ' + ', '.join(exported))

        if self.environment.is_async:
            self.writeline('from jinja2.asyncsupport import auto_await, '
                           'auto_aiter, make_async_loop_context')

        # if we want a deferred initialization we cannot move the
        # environment into a local name
        envenv = not self.defer_init and ', environment=environment' or ''

        # do we have an extends tag at all?  If not, we can save some
        # overhead by just not processing any inheritance code.
        have_extends = node.find(nodes.Extends) is not None

        # find all blocks
        for block in node.find_all(nodes.Block):
            if block.name in self.blocks:
                self.fail('block %r defined twice' % block.name, block.lineno)
            self.blocks[block.name] = block

        # find all imports and import them
        for import_ in node.find_all(nodes.ImportedName):
            if import_.importname not in self.import_aliases:
                imp = import_.importname
                self.import_aliases[imp] = alias = self.temporary_identifier()
                if '.' in imp:
                    module, obj = imp.rsplit('.', 1)
                    self.writeline('from %s import %s as %s' %
                                   (module, obj, alias))
                else:
                    self.writeline('import %s as %s' % (imp, alias))

        # add the load name
        self.writeline('name = %r' % self.name)

        # generate the root render function.
        self.writeline('%s(context, missing=missing%s):' %
                       (self.func('root'), envenv), extra=1)
        self.indent()
        self.write_commons()

        # process the root
        frame = Frame(eval_ctx)
        if 'self' in find_undeclared(node.body, ('self',)):
            ref = frame.symbols.declare_parameter('self')
            self.writeline('%s = TemplateReference(context)' % ref)
        frame.symbols.analyze_node(node)
        frame.toplevel = frame.rootlevel = True
        frame.require_output_check = have_extends and not self.has_known_extends
        if have_extends:
            self.writeline('parent_template = None')
        self.enter_frame(frame)
        self.pull_dependencies(node.body)
        self.blockvisit(node.body, frame)
        self.leave_frame(frame, with_python_scope=True)
        self.outdent()

        # make sure that the parent root is called.
        if have_extends:
            if not self.has_known_extends:
                self.indent()
                self.writeline('if parent_template is not None:')
            self.indent()
            if supports_yield_from and not self.environment.is_async:
                self.writeline('yield from parent_template.'
                               'root_render_func(context)')
            else:
                self.writeline('%sfor event in parent_template.'
                               'root_render_func(context):' %
                               (self.environment.is_async and 'async ' or ''))
                self.indent()
                self.writeline('yield event')
                self.outdent()
            self.outdent(1 + (not self.has_known_extends))

        # at this point we now have the blocks collected and can visit them too.
        for name, block in iteritems(self.blocks):
            self.writeline('%s(context, missing=missing%s):' %
                           (self.func('block_' + name), envenv),
                           block, 1)
            self.indent()
            self.write_commons()
            # It's important that we do not make this frame a child of the
            # toplevel template.  This would cause a variety of
            # interesting issues with identifier tracking.
            block_frame = Frame(eval_ctx)
            undeclared = find_undeclared(block.body, ('self', 'super'))
            if 'self' in undeclared:
                ref = block_frame.symbols.declare_parameter('self')
                self.writeline('%s = TemplateReference(context)' % ref)
            if 'super' in undeclared:
                ref = block_frame.symbols.declare_parameter('super')
                self.writeline('%s = context.super(%r, '
                               'block_%s)' % (ref, name, name))
            block_frame.symbols.analyze_node(block)
            block_frame.block = name
            self.enter_frame(block_frame)
            self.pull_dependencies(block.body)
            self.blockvisit(block.body, block_frame)
            self.leave_frame(block_frame, with_python_scope=True)
            self.outdent()

        self.writeline('blocks = {%s}' % ', '.join('%r: block_%s' % (x, x)
                                                   for x in self.blocks),
                       extra=1)

        # add a function that returns the debug info
        self.writeline('debug_info = %r' % '&'.join('%s=%s' % x for x
                                                    in self.debug_info))

    def visit_Block(self, node, frame):
        """Call a block and register it for the template."""
        level = 0
        if frame.toplevel:
            # if we know that we are a child template, there is no need to
            # check if we are one
            if self.has_known_extends:
                return
            if self.extends_so_far > 0:
                self.writeline('if parent_template is None:')
                self.indent()
                level += 1
        context = node.scoped and (
            'context.derived(%s)' % self.dump_local_context(frame)) or 'context'

        if supports_yield_from and not self.environment.is_async and \
                        frame.buffer is None:
            self.writeline('yield from context.blocks[%r][0](%s)' % (
                node.name, context), node)
        else:
            loop = self.environment.is_async and 'async for' or 'for'
            self.writeline('%s event in context.blocks[%r][0](%s):' % (
                loop, node.name, context), node)
            self.indent()
            self.simple_write('event', frame)
            self.outdent()

        self.outdent(level)

    def visit_Extends(self, node, frame):
        """Calls the extender."""
        if not frame.toplevel:
            self.fail('cannot use extend from a non top-level scope',
                      node.lineno)

        # if the number of extends statements in general is zero so
        # far, we don't have to add a check if something extended
        # the template before this one.
        if self.extends_so_far > 0:

            # if we have a known extends we just add a template runtime
            # error into the generated code.  We could catch that at compile
            # time too, but i welcome it not to confuse users by throwing the
            # same error at different times just "because we can".
            if not self.has_known_extends:
                self.writeline('if parent_template is not None:')
                self.indent()
            self.writeline('raise TemplateRuntimeError(%r)' %
                           'extended multiple times')

            # if we have a known extends already we don't need that code here
            # as we know that the template execution will end here.
            if self.has_known_extends:
                raise CompilerExit()
            else:
                self.outdent()

        self.writeline('parent_template = environment.get_template(', node)
        self.visit(node.template, frame)
        self.write(', %r)' % self.name)
        self.writeline('for name, parent_block in parent_template.'
                       'blocks.%s():' % dict_item_iter)
        self.indent()
        self.writeline('context.blocks.setdefault(name, []).'
                       'append(parent_block)')
        self.outdent()

        # if this extends statement was in the root level we can take
        # advantage of that information and simplify the generated code
        # in the top level from this point onwards
        if frame.rootlevel:
            self.has_known_extends = True

        # and now we have one more
        self.extends_so_far += 1

    def visit_Include(self, node, frame):
        """Handles includes."""
        if node.ignore_missing:
            self.writeline('try:')
            self.indent()

        func_name = 'get_or_select_template'
        if isinstance(node.template, nodes.Const):
            if isinstance(node.template.value, string_types):
                func_name = 'get_template'
            elif isinstance(node.template.value, (tuple, list)):
                func_name = 'select_template'
        elif isinstance(node.template, (nodes.Tuple, nodes.List)):
            func_name = 'select_template'

        self.writeline('template = environment.%s(' % func_name, node)
        self.visit(node.template, frame)
        self.write(', %r)' % self.name)
        if node.ignore_missing:
            self.outdent()
            self.writeline('except TemplateNotFound:')
            self.indent()
            self.writeline('pass')
            self.outdent()
            self.writeline('else:')
            self.indent()

        skip_event_yield = False
        if node.with_context:
            loop = self.environment.is_async and 'async for' or 'for'
            self.writeline('%s event in template.root_render_func('
                           'template.new_context(context.get_all(), True, '
                           '%s)):' % (loop, self.dump_local_context(frame)))
        elif self.environment.is_async:
            self.writeline('for event in (await '
                           'template._get_default_module_async())'
                           '._body_stream:')
        else:
            if supports_yield_from:
                self.writeline('yield from template._get_default_module()'
                               '._body_stream')
                skip_event_yield = True
            else:
                self.writeline('for event in template._get_default_module()'
                               '._body_stream:')

        if not skip_event_yield:
            self.indent()
            self.simple_write('event', frame)
            self.outdent()

        if node.ignore_missing:
            self.outdent()

    def visit_Import(self, node, frame):
        """Visit regular imports."""
        self.writeline('%s = ' % frame.symbols.ref(node.target), node)
        if frame.toplevel:
            self.write('context.vars[%r] = ' % node.target)
        if self.environment.is_async:
            self.write('await ')
        self.write('environment.get_template(')
        self.visit(node.template, frame)
        self.write(', %r).' % self.name)
        if node.with_context:
            self.write('make_module%s(context.get_all(), True, %s)'
                       % (self.environment.is_async and '_async' or '',
                          self.dump_local_context(frame)))
        elif self.environment.is_async:
            self.write('_get_default_module_async()')
        else:
            self.write('_get_default_module()')
        if frame.toplevel and not node.target.startswith('_'):
            self.writeline('context.exported_vars.discard(%r)' % node.target)

    def visit_FromImport(self, node, frame):
        """Visit named imports."""
        self.newline(node)
        self.write('included_template = %senvironment.get_template('
                   % (self.environment.is_async and 'await ' or ''))
        self.visit(node.template, frame)
        self.write(', %r).' % self.name)
        if node.with_context:
            self.write('make_module%s(context.get_all(), True, %s)'
                       % (self.environment.is_async and '_async' or '',
                          self.dump_local_context(frame)))
        elif self.environment.is_async:
            self.write('_get_default_module_async()')
        else:
            self.write('_get_default_module()')

        var_names = []
        discarded_names = []
        for name in node.names:
            if isinstance(name, tuple):
                name, alias = name
            else:
                alias = name
            self.writeline('%s = getattr(included_template, '
                           '%r, missing)' % (frame.symbols.ref(alias), name))
            self.writeline('if %s is missing:' % frame.symbols.ref(alias))
            self.indent()
            self.writeline('%s = undefined(%r %% '
                           'included_template.__name__, '
                           'name=%r)' %
                           (frame.symbols.ref(alias),
                            'the template %%r (imported on %s) does '
                            'not export the requested name %s' % (
                                self.position(node),
                                repr(name)
                            ), name))
            self.outdent()
            if frame.toplevel:
                var_names.append(alias)
                if not alias.startswith('_'):
                    discarded_names.append(alias)

        if var_names:
            if len(var_names) == 1:
                name = var_names[0]
                self.writeline('context.vars[%r] = %s' %
                               (name, frame.symbols.ref(name)))
            else:
                self.writeline('context.vars.update({%s})' % ', '.join(
                    '%r: %s' % (name, frame.symbols.ref(name)) for name in var_names
                ))
        if discarded_names:
            if len(discarded_names) == 1:
                self.writeline('context.exported_vars.discard(%r)' %
                               discarded_names[0])
            else:
                self.writeline('context.exported_vars.difference_'
                               'update((%s))' % ', '.join(imap(repr, discarded_names)))

    def visit_For(self, node, frame):
        loop_frame = frame.inner()
        test_frame = frame.inner()
        else_frame = frame.inner()

        # try to figure out if we have an extended loop.  An extended loop
        # is necessary if the loop is in recursive mode if the special loop
        # variable is accessed in the body.
        extended_loop = node.recursive or 'loop' in \
                                          find_undeclared(node.iter_child_nodes(
                                              only=('body',)), ('loop',))

        loop_ref = None
        if extended_loop:
            loop_ref = loop_frame.symbols.declare_parameter('loop')

        loop_frame.symbols.analyze_node(node, for_branch='body')
        if node.else_:
            else_frame.symbols.analyze_node(node, for_branch='else')

        if node.test:
            loop_filter_func = self.temporary_identifier()
            test_frame.symbols.analyze_node(node, for_branch='test')
            self.writeline('%s(fiter):' % self.func(loop_filter_func), node.test)
            self.indent()
            self.enter_frame(test_frame)
            self.writeline(self.environment.is_async and 'async for ' or 'for ')
            self.visit(node.target, loop_frame)
            self.write(' in ')
            self.write(self.environment.is_async and 'auto_aiter(fiter)' or 'fiter')
            self.write(':')
            self.indent()
            self.writeline('if ', node.test)
            self.visit(node.test, test_frame)
            self.write(':')
            self.indent()
            self.writeline('yield ')
            self.visit(node.target, loop_frame)
            self.outdent(3)
            self.leave_frame(test_frame, with_python_scope=True)

        # if we don't have an recursive loop we have to find the shadowed
        # variables at that point.  Because loops can be nested but the loop
        # variable is a special one we have to enforce aliasing for it.
        if node.recursive:
            self.writeline('%s(reciter, loop_render_func, depth=0):' %
                           self.func('loop'), node)
            self.indent()
            self.buffer(loop_frame)

            # Use the same buffer for the else frame
            else_frame.buffer = loop_frame.buffer

        # make sure the loop variable is a special one and raise a template
        # assertion error if a loop tries to write to loop
        if extended_loop:
            self.writeline('%s = missing' % loop_ref)

        for name in node.find_all(nodes.Name):
            if name.ctx == 'store' and name.name == 'loop':
                self.fail('Can\'t assign to special loop variable '
                          'in for-loop target', name.lineno)

        if node.else_:
            iteration_indicator = self.temporary_identifier()
            self.writeline('%s = 1' % iteration_indicator)

        self.writeline(self.environment.is_async and 'async for ' or 'for ', node)
        self.visit(node.target, loop_frame)
        if extended_loop:
            if self.environment.is_async:
                self.write(', %s in await make_async_loop_context(' % loop_ref)
            else:
                self.write(', %s in LoopContext(' % loop_ref)
        else:
            self.write(' in ')

        if node.test:
            self.write('%s(' % loop_filter_func)
        if node.recursive:
            self.write('reciter')
        else:
            if self.environment.is_async and not extended_loop:
                self.write('auto_aiter(')
            self.visit(node.iter, frame)
            if self.environment.is_async and not extended_loop:
                self.write(')')
        if node.test:
            self.write(')')

        if node.recursive:
            self.write(', loop_render_func, depth):')
        else:
            self.write(extended_loop and '):' or ':')

        self.indent()
        self.enter_frame(loop_frame)

        self.blockvisit(node.body, loop_frame)
        if node.else_:
            self.writeline('%s = 0' % iteration_indicator)
        self.outdent()
        self.leave_frame(loop_frame, with_python_scope=node.recursive
                                                       and not node.else_)

        if node.else_:
            self.writeline('if %s:' % iteration_indicator)
            self.indent()
            self.enter_frame(else_frame)
            self.blockvisit(node.else_, else_frame)
            self.leave_frame(else_frame)
            self.outdent()

        # if the node was recursive we have to return the buffer contents
        # and start the iteration code
        if node.recursive:
            self.return_buffer_contents(loop_frame)
            self.outdent()
            self.start_write(frame, node)
            if self.environment.is_async:
                self.write('await ')
            self.write('loop(')
            if self.environment.is_async:
                self.write('auto_aiter(')
            self.visit(node.iter, frame)
            if self.environment.is_async:
                self.write(')')
            self.write(', loop)')
            self.end_write(frame)

    def visit_If(self, node, frame):
        if_frame = frame.soft()
        self.writeline('if ', node)
        self.visit(node.test, if_frame)
        self.write(':')
        self.indent()
        self.blockvisit(node.body, if_frame)
        self.outdent()
        if node.else_:
            self.writeline('else:')
            self.indent()
            self.blockvisit(node.else_, if_frame)
            self.outdent()

    def visit_Macro(self, node, frame):
        macro_frame, macro_ref = self.macro_body(node, frame)
        self.newline()
        if frame.toplevel:
            if not node.name.startswith('_'):
                self.write('context.exported_vars.add(%r)' % node.name)
            ref = frame.symbols.ref(node.name)
            self.writeline('context.vars[%r] = ' % node.name)
        self.write('%s = ' % frame.symbols.ref(node.name))
        self.macro_def(macro_ref, macro_frame)

    def visit_CallBlock(self, node, frame):
        call_frame, macro_ref = self.macro_body(node, frame)
        self.writeline('caller = ')
        self.macro_def(macro_ref, call_frame)
        self.start_write(frame, node)
        self.visit_Call(node.call, frame, forward_caller=True)
        self.end_write(frame)

    def visit_FilterBlock(self, node, frame):
        filter_frame = frame.inner()
        filter_frame.symbols.analyze_node(node)
        self.enter_frame(filter_frame)
        self.buffer(filter_frame)
        self.blockvisit(node.body, filter_frame)
        self.start_write(frame, node)
        self.visit_Filter(node.filter, filter_frame)
        self.end_write(frame)
        self.leave_frame(filter_frame)

    def visit_With(self, node, frame):
        with_frame = frame.inner()
        with_frame.symbols.analyze_node(node)
        self.enter_frame(with_frame)
        for idx, (target, expr) in enumerate(izip(node.targets, node.values)):
            self.newline()
            self.visit(target, with_frame)
            self.write(' = ')
            self.visit(expr, frame)
        self.blockvisit(node.body, with_frame)
        self.leave_frame(with_frame)

    def visit_ExprStmt(self, node, frame):
        self.newline(node)
        self.visit(node.node, frame)

    def visit_Output(self, node, frame):
        # if we have a known extends statement, we don't output anything
        # if we are in a require_output_check section
        if self.has_known_extends and frame.require_output_check:
            return

        allow_constant_finalize = True
        if self.environment.finalize:
            func = self.environment.finalize
            if getattr(func, 'contextfunction', False) or \
                    getattr(func, 'evalcontextfunction', False):
                allow_constant_finalize = False
            elif getattr(func, 'environmentfunction', False):
                finalize = lambda x: text_type(
                    self.environment.finalize(self.environment, x))
            else:
                finalize = lambda x: text_type(self.environment.finalize(x))
        else:
            finalize = text_type

        # if we are inside a frame that requires output checking, we do so
        outdent_later = False
        if frame.require_output_check:
            self.writeline('if parent_template is None:')
            self.indent()
            outdent_later = True

        # try to evaluate as many chunks as possible into a static
        # string at compile time.
        body = []
        for child in node.nodes:
            try:
                if not allow_constant_finalize:
                    raise nodes.Impossible()
                const = child.as_const(frame.eval_ctx)
            except nodes.Impossible:
                body.append(child)
                continue
            # the frame can't be volatile here, becaus otherwise the
            # as_const() function would raise an Impossible exception
            # at that point.
            try:
                if frame.eval_ctx.autoescape:
                    if hasattr(const, '__html__'):
                        const = const.__html__()
                    else:
                        const = escape(const)
                const = finalize(const)
            except Exception:
                # if something goes wrong here we evaluate the node
                # at runtime for easier debugging
                body.append(child)
                continue
            if body and isinstance(body[-1], list):
                body[-1].append(const)
            else:
                body.append([const])

        # if we have less than 3 nodes or a buffer we yield or extend/append
        if len(body) < 3 or frame.buffer is not None:
            if frame.buffer is not None:
                # for one item we append, for more we extend
                if len(body) == 1:
                    self.writeline('%s.append(' % frame.buffer)
                else:
                    self.writeline('%s.extend((' % frame.buffer)
                self.indent()
            for item in body:
                if isinstance(item, list):
                    val = repr(concat(item))
                    if frame.buffer is None:
                        self.writeline('yield ' + val)
                    else:
                        self.writeline(val + ',')
                else:
                    if frame.buffer is None:
                        self.writeline('yield ', item)
                    else:
                        self.newline(item)
                    close = 1
                    if frame.eval_ctx.volatile:
                        self.write('(escape if context.eval_ctx.autoescape'
                                   ' else to_string)(')
                    elif frame.eval_ctx.autoescape:
                        self.write('escape(')
                    else:
                        self.write('to_string(')
                    if self.environment.finalize is not None:
                        self.write('environment.finalize(')
                        if getattr(self.environment.finalize,
                                   "contextfunction", False):
                            self.write('context, ')
                        close += 1
                    self.visit(item, frame)
                    self.write(')' * close)
                    if frame.buffer is not None:
                        self.write(',')
            if frame.buffer is not None:
                # close the open parentheses
                self.outdent()
                self.writeline(len(body) == 1 and ')' or '))')

        # otherwise we create a format string as this is faster in that case
        else:
            format = []
            arguments = []
            for item in body:
                if isinstance(item, list):
                    format.append(concat(item).replace('%', '%%'))
                else:
                    format.append('%s')
                    arguments.append(item)
            self.writeline('yield ')
            self.write(repr(concat(format)) + ' % (')
            self.indent()
            for argument in arguments:
                self.newline(argument)
                close = 0
                if frame.eval_ctx.volatile:
                    self.write('(escape if context.eval_ctx.autoescape else'
                               ' to_string)(')
                    close += 1
                elif frame.eval_ctx.autoescape:
                    self.write('escape(')
                    close += 1
                if self.environment.finalize is not None:
                    self.write('environment.finalize(')
                    if getattr(self.environment.finalize,
                               'contextfunction', False):
                        self.write('context, ')
                    elif getattr(self.environment.finalize,
                                 'evalcontextfunction', False):
                        self.write('context.eval_ctx, ')
                    elif getattr(self.environment.finalize,
                                 'environmentfunction', False):
                        self.write('environment, ')
                    close += 1
                self.visit(argument, frame)
                self.write(')' * close + ', ')
            self.outdent()
            self.writeline(')')

        if outdent_later:
            self.outdent()

    def visit_Assign(self, node, frame):
        self.push_assign_tracking()
        self.newline(node)
        self.visit(node.target, frame)
        self.write(' = ')
        self.visit(node.node, frame)
        self.pop_assign_tracking(frame)

    def visit_AssignBlock(self, node, frame):
        self.push_assign_tracking()
        block_frame = frame.inner()
        # This is a special case.  Since a set block always captures we
        # will disable output checks.  This way one can use set blocks
        # toplevel even in extended templates.
        block_frame.require_output_check = False
        block_frame.symbols.analyze_node(node)
        self.enter_frame(block_frame)
        self.buffer(block_frame)
        self.blockvisit(node.body, block_frame)
        self.newline(node)
        self.visit(node.target, frame)
        self.write(' = (Markup if context.eval_ctx.autoescape '
                   'else identity)(concat(%s))' % block_frame.buffer)
        self.pop_assign_tracking(frame)
        self.leave_frame(block_frame)

    # -- Expression Visitors

    def visit_Name(self, node, frame):
        if node.ctx == 'store' and frame.toplevel:
            if self._assign_stack:
                self._assign_stack[-1].add(node.name)
        ref = frame.symbols.ref(node.name)

        # If we are looking up a variable we might have to deal with the
        # case where it's undefined.  We can skip that case if the load
        # instruction indicates a parameter which are always defined.
        if node.ctx == 'load':
            load = frame.symbols.find_load(ref)
            if not (load is not None and load[0] == VAR_LOAD_PARAMETER and \
                            not self.parameter_is_undeclared(ref)):
                self.write('(undefined(name=%r) if %s is missing else %s)' %
                           (node.name, ref, ref))
                return

        self.write(ref)

    def visit_Const(self, node, frame):
        val = node.as_const(frame.eval_ctx)
        if isinstance(val, float):
            self.write(str(val))
        else:
            self.write(repr(val))

    def visit_TemplateData(self, node, frame):
        try:
            self.write(repr(node.as_const(frame.eval_ctx)))
        except nodes.Impossible:
            self.write('(Markup if context.eval_ctx.autoescape else identity)(%r)'
                       % node.data)

    def visit_Tuple(self, node, frame):
        self.write('(')
        idx = -1
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item, frame)
        self.write(idx == 0 and ',)' or ')')

    def visit_List(self, node, frame):
        self.write('[')
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item, frame)
        self.write(']')

    def visit_Dict(self, node, frame):
        self.write('{')
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item.key, frame)
            self.write(': ')
            self.visit(item.value, frame)
        self.write('}')

    def binop(operator, interceptable=True):
        @optimizeconst
        def visitor(self, node, frame):
            if self.environment.sandboxed and \
                            operator in self.environment.intercepted_binops:
                self.write('environment.call_binop(context, %r, ' % operator)
                self.visit(node.left, frame)
                self.write(', ')
                self.visit(node.right, frame)
            else:
                self.write('(')
                self.visit(node.left, frame)
                self.write(' %s ' % operator)
                self.visit(node.right, frame)
            self.write(')')
        return visitor

    def uaop(operator, interceptable=True):
        @optimizeconst
        def visitor(self, node, frame):
            if self.environment.sandboxed and \
                            operator in self.environment.intercepted_unops:
                self.write('environment.call_unop(context, %r, ' % operator)
                self.visit(node.node, frame)
            else:
                self.write('(' + operator)
                self.visit(node.node, frame)
            self.write(')')
        return visitor

    visit_Add = binop('+')
    visit_Sub = binop('-')
    visit_Mul = binop('*')
    visit_Div = binop('/')
    visit_FloorDiv = binop('//')
    visit_Pow = binop('**')
    visit_Mod = binop('%')
    visit_And = binop('and', interceptable=False)
    visit_Or = binop('or', interceptable=False)
    visit_Pos = uaop('+')
    visit_Neg = uaop('-')
    visit_Not = uaop('not ', interceptable=False)
    del binop, uaop

    @optimizeconst
    def visit_Concat(self, node, frame):
        if frame.eval_ctx.volatile:
            func_name = '(context.eval_ctx.volatile and' \
                        ' markup_join or unicode_join)'
        elif frame.eval_ctx.autoescape:
            func_name = 'markup_join'
        else:
            func_name = 'unicode_join'
        self.write('%s((' % func_name)
        for arg in node.nodes:
            self.visit(arg, frame)
            self.write(', ')
        self.write('))')

    @optimizeconst
    def visit_Compare(self, node, frame):
        self.visit(node.expr, frame)
        for op in node.ops:
            self.visit(op, frame)

    def visit_Operand(self, node, frame):
        self.write(' %s ' % operators[node.op])
        self.visit(node.expr, frame)

    @optimizeconst
    def visit_Getattr(self, node, frame):
        self.write('environment.getattr(')
        self.visit(node.node, frame)
        self.write(', %r)' % node.attr)

    @optimizeconst
    def visit_Getitem(self, node, frame):
        # slices bypass the environment getitem method.
        if isinstance(node.arg, nodes.Slice):
            self.visit(node.node, frame)
            self.write('[')
            self.visit(node.arg, frame)
            self.write(']')
        else:
            self.write('environment.getitem(')
            self.visit(node.node, frame)
            self.write(', ')
            self.visit(node.arg, frame)
            self.write(')')

    def visit_Slice(self, node, frame):
        if node.start is not None:
            self.visit(node.start, frame)
        self.write(':')
        if node.stop is not None:
            self.visit(node.stop, frame)
        if node.step is not None:
            self.write(':')
            self.visit(node.step, frame)

    @optimizeconst
    def visit_Filter(self, node, frame):
        if self.environment.is_async:
            self.write('await auto_await(')
        self.write(self.filters[node.name] + '(')
        func = self.environment.filters.get(node.name)
        if func is None:
            self.fail('no filter named %r' % node.name, node.lineno)
        if getattr(func, 'contextfilter', False):
            self.write('context, ')
        elif getattr(func, 'evalcontextfilter', False):
            self.write('context.eval_ctx, ')
        elif getattr(func, 'environmentfilter', False):
            self.write('environment, ')

        # if the filter node is None we are inside a filter block
        # and want to write to the current buffer
        if node.node is not None:
            self.visit(node.node, frame)
        elif frame.eval_ctx.volatile:
            self.write('(context.eval_ctx.autoescape and'
                       ' Markup(concat(%s)) or concat(%s))' %
                       (frame.buffer, frame.buffer))
        elif frame.eval_ctx.autoescape:
            self.write('Markup(concat(%s))' % frame.buffer)
        else:
            self.write('concat(%s)' % frame.buffer)
        self.signature(node, frame)
        self.write(')')
        if self.environment.is_async:
            self.write(')')

    @optimizeconst
    def visit_Test(self, node, frame):
        self.write(self.tests[node.name] + '(')
        if node.name not in self.environment.tests:
            self.fail('no test named %r' % node.name, node.lineno)
        self.visit(node.node, frame)
        self.signature(node, frame)
        self.write(')')

    @optimizeconst
    def visit_CondExpr(self, node, frame):
        def write_expr2():
            if node.expr2 is not None:
                return self.visit(node.expr2, frame)
            self.write('undefined(%r)' % ('the inline if-'
                                          'expression on %s evaluated to false and '
                                          'no else section was defined.' % self.position(node)))

        self.write('(')
        self.visit(node.expr1, frame)
        self.write(' if ')
        self.visit(node.test, frame)
        self.write(' else ')
        write_expr2()
        self.write(')')

    @optimizeconst
    def visit_Call(self, node, frame, forward_caller=False):
        if self.environment.is_async:
            self.write('await auto_await(')
        if self.environment.sandboxed:
            self.write('environment.call(context, ')
        else:
            self.write('context.call(')
        self.visit(node.node, frame)
        extra_kwargs = forward_caller and {'caller': 'caller'} or None
        self.signature(node, frame, extra_kwargs)
        self.write(')')
        if self.environment.is_async:
            self.write(')')

    def visit_Keyword(self, node, frame):
        self.write(node.key + '=')
        self.visit(node.value, frame)

    # -- Unused nodes for extensions

    def visit_MarkSafe(self, node, frame):
        self.write('Markup(')
        self.visit(node.expr, frame)
        self.write(')')

    def visit_MarkSafeIfAutoescape(self, node, frame):
        self.write('(context.eval_ctx.autoescape and Markup or identity)(')
        self.visit(node.expr, frame)
        self.write(')')

    def visit_EnvironmentAttribute(self, node, frame):
        self.write('environment.' + node.name)

    def visit_ExtensionAttribute(self, node, frame):
        self.write('environment.extensions[%r].%s' % (node.identifier, node.name))

    def visit_ImportedName(self, node, frame):
        self.write(self.import_aliases[node.importname])

    def visit_InternalName(self, node, frame):
        self.write(node.name)

    def visit_ContextReference(self, node, frame):
        self.write('context')

    def visit_Continue(self, node, frame):
        self.writeline('continue', node)

    def visit_Break(self, node, frame):
        self.writeline('break', node)

    def visit_Scope(self, node, frame):
        scope_frame = frame.inner()
        scope_frame.symbols.analyze_node(node)
        self.enter_frame(scope_frame)
        self.blockvisit(node.body, scope_frame)
        self.leave_frame(scope_frame)

    def visit_EvalContextModifier(self, node, frame):
        for keyword in node.options:
            self.writeline('context.eval_ctx.%s = ' % keyword.key)
            self.visit(keyword.value, frame)
            try:
                val = keyword.value.as_const(frame.eval_ctx)
            except nodes.Impossible:
                frame.eval_ctx.volatile = True
            else:
                setattr(frame.eval_ctx, keyword.key, val)

    def visit_ScopedEvalContextModifier(self, node, frame):
        old_ctx_name = self.temporary_identifier()
        saved_ctx = frame.eval_ctx.save()
        self.writeline('%s = context.eval_ctx.save()' % old_ctx_name)
        self.visit_EvalContextModifier(node, frame)
        for child in node.body:
            self.visit(child, frame)
        frame.eval_ctx.revert(saved_ctx)
        self.writeline('context.eval_ctx.revert(%s)' % old_ctx_name)





"""
    jinja2.nodes
    ~~~~~~~~~~~~

    This module implements additional nodes derived from the ast base node.

    It also provides some node tree helper functions like `in_lineno` and
    `get_nodes` used by the parser and translator in order to normalize
    python and jinja nodes.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import types
import operator

from collections import deque
# from jinja2.utils import Markup
# from jinja2._compat import izip, with_metaclass, text_type, PY2


#: the types we support for context functions
_context_function_types = (types.FunctionType, types.MethodType)


_binop_to_func = {
    '*':        operator.mul,
    '/':        operator.truediv,
    '//':       operator.floordiv,
    '**':       operator.pow,
    '%':        operator.mod,
    '+':        operator.add,
    '-':        operator.sub
}

_uaop_to_func = {
    'not':      operator.not_,
    '+':        operator.pos,
    '-':        operator.neg
}

_cmpop_to_func = {
    'eq':       operator.eq,
    'ne':       operator.ne,
    'gt':       operator.gt,
    'gteq':     operator.ge,
    'lt':       operator.lt,
    'lteq':     operator.le,
    'in':       lambda a, b: a in b,
    'notin':    lambda a, b: a not in b
}


class Impossible(Exception):
    """Raised if the node could not perform a requested action."""


class NodeType(type):
    """A metaclass for nodes that handles the field and attribute
    inheritance.  fields and attributes from the parent class are
    automatically forwarded to the child."""

    def __new__(cls, name, bases, d):
        for attr in 'fields', 'attributes':
            storage = []
            storage.extend(getattr(bases[0], attr, ()))
            storage.extend(d.get(attr, ()))
            assert len(bases) == 1, 'multiple inheritance not allowed'
            assert len(storage) == len(set(storage)), 'layout conflict'
            d[attr] = tuple(storage)
        d.setdefault('abstract', False)
        return type.__new__(cls, name, bases, d)


class EvalContext(object):
    """Holds evaluation time information.  Custom attributes can be attached
    to it in extensions.
    """

    def __init__(self, environment, template_name=None):
        self.environment = environment
        if callable(environment.autoescape):
            self.autoescape = environment.autoescape(template_name)
        else:
            self.autoescape = environment.autoescape
        self.volatile = False

    def save(self):
        return self.__dict__.copy()

    def revert(self, old):
        self.__dict__.clear()
        self.__dict__.update(old)


def get_eval_context(node, ctx):
    if ctx is None:
        if node.environment is None:
            raise RuntimeError('if no eval context is passed, the '
                               'node must have an attached '
                               'environment.')
        return EvalContext(node.environment)
    return ctx


class Node(with_metaclass(NodeType, object)):
    """Baseclass for all Jinja2 nodes.  There are a number of nodes available
    of different types.  There are four major types:

    -   :class:`Stmt`: statements
    -   :class:`Expr`: expressions
    -   :class:`Helper`: helper nodes
    -   :class:`Template`: the outermost wrapper node

    All nodes have fields and attributes.  Fields may be other nodes, lists,
    or arbitrary values.  Fields are passed to the constructor as regular
    positional arguments, attributes as keyword arguments.  Each node has
    two attributes: `lineno` (the line number of the node) and `environment`.
    The `environment` attribute is set at the end of the parsing process for
    all nodes automatically.
    """
    fields = ()
    attributes = ('lineno', 'environment')
    abstract = True

    def __init__(self, *fields, **attributes):
        if self.abstract:
            raise TypeError('abstract nodes are not instanciable')
        if fields:
            if len(fields) != len(self.fields):
                if not self.fields:
                    raise TypeError('%r takes 0 arguments' %
                                    self.__class__.__name__)
                raise TypeError('%r takes 0 or %d argument%s' % (
                    self.__class__.__name__,
                    len(self.fields),
                    len(self.fields) != 1 and 's' or ''
                ))
            for name, arg in izip(self.fields, fields):
                setattr(self, name, arg)
        for attr in self.attributes:
            setattr(self, attr, attributes.pop(attr, None))
        if attributes:
            raise TypeError('unknown attribute %r' %
                            next(iter(attributes)))

    def iter_fields(self, exclude=None, only=None):
        """This method iterates over all fields that are defined and yields
        ``(key, value)`` tuples.  Per default all fields are returned, but
        it's possible to limit that to some fields by providing the `only`
        parameter or to exclude some using the `exclude` parameter.  Both
        should be sets or tuples of field names.
        """
        for name in self.fields:
            if (exclude is only is None) or \
                    (exclude is not None and name not in exclude) or \
                    (only is not None and name in only):
                try:
                    yield name, getattr(self, name)
                except AttributeError:
                    pass

    def iter_child_nodes(self, exclude=None, only=None):
        """Iterates over all direct child nodes of the node.  This iterates
        over all fields and yields the values of they are nodes.  If the value
        of a field is a list all the nodes in that list are returned.
        """
        for field, item in self.iter_fields(exclude, only):
            if isinstance(item, list):
                for n in item:
                    if isinstance(n, Node):
                        yield n
            elif isinstance(item, Node):
                yield item

    def find(self, node_type):
        """Find the first node of a given type.  If no such node exists the
        return value is `None`.
        """
        for result in self.find_all(node_type):
            return result

    def find_all(self, node_type):
        """Find all the nodes of a given type.  If the type is a tuple,
        the check is performed for any of the tuple items.
        """
        for child in self.iter_child_nodes():
            if isinstance(child, node_type):
                yield child
            for result in child.find_all(node_type):
                yield result

    def set_ctx(self, ctx):
        """Reset the context of a node and all child nodes.  Per default the
        parser will all generate nodes that have a 'load' context as it's the
        most common one.  This method is used in the parser to set assignment
        targets and other nodes to a store context.
        """
        todo = deque([self])
        while todo:
            node = todo.popleft()
            if 'ctx' in node.fields:
                node.ctx = ctx
            todo.extend(node.iter_child_nodes())
        return self

    def set_lineno(self, lineno, override=False):
        """Set the line numbers of the node and children."""
        todo = deque([self])
        while todo:
            node = todo.popleft()
            if 'lineno' in node.attributes:
                if node.lineno is None or override:
                    node.lineno = lineno
            todo.extend(node.iter_child_nodes())
        return self

    def set_environment(self, environment):
        """Set the environment for all nodes."""
        todo = deque([self])
        while todo:
            node = todo.popleft()
            node.environment = environment
            todo.extend(node.iter_child_nodes())
        return self

    def __eq__(self, other):
        return type(self) is type(other) and \
               tuple(self.iter_fields()) == tuple(other.iter_fields())

    def __ne__(self, other):
        return not self.__eq__(other)

    # Restore Python 2 hashing behavior on Python 3
    __hash__ = object.__hash__

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (arg, getattr(self, arg, None)) for
                      arg in self.fields)
        )

    def dump(self):
        def _dump(node):
            if not isinstance(node, Node):
                buf.append(repr(node))
                return

            buf.append('nodes.%s(' % node.__class__.__name__)
            if not node.fields:
                buf.append(')')
                return
            for idx, field in enumerate(node.fields):
                if idx:
                    buf.append(', ')
                value = getattr(node, field)
                if isinstance(value, list):
                    buf.append('[')
                    for idx, item in enumerate(value):
                        if idx:
                            buf.append(', ')
                        _dump(item)
                    buf.append(']')
                else:
                    _dump(value)
            buf.append(')')
        buf = []
        _dump(self)
        return ''.join(buf)



class Stmt(Node):
    """Base node for all statements."""
    abstract = True


class Helper(Node):
    """Nodes that exist in a specific context only."""
    abstract = True


class Template(Node):
    """Node that represents a template.  This must be the outermost node that
    is passed to the compiler.
    """
    fields = ('body',)


class Output(Stmt):
    """A node that holds multiple expressions which are then printed out.
    This is used both for the `print` statement and the regular template data.
    """
    fields = ('nodes',)


class Extends(Stmt):
    """Represents an extends statement."""
    fields = ('template',)


class For(Stmt):
    """The for loop.  `target` is the target for the iteration (usually a
    :class:`Name` or :class:`Tuple`), `iter` the iterable.  `body` is a list
    of nodes that are used as loop-body, and `else_` a list of nodes for the
    `else` block.  If no else node exists it has to be an empty list.

    For filtered nodes an expression can be stored as `test`, otherwise `None`.
    """
    fields = ('target', 'iter', 'body', 'else_', 'test', 'recursive')


class If(Stmt):
    """If `test` is true, `body` is rendered, else `else_`."""
    fields = ('test', 'body', 'else_')


class Macro(Stmt):
    """A macro definition.  `name` is the name of the macro, `args` a list of
    arguments and `defaults` a list of defaults if there are any.  `body` is
    a list of nodes for the macro body.
    """
    fields = ('name', 'args', 'defaults', 'body')


class CallBlock(Stmt):
    """Like a macro without a name but a call instead.  `call` is called with
    the unnamed macro as `caller` argument this node holds.
    """
    fields = ('call', 'args', 'defaults', 'body')


class FilterBlock(Stmt):
    """Node for filter sections."""
    fields = ('body', 'filter')


class With(Stmt):
    """Specific node for with statements.  In older versions of Jinja the
    with statement was implemented on the base of the `Scope` node instead.

    .. versionadded:: 2.9.3
    """
    fields = ('targets', 'values', 'body')


class Block(Stmt):
    """A node that represents a block."""
    fields = ('name', 'body', 'scoped')


class Include(Stmt):
    """A node that represents the include tag."""
    fields = ('template', 'with_context', 'ignore_missing')


class Import(Stmt):
    """A node that represents the import tag."""
    fields = ('template', 'target', 'with_context')


class FromImport(Stmt):
    """A node that represents the from import tag.  It's important to not
    pass unsafe names to the name attribute.  The compiler translates the
    attribute lookups directly into getattr calls and does *not* use the
    subscript callback of the interface.  As exported variables may not
    start with double underscores (which the parser asserts) this is not a
    problem for regular Jinja code, but if this node is used in an extension
    extra care must be taken.

    The list of names may contain tuples if aliases are wanted.
    """
    fields = ('template', 'names', 'with_context')


class ExprStmt(Stmt):
    """A statement that evaluates an expression and discards the result."""
    fields = ('node',)


class Assign(Stmt):
    """Assigns an expression to a target."""
    fields = ('target', 'node')


class AssignBlock(Stmt):
    """Assigns a block to a target."""
    fields = ('target', 'body')


class Expr(Node):
    """Baseclass for all expressions."""
    abstract = True

    def as_const(self, eval_ctx=None):
        """Return the value of the expression as constant or raise
        :exc:`Impossible` if this was not possible.

        An :class:`EvalContext` can be provided, if none is given
        a default context is created which requires the nodes to have
        an attached environment.

        .. versionchanged:: 2.4
           the `eval_ctx` parameter was added.
        """
        raise Impossible()

    def can_assign(self):
        """Check if it's possible to assign something to this node."""
        return False


class BinExpr(Expr):
    """Baseclass for all binary expressions."""
    fields = ('left', 'right')
    operator = None
    abstract = True

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        # intercepted operators cannot be folded at compile time
        if self.environment.sandboxed and \
                        self.operator in self.environment.intercepted_binops:
            raise Impossible()
        f = _binop_to_func[self.operator]
        try:
            return f(self.left.as_const(eval_ctx), self.right.as_const(eval_ctx))
        except Exception:
            raise Impossible()


class UnaryExpr(Expr):
    """Baseclass for all unary expressions."""
    fields = ('node',)
    operator = None
    abstract = True

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        # intercepted operators cannot be folded at compile time
        if self.environment.sandboxed and \
                        self.operator in self.environment.intercepted_unops:
            raise Impossible()
        f = _uaop_to_func[self.operator]
        try:
            return f(self.node.as_const(eval_ctx))
        except Exception:
            raise Impossible()


class Name(Expr):
    """Looks up a name or stores a value in a name.
    The `ctx` of the node can be one of the following values:

    -   `store`: store a value in the name
    -   `load`: load that name
    -   `param`: like `store` but if the name was defined as function parameter.
    """
    fields = ('name', 'ctx')

    def can_assign(self):
        return self.name not in ('true', 'false', 'none',
                                 'True', 'False', 'None')


class Literal(Expr):
    """Baseclass for literals."""
    abstract = True


class Const(Literal):
    """All constant values.  The parser will return this node for simple
    constants such as ``42`` or ``"foo"`` but it can be used to store more
    complex values such as lists too.  Only constants with a safe
    representation (objects where ``eval(repr(x)) == x`` is true).
    """
    fields = ('value',)

    def as_const(self, eval_ctx=None):
        rv = self.value
        if PY2 and type(rv) is text_type and \
                self.environment.policies['compiler.ascii_str']:
            try:
                rv = rv.encode('ascii')
            except UnicodeError:
                pass
        return rv

    @classmethod
    def from_untrusted(cls, value, lineno=None, environment=None):
        """Return a const object if the value is representable as
        constant value in the generated code, otherwise it will raise
        an `Impossible` exception.
        """
        # from .compiler import has_safe_repr
        if not has_safe_repr(value):
            raise Impossible()
        return cls(value, lineno=lineno, environment=environment)


class TemplateData(Literal):
    """A constant template string."""
    fields = ('data',)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if eval_ctx.volatile:
            raise Impossible()
        if eval_ctx.autoescape:
            return Markup(self.data)
        return self.data


class Tuple(Literal):
    """For loop unpacking and some other things like multiple arguments
    for subscripts.  Like for :class:`Name` `ctx` specifies if the tuple
    is used for loading the names or storing.
    """
    fields = ('items', 'ctx')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return tuple(x.as_const(eval_ctx) for x in self.items)

    def can_assign(self):
        for item in self.items:
            if not item.can_assign():
                return False
        return True


class List(Literal):
    """Any list literal such as ``[1, 2, 3]``"""
    fields = ('items',)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return [x.as_const(eval_ctx) for x in self.items]


class Dict(Literal):
    """Any dict literal such as ``{1: 2, 3: 4}``.  The items must be a list of
    :class:`Pair` nodes.
    """
    fields = ('items',)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return dict(x.as_const(eval_ctx) for x in self.items)


class Pair(Helper):
    """A key, value pair for dicts."""
    fields = ('key', 'value')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.key.as_const(eval_ctx), self.value.as_const(eval_ctx)


class Keyword(Helper):
    """A key, value pair for keyword arguments where key is a string."""
    fields = ('key', 'value')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.key, self.value.as_const(eval_ctx)


class CondExpr(Expr):
    """A conditional expression (inline if expression).  (``{{
    foo if bar else baz }}``)
    """
    fields = ('test', 'expr1', 'expr2')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if self.test.as_const(eval_ctx):
            return self.expr1.as_const(eval_ctx)

        # if we evaluate to an undefined object, we better do that at runtime
        if self.expr2 is None:
            raise Impossible()

        return self.expr2.as_const(eval_ctx)


class Filter(Expr):
    """This node applies a filter on an expression.  `name` is the name of
    the filter, the rest of the fields are the same as for :class:`Call`.

    If the `node` of a filter is `None` the contents of the last buffer are
    filtered.  Buffers are created by macros and filter blocks.
    """
    fields = ('node', 'name', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if eval_ctx.volatile or self.node is None:
            raise Impossible()
        # we have to be careful here because we call filter_ below.
        # if this variable would be called filter, 2to3 would wrap the
        # call in a list beause it is assuming we are talking about the
        # builtin filter function here which no longer returns a list in
        # python 3.  because of that, do not rename filter_ to filter!
        filter_ = self.environment.filters.get(self.name)
        if filter_ is None or getattr(filter_, 'contextfilter', False):
            raise Impossible()

        # We cannot constant handle async filters, so we need to make sure
        # to not go down this path.
        if eval_ctx.environment.is_async and \
                getattr(filter_, 'asyncfiltervariant', False):
            raise Impossible()

        obj = self.node.as_const(eval_ctx)
        args = [obj] + [x.as_const(eval_ctx) for x in self.args]
        if getattr(filter_, 'evalcontextfilter', False):
            args.insert(0, eval_ctx)
        elif getattr(filter_, 'environmentfilter', False):
            args.insert(0, self.environment)
        kwargs = dict(x.as_const(eval_ctx) for x in self.kwargs)
        if self.dyn_args is not None:
            try:
                args.extend(self.dyn_args.as_const(eval_ctx))
            except Exception:
                raise Impossible()
        if self.dyn_kwargs is not None:
            try:
                kwargs.update(self.dyn_kwargs.as_const(eval_ctx))
            except Exception:
                raise Impossible()
        try:
            return filter_(*args, **kwargs)
        except Exception:
            raise Impossible()


class Test(Expr):
    """Applies a test on an expression.  `name` is the name of the test, the
    rest of the fields are the same as for :class:`Call`.
    """
    fields = ('node', 'name', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')


class Call(Expr):
    """Calls an expression.  `args` is a list of arguments, `kwargs` a list
    of keyword arguments (list of :class:`Keyword` nodes), and `dyn_args`
    and `dyn_kwargs` has to be either `None` or a node that is used as
    node for dynamic positional (``*args``) or keyword (``**kwargs``)
    arguments.
    """
    fields = ('node', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')


class Getitem(Expr):
    """Get an attribute or item from an expression and prefer the item."""
    fields = ('node', 'arg', 'ctx')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if self.ctx != 'load':
            raise Impossible()
        try:
            return self.environment.getitem(self.node.as_const(eval_ctx),
                                            self.arg.as_const(eval_ctx))
        except Exception:
            raise Impossible()

    def can_assign(self):
        return False


class Getattr(Expr):
    """Get an attribute or item from an expression that is a ascii-only
    bytestring and prefer the attribute.
    """
    fields = ('node', 'attr', 'ctx')

    def as_const(self, eval_ctx=None):
        if self.ctx != 'load':
            raise Impossible()
        try:
            eval_ctx = get_eval_context(self, eval_ctx)
            return self.environment.getattr(self.node.as_const(eval_ctx),
                                            self.attr)
        except Exception:
            raise Impossible()

    def can_assign(self):
        return False


class Slice(Expr):
    """Represents a slice object.  This must only be used as argument for
    :class:`Subscript`.
    """
    fields = ('start', 'stop', 'step')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        def const(obj):
            if obj is None:
                return None
            return obj.as_const(eval_ctx)
        return slice(const(self.start), const(self.stop), const(self.step))


class Concat(Expr):
    """Concatenates the list of expressions provided after converting them to
    unicode.
    """
    fields = ('nodes',)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return ''.join(text_type(x.as_const(eval_ctx)) for x in self.nodes)


class Compare(Expr):
    """Compares an expression with some other expressions.  `ops` must be a
    list of :class:`Operand`\\s.
    """
    fields = ('expr', 'ops')

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        result = value = self.expr.as_const(eval_ctx)
        try:
            for op in self.ops:
                new_value = op.expr.as_const(eval_ctx)
                result = _cmpop_to_func[op.op](value, new_value)
                value = new_value
        except Exception:
            raise Impossible()
        return result


class Operand(Helper):
    """Holds an operator and an expression."""
    fields = ('op', 'expr')

if __debug__:
    Operand.__doc__ += '\nThe following operators are available: ' + \
                       ', '.join(sorted('``%s``' % x for x in set(_binop_to_func) |
                                        set(_uaop_to_func) | set(_cmpop_to_func)))


class Mul(BinExpr):
    """Multiplies the left with the right node."""
    operator = '*'


class Div(BinExpr):
    """Divides the left by the right node."""
    operator = '/'


class FloorDiv(BinExpr):
    """Divides the left by the right node and truncates conver the
    result into an integer by truncating.
    """
    operator = '//'


class Add(BinExpr):
    """Add the left to the right node."""
    operator = '+'


class Sub(BinExpr):
    """Subtract the right from the left node."""
    operator = '-'


class Mod(BinExpr):
    """Left modulo right."""
    operator = '%'


class Pow(BinExpr):
    """Left to the power of right."""
    operator = '**'


class And(BinExpr):
    """Short circuited AND."""
    operator = 'and'

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.left.as_const(eval_ctx) and self.right.as_const(eval_ctx)


class Or(BinExpr):
    """Short circuited OR."""
    operator = 'or'

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.left.as_const(eval_ctx) or self.right.as_const(eval_ctx)


class Not(UnaryExpr):
    """Negate the expression."""
    operator = 'not'


class Neg(UnaryExpr):
    """Make the expression negative."""
    operator = '-'


class Pos(UnaryExpr):
    """Make the expression positive (noop for most expressions)"""
    operator = '+'


# Helpers for extensions


class EnvironmentAttribute(Expr):
    """Loads an attribute from the environment object.  This is useful for
    extensions that want to call a callback stored on the environment.
    """
    fields = ('name',)


class ExtensionAttribute(Expr):
    """Returns the attribute of an extension bound to the environment.
    The identifier is the identifier of the :class:`Extension`.

    This node is usually constructed by calling the
    :meth:`~jinja2.ext.Extension.attr` method on an extension.
    """
    fields = ('identifier', 'name')


class ImportedName(Expr):
    """If created with an import name the import name is returned on node
    access.  For example ``ImportedName('cgi.escape')`` returns the `escape`
    function from the cgi module on evaluation.  Imports are optimized by the
    compiler so there is no need to assign them to local variables.
    """
    fields = ('importname',)


class InternalName(Expr):
    """An internal name in the compiler.  You cannot create these nodes
    yourself but the parser provides a
    :meth:`~jinja2.parser.Parser.free_identifier` method that creates
    a new identifier for you.  This identifier is not available from the
    template and is not threated specially by the compiler.
    """
    fields = ('name',)

    def __init__(self):
        raise TypeError('Can\'t create internal names.  Use the '
                        '`free_identifier` method on a parser.')


class MarkSafe(Expr):
    """Mark the wrapped expression as safe (wrap it as `Markup`)."""
    fields = ('expr',)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return Markup(self.expr.as_const(eval_ctx))


class MarkSafeIfAutoescape(Expr):
    """Mark the wrapped expression as safe (wrap it as `Markup`) but
    only if autoescaping is active.

    .. versionadded:: 2.5
    """
    fields = ('expr',)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if eval_ctx.volatile:
            raise Impossible()
        expr = self.expr.as_const(eval_ctx)
        if eval_ctx.autoescape:
            return Markup(expr)
        return expr


class ContextReference(Expr):
    """Returns the current template context.  It can be used like a
    :class:`Name` node, with a ``'load'`` ctx and will return the
    current :class:`~jinja2.runtime.Context` object.

    Here an example that assigns the current template name to a
    variable named `foo`::

        Assign(Name('foo', ctx='store'),
               Getattr(ContextReference(), 'name'))
    """


class Continue(Stmt):
    """Continue a loop."""


class Break(Stmt):
    """Break a loop."""


class Scope(Stmt):
    """An artificial scope."""
    fields = ('body',)


class EvalContextModifier(Stmt):
    """Modifies the eval context.  For each option that should be modified,
    a :class:`Keyword` has to be added to the :attr:`options` list.

    Example to change the `autoescape` setting::

        EvalContextModifier(options=[Keyword('autoescape', Const(True))])
    """
    fields = ('options',)


class ScopedEvalContextModifier(EvalContextModifier):
    """Modifies the eval context and reverts it later.  Works exactly like
    :class:`EvalContextModifier` but will only modify the
    :class:`~jinja2.nodes.EvalContext` for nodes in the :attr:`body`.
    """
    fields = ('body',)


# make sure nobody creates custom nodes
def _failing_new(*args, **kwargs):
    raise TypeError('can\'t create custom node types')
NodeType.__new__ = staticmethod(_failing_new); del _failing_new



"""
    jinja2.environment
    ~~~~~~~~~~~~~~~~~~

    Provides a class that holds runtime and parsing time options.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import weakref
from functools import reduce, partial
from jinja2 import nodes
# from jinja2.defaults import BLOCK_START_STRING, \
#     BLOCK_END_STRING, VARIABLE_START_STRING, VARIABLE_END_STRING, \
#     COMMENT_START_STRING, COMMENT_END_STRING, LINE_STATEMENT_PREFIX, \
#     LINE_COMMENT_PREFIX, TRIM_BLOCKS, NEWLINE_SEQUENCE, \
#     DEFAULT_FILTERS, DEFAULT_TESTS, DEFAULT_NAMESPACE, \
#     DEFAULT_POLICIES, KEEP_TRAILING_NEWLINE, LSTRIP_BLOCKS
from jinja2.lexer import get_lexer, TokenStream
from jinja2.parser import Parser
from jinja2.nodes import EvalContext
from jinja2.compiler import generate, CodeGenerator
from jinja2.runtime import Undefined, new_context, Context
from jinja2.exceptions import TemplateSyntaxError, TemplateNotFound, \
    TemplatesNotFound, TemplateRuntimeError
from jinja2.utils import import_string, LRUCache, Markup, missing, \
    concat, consume, internalcode, have_async_gen
from jinja2._compat import imap, ifilter, string_types, iteritems, \
    text_type, reraise, implements_iterator, implements_to_string, \
    encode_filename, PY2, PYPY


# for direct template usage we have up to ten living environments
_spontaneous_environments = LRUCache(10)

# the function to create jinja traceback objects.  This is dynamically
# imported on the first exception in the exception handler.
_make_traceback = None


def get_spontaneous_environment(*args):
    """Return a new spontaneous environment.  A spontaneous environment is an
    unnamed and unaccessible (in theory) environment that is used for
    templates generated from a string and not from the file system.
    """
    try:
        env = _spontaneous_environments.get(args)
    except TypeError:
        return Environment(*args)
    if env is not None:
        return env
    _spontaneous_environments[args] = env = Environment(*args)
    env.shared = True
    return env


def create_cache(size):
    """Return the cache class for the given size."""
    if size == 0:
        return None
    if size < 0:
        return {}
    return LRUCache(size)


def copy_cache(cache):
    """Create an empty copy of the given cache."""
    if cache is None:
        return None
    elif type(cache) is dict:
        return {}
    return LRUCache(cache.capacity)


def load_extensions(environment, extensions):
    """Load the extensions from the list and bind it to the environment.
    Returns a dict of instantiated environments.
    """
    result = {}
    for extension in extensions:
        if isinstance(extension, string_types):
            extension = import_string(extension)
        result[extension.identifier] = extension(environment)
    return result


def fail_for_missing_callable(string, name):
    msg = string % name
    if isinstance(name, Undefined):
        try:
            name._fail_with_undefined_error()
        except Exception as e:
            msg = '%s (%s; did you forget to quote the callable name?)' % (msg, e)
    raise TemplateRuntimeError(msg)


def _environment_sanity_check(environment):
    """Perform a sanity check on the environment."""
    assert issubclass(environment.undefined, Undefined), 'undefined must ' \
                                                         'be a subclass of undefined because filters depend on it.'
    assert environment.block_start_string != \
           environment.variable_start_string != \
           environment.comment_start_string, 'block, variable and comment ' \
                                             'start strings must be different'
    assert environment.newline_sequence in ('\r', '\r\n', '\n'), \
        'newline_sequence set to unknown line ending string.'
    return environment


class Environment(object):
    r"""The core component of Jinja is the `Environment`.  It contains
    important shared variables like configuration, filters, tests,
    globals and others.  Instances of this class may be modified if
    they are not shared and if no template was loaded so far.
    Modifications on environments after the first template was loaded
    will lead to surprising effects and undefined behavior.

    Here are the possible initialization parameters:

        `block_start_string`
            The string marking the beginning of a block.  Defaults to ``'{%'``.

        `block_end_string`
            The string marking the end of a block.  Defaults to ``'%}'``.

        `variable_start_string`
            The string marking the beginning of a print statement.
            Defaults to ``'{{'``.

        `variable_end_string`
            The string marking the end of a print statement.  Defaults to
            ``'}}'``.

        `comment_start_string`
            The string marking the beginning of a comment.  Defaults to ``'{#'``.

        `comment_end_string`
            The string marking the end of a comment.  Defaults to ``'#}'``.

        `line_statement_prefix`
            If given and a string, this will be used as prefix for line based
            statements.  See also :ref:`line-statements`.

        `line_comment_prefix`
            If given and a string, this will be used as prefix for line based
            comments.  See also :ref:`line-statements`.

            .. versionadded:: 2.2

        `trim_blocks`
            If this is set to ``True`` the first newline after a block is
            removed (block, not variable tag!).  Defaults to `False`.

        `lstrip_blocks`
            If this is set to ``True`` leading spaces and tabs are stripped
            from the start of a line to a block.  Defaults to `False`.

        `newline_sequence`
            The sequence that starts a newline.  Must be one of ``'\r'``,
            ``'\n'`` or ``'\r\n'``.  The default is ``'\n'`` which is a
            useful default for Linux and OS X systems as well as web
            applications.

        `keep_trailing_newline`
            Preserve the trailing newline when rendering templates.
            The default is ``False``, which causes a single newline,
            if present, to be stripped from the end of the template.

            .. versionadded:: 2.7

        `extensions`
            List of Jinja extensions to use.  This can either be import paths
            as strings or extension classes.  For more information have a
            look at :ref:`the extensions documentation <jinja-extensions>`.

        `optimized`
            should the optimizer be enabled?  Default is ``True``.

        `undefined`
            :class:`Undefined` or a subclass of it that is used to represent
            undefined values in the template.

        `finalize`
            A callable that can be used to process the result of a variable
            expression before it is output.  For example one can convert
            ``None`` implicitly into an empty string here.

        `autoescape`
            If set to ``True`` the XML/HTML autoescaping feature is enabled by
            default.  For more details about autoescaping see
            :class:`~jinja2.utils.Markup`.  As of Jinja 2.4 this can also
            be a callable that is passed the template name and has to
            return ``True`` or ``False`` depending on autoescape should be
            enabled by default.

            .. versionchanged:: 2.4
               `autoescape` can now be a function

        `loader`
            The template loader for this environment.

        `cache_size`
            The size of the cache.  Per default this is ``400`` which means
            that if more than 400 templates are loaded the loader will clean
            out the least recently used template.  If the cache size is set to
            ``0`` templates are recompiled all the time, if the cache size is
            ``-1`` the cache will not be cleaned.

            .. versionchanged:: 2.8
               The cache size was increased to 400 from a low 50.

        `auto_reload`
            Some loaders load templates from locations where the template
            sources may change (ie: file system or database).  If
            ``auto_reload`` is set to ``True`` (default) every time a template is
            requested the loader checks if the source changed and if yes, it
            will reload the template.  For higher performance it's possible to
            disable that.

        `bytecode_cache`
            If set to a bytecode cache object, this object will provide a
            cache for the internal Jinja bytecode so that templates don't
            have to be parsed if they were not changed.

            See :ref:`bytecode-cache` for more information.

        `enable_async`
            If set to true this enables async template execution which allows
            you to take advantage of newer Python features.  This requires
            Python 3.6 or later.
    """

    #: if this environment is sandboxed.  Modifying this variable won't make
    #: the environment sandboxed though.  For a real sandboxed environment
    #: have a look at jinja2.sandbox.  This flag alone controls the code
    #: generation by the compiler.
    sandboxed = False

    #: True if the environment is just an overlay
    overlayed = False

    #: the environment this environment is linked to if it is an overlay
    linked_to = None

    #: shared environments have this set to `True`.  A shared environment
    #: must not be modified
    shared = False

    #: these are currently EXPERIMENTAL undocumented features.
    exception_handler = None
    exception_formatter = None

    #: the class that is used for code generation.  See
    #: :class:`~jinja2.compiler.CodeGenerator` for more information.
    code_generator_class = CodeGenerator

    #: the context class thatis used for templates.  See
    #: :class:`~jinja2.runtime.Context` for more information.
    context_class = Context

    def __init__(self,
                 block_start_string=BLOCK_START_STRING,
                 block_end_string=BLOCK_END_STRING,
                 variable_start_string=VARIABLE_START_STRING,
                 variable_end_string=VARIABLE_END_STRING,
                 comment_start_string=COMMENT_START_STRING,
                 comment_end_string=COMMENT_END_STRING,
                 line_statement_prefix=LINE_STATEMENT_PREFIX,
                 line_comment_prefix=LINE_COMMENT_PREFIX,
                 trim_blocks=TRIM_BLOCKS,
                 lstrip_blocks=LSTRIP_BLOCKS,
                 newline_sequence=NEWLINE_SEQUENCE,
                 keep_trailing_newline=KEEP_TRAILING_NEWLINE,
                 extensions=(),
                 optimized=True,
                 undefined=Undefined,
                 finalize=None,
                 autoescape=False,
                 loader=None,
                 cache_size=400,
                 auto_reload=True,
                 bytecode_cache=None,
                 enable_async=False):
        # !!Important notice!!
        #   The constructor accepts quite a few arguments that should be
        #   passed by keyword rather than position.  However it's important to
        #   not change the order of arguments because it's used at least
        #   internally in those cases:
        #       -   spontaneous environments (i18n extension and Template)
        #       -   unittests
        #   If parameter changes are required only add parameters at the end
        #   and don't change the arguments (or the defaults!) of the arguments
        #   existing already.

        # lexer / parser information
        self.block_start_string = block_start_string
        self.block_end_string = block_end_string
        self.variable_start_string = variable_start_string
        self.variable_end_string = variable_end_string
        self.comment_start_string = comment_start_string
        self.comment_end_string = comment_end_string
        self.line_statement_prefix = line_statement_prefix
        self.line_comment_prefix = line_comment_prefix
        self.trim_blocks = trim_blocks
        self.lstrip_blocks = lstrip_blocks
        self.newline_sequence = newline_sequence
        self.keep_trailing_newline = keep_trailing_newline

        # runtime information
        self.undefined = undefined
        self.optimized = optimized
        self.finalize = finalize
        self.autoescape = autoescape

        # defaults
        self.filters = DEFAULT_FILTERS.copy()
        self.tests = DEFAULT_TESTS.copy()
        self.globals = DEFAULT_NAMESPACE.copy()

        # set the loader provided
        self.loader = loader
        self.cache = create_cache(cache_size)
        self.bytecode_cache = bytecode_cache
        self.auto_reload = auto_reload

        # configurable policies
        self.policies = DEFAULT_POLICIES.copy()

        # load extensions
        self.extensions = load_extensions(self, extensions)

        self.enable_async = enable_async
        self.is_async = self.enable_async and have_async_gen

        _environment_sanity_check(self)

    def add_extension(self, extension):
        """Adds an extension after the environment was created.

        .. versionadded:: 2.5
        """
        self.extensions.update(load_extensions(self, [extension]))

    def extend(self, **attributes):
        """Add the items to the instance of the environment if they do not exist
        yet.  This is used by :ref:`extensions <writing-extensions>` to register
        callbacks and configuration values without breaking inheritance.
        """
        for key, value in iteritems(attributes):
            if not hasattr(self, key):
                setattr(self, key, value)

    def overlay(self, block_start_string=missing, block_end_string=missing,
                variable_start_string=missing, variable_end_string=missing,
                comment_start_string=missing, comment_end_string=missing,
                line_statement_prefix=missing, line_comment_prefix=missing,
                trim_blocks=missing, lstrip_blocks=missing,
                extensions=missing, optimized=missing,
                undefined=missing, finalize=missing, autoescape=missing,
                loader=missing, cache_size=missing, auto_reload=missing,
                bytecode_cache=missing):
        """Create a new overlay environment that shares all the data with the
        current environment except for cache and the overridden attributes.
        Extensions cannot be removed for an overlayed environment.  An overlayed
        environment automatically gets all the extensions of the environment it
        is linked to plus optional extra extensions.

        Creating overlays should happen after the initial environment was set
        up completely.  Not all attributes are truly linked, some are just
        copied over so modifications on the original environment may not shine
        through.
        """
        args = dict(locals())
        del args['self'], args['cache_size'], args['extensions']

        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.overlayed = True
        rv.linked_to = self

        for key, value in iteritems(args):
            if value is not missing:
                setattr(rv, key, value)

        if cache_size is not missing:
            rv.cache = create_cache(cache_size)
        else:
            rv.cache = copy_cache(self.cache)

        rv.extensions = {}
        for key, value in iteritems(self.extensions):
            rv.extensions[key] = value.bind(rv)
        if extensions is not missing:
            rv.extensions.update(load_extensions(rv, extensions))

        return _environment_sanity_check(rv)

    lexer = property(get_lexer, doc="The lexer for this environment.")

    def iter_extensions(self):
        """Iterates over the extensions by priority."""
        return iter(sorted(self.extensions.values(),
                           key=lambda x: x.priority))

    def getitem(self, obj, argument):
        """Get an item or attribute of an object but prefer the item."""
        try:
            return obj[argument]
        except (AttributeError, TypeError, LookupError):
            if isinstance(argument, string_types):
                try:
                    attr = str(argument)
                except Exception:
                    pass
                else:
                    try:
                        return getattr(obj, attr)
                    except AttributeError:
                        pass
            return self.undefined(obj=obj, name=argument)

    def getattr(self, obj, attribute):
        """Get an item or attribute of an object but prefer the attribute.
        Unlike :meth:`getitem` the attribute *must* be a bytestring.
        """
        try:
            return getattr(obj, attribute)
        except AttributeError:
            pass
        try:
            return obj[attribute]
        except (TypeError, LookupError, AttributeError):
            return self.undefined(obj=obj, name=attribute)

    def call_filter(self, name, value, args=None, kwargs=None,
                    context=None, eval_ctx=None):
        """Invokes a filter on a value the same way the compiler does it.

        Note that on Python 3 this might return a coroutine in case the
        filter is running from an environment in async mode and the filter
        supports async execution.  It's your responsibility to await this
        if needed.

        .. versionadded:: 2.7
        """
        func = self.filters.get(name)
        if func is None:
            fail_for_missing_callable('no filter named %r', name)
        args = [value] + list(args or ())
        if getattr(func, 'contextfilter', False):
            if context is None:
                raise TemplateRuntimeError('Attempted to invoke context '
                                           'filter without context')
            args.insert(0, context)
        elif getattr(func, 'evalcontextfilter', False):
            if eval_ctx is None:
                if context is not None:
                    eval_ctx = context.eval_ctx
                else:
                    eval_ctx = EvalContext(self)
            args.insert(0, eval_ctx)
        elif getattr(func, 'environmentfilter', False):
            args.insert(0, self)
        return func(*args, **(kwargs or {}))

    def call_test(self, name, value, args=None, kwargs=None):
        """Invokes a test on a value the same way the compiler does it.

        .. versionadded:: 2.7
        """
        func = self.tests.get(name)
        if func is None:
            fail_for_missing_callable('no test named %r', name)
        return func(value, *(args or ()), **(kwargs or {}))

    @internalcode
    def parse(self, source, name=None, filename=None):
        """Parse the sourcecode and return the abstract syntax tree.  This
        tree of nodes is used by the compiler to convert the template into
        executable source- or bytecode.  This is useful for debugging or to
        extract information from templates.

        If you are :ref:`developing Jinja2 extensions <writing-extensions>`
        this gives you a good overview of the node tree generated.
        """
        try:
            return self._parse(source, name, filename)
        except TemplateSyntaxError:
            exc_info = sys.exc_info()
        self.handle_exception(exc_info, source_hint=source)

    def _parse(self, source, name, filename):
        """Internal parsing function used by `parse` and `compile`."""
        return Parser(self, source, name, encode_filename(filename)).parse()

    def lex(self, source, name=None, filename=None):
        """Lex the given sourcecode and return a generator that yields
        tokens as tuples in the form ``(lineno, token_type, value)``.
        This can be useful for :ref:`extension development <writing-extensions>`
        and debugging templates.

        This does not perform preprocessing.  If you want the preprocessing
        of the extensions to be applied you have to filter source through
        the :meth:`preprocess` method.
        """
        source = text_type(source)
        try:
            return self.lexer.tokeniter(source, name, filename)
        except TemplateSyntaxError:
            exc_info = sys.exc_info()
        self.handle_exception(exc_info, source_hint=source)

    def preprocess(self, source, name=None, filename=None):
        """Preprocesses the source with all extensions.  This is automatically
        called for all parsing and compiling methods but *not* for :meth:`lex`
        because there you usually only want the actual source tokenized.
        """
        return reduce(lambda s, e: e.preprocess(s, name, filename),
                      self.iter_extensions(), text_type(source))

    def _tokenize(self, source, name, filename=None, state=None):
        """Called by the parser to do the preprocessing and filtering
        for all the extensions.  Returns a :class:`~jinja2.lexer.TokenStream`.
        """
        source = self.preprocess(source, name, filename)
        stream = self.lexer.tokenize(source, name, filename, state)
        for ext in self.iter_extensions():
            stream = ext.filter_stream(stream)
            if not isinstance(stream, TokenStream):
                stream = TokenStream(stream, name, filename)
        return stream

    def _generate(self, source, name, filename, defer_init=False):
        """Internal hook that can be overridden to hook a different generate
        method in.

        .. versionadded:: 2.5
        """
        return generate(source, self, name, filename, defer_init=defer_init,
                        optimized=self.optimized)

    def _compile(self, source, filename):
        """Internal hook that can be overridden to hook a different compile
        method in.

        .. versionadded:: 2.5
        """
        return compile(source, filename, 'exec')

    @internalcode
    def compile(self, source, name=None, filename=None, raw=False,
                defer_init=False):
        """Compile a node or template source code.  The `name` parameter is
        the load name of the template after it was joined using
        :meth:`join_path` if necessary, not the filename on the file system.
        the `filename` parameter is the estimated filename of the template on
        the file system.  If the template came from a database or memory this
        can be omitted.

        The return value of this method is a python code object.  If the `raw`
        parameter is `True` the return value will be a string with python
        code equivalent to the bytecode returned otherwise.  This method is
        mainly used internally.

        `defer_init` is use internally to aid the module code generator.  This
        causes the generated code to be able to import without the global
        environment variable to be set.

        .. versionadded:: 2.4
           `defer_init` parameter added.
        """
        source_hint = None
        try:
            if isinstance(source, string_types):
                source_hint = source
                source = self._parse(source, name, filename)
            source = self._generate(source, name, filename,
                                    defer_init=defer_init)
            if raw:
                return source
            if filename is None:
                filename = '<template>'
            else:
                filename = encode_filename(filename)
            return self._compile(source, filename)
        except TemplateSyntaxError:
            exc_info = sys.exc_info()
        self.handle_exception(exc_info, source_hint=source_hint)

    def compile_expression(self, source, undefined_to_none=True):
        """A handy helper method that returns a callable that accepts keyword
        arguments that appear as variables in the expression.  If called it
        returns the result of the expression.

        This is useful if applications want to use the same rules as Jinja
        in template "configuration files" or similar situations.

        Example usage:

        >>> env = Environment()
        >>> expr = env.compile_expression('foo == 42')
        >>> expr(foo=23)
        False
        >>> expr(foo=42)
        True

        Per default the return value is converted to `None` if the
        expression returns an undefined value.  This can be changed
        by setting `undefined_to_none` to `False`.

        >>> env.compile_expression('var')() is None
        True
        >>> env.compile_expression('var', undefined_to_none=False)()
        Undefined

        .. versionadded:: 2.1
        """
        parser = Parser(self, source, state='variable')
        exc_info = None
        try:
            expr = parser.parse_expression()
            if not parser.stream.eos:
                raise TemplateSyntaxError('chunk after expression',
                                          parser.stream.current.lineno,
                                          None, None)
            expr.set_environment(self)
        except TemplateSyntaxError:
            exc_info = sys.exc_info()
        if exc_info is not None:
            self.handle_exception(exc_info, source_hint=source)
        body = [nodes.Assign(nodes.Name('result', 'store'), expr, lineno=1)]
        template = self.from_string(nodes.Template(body, lineno=1))
        return TemplateExpression(template, undefined_to_none)

    def compile_templates(self, target, extensions=None, filter_func=None,
                          zip='deflated', log_function=None,
                          ignore_errors=True, py_compile=False):
        """Finds all the templates the loader can find, compiles them
        and stores them in `target`.  If `zip` is `None`, instead of in a
        zipfile, the templates will be stored in a directory.
        By default a deflate zip algorithm is used. To switch to
        the stored algorithm, `zip` can be set to ``'stored'``.

        `extensions` and `filter_func` are passed to :meth:`list_templates`.
        Each template returned will be compiled to the target folder or
        zipfile.

        By default template compilation errors are ignored.  In case a
        log function is provided, errors are logged.  If you want template
        syntax errors to abort the compilation you can set `ignore_errors`
        to `False` and you will get an exception on syntax errors.

        If `py_compile` is set to `True` .pyc files will be written to the
        target instead of standard .py files.  This flag does not do anything
        on pypy and Python 3 where pyc files are not picked up by itself and
        don't give much benefit.

        .. versionadded:: 2.4
        """
        from jinja2.loaders import ModuleLoader

        if log_function is None:
            log_function = lambda x: None

        if py_compile:
            if not PY2 or PYPY:
                from warnings import warn
                warn(Warning('py_compile has no effect on pypy or Python 3'))
                py_compile = False
            else:
                import imp
                import marshal
                py_header = imp.get_magic() + \
                            u'\xff\xff\xff\xff'.encode('iso-8859-15')

                # Python 3.3 added a source filesize to the header
                if sys.version_info >= (3, 3):
                    py_header += u'\x00\x00\x00\x00'.encode('iso-8859-15')

        def write_file(filename, data, mode):
            if zip:
                info = ZipInfo(filename)
                info.external_attr = 0o755 << 16
                zip_file.writestr(info, data)
            else:
                f = open(os.path.join(target, filename), mode)
                try:
                    f.write(data)
                finally:
                    f.close()

        if zip is not None:
            from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED
            zip_file = ZipFile(target, 'w', dict(deflated=ZIP_DEFLATED,
                                                 stored=ZIP_STORED)[zip])
            log_function('Compiling into Zip archive "%s"' % target)
        else:
            if not os.path.isdir(target):
                os.makedirs(target)
            log_function('Compiling into folder "%s"' % target)

        try:
            for name in self.list_templates(extensions, filter_func):
                source, filename, _ = self.loader.get_source(self, name)
                try:
                    code = self.compile(source, name, filename, True, True)
                except TemplateSyntaxError as e:
                    if not ignore_errors:
                        raise
                    log_function('Could not compile "%s": %s' % (name, e))
                    continue

                filename = ModuleLoader.get_module_filename(name)

                if py_compile:
                    c = self._compile(code, encode_filename(filename))
                    write_file(filename + 'c', py_header +
                               marshal.dumps(c), 'wb')
                    log_function('Byte-compiled "%s" as %s' %
                                 (name, filename + 'c'))
                else:
                    write_file(filename, code, 'w')
                    log_function('Compiled "%s" as %s' % (name, filename))
        finally:
            if zip:
                zip_file.close()

        log_function('Finished compiling templates')

    def list_templates(self, extensions=None, filter_func=None):
        """Returns a list of templates for this environment.  This requires
        that the loader supports the loader's
        :meth:`~BaseLoader.list_templates` method.

        If there are other files in the template folder besides the
        actual templates, the returned list can be filtered.  There are two
        ways: either `extensions` is set to a list of file extensions for
        templates, or a `filter_func` can be provided which is a callable that
        is passed a template name and should return `True` if it should end up
        in the result list.

        If the loader does not support that, a :exc:`TypeError` is raised.

        .. versionadded:: 2.4
        """
        x = self.loader.list_templates()
        if extensions is not None:
            if filter_func is not None:
                raise TypeError('either extensions or filter_func '
                                'can be passed, but not both')
            filter_func = lambda x: '.' in x and \
                                    x.rsplit('.', 1)[1] in extensions
        if filter_func is not None:
            x = list(ifilter(filter_func, x))
        return x

    def handle_exception(self, exc_info=None, rendered=False, source_hint=None):
        """Exception handling helper.  This is used internally to either raise
        rewritten exceptions or return a rendered traceback for the template.
        """
        global _make_traceback
        if exc_info is None:
            exc_info = sys.exc_info()

        # the debugging module is imported when it's used for the first time.
        # we're doing a lot of stuff there and for applications that do not
        # get any exceptions in template rendering there is no need to load
        # all of that.
        if _make_traceback is None:
            from jinja2.debug import make_traceback as _make_traceback
        traceback = _make_traceback(exc_info, source_hint)
        if rendered and self.exception_formatter is not None:
            return self.exception_formatter(traceback)
        if self.exception_handler is not None:
            self.exception_handler(traceback)
        exc_type, exc_value, tb = traceback.standard_exc_info
        reraise(exc_type, exc_value, tb)

    def join_path(self, template, parent):
        """Join a template with the parent.  By default all the lookups are
        relative to the loader root so this method returns the `template`
        parameter unchanged, but if the paths should be relative to the
        parent template, this function can be used to calculate the real
        template name.

        Subclasses may override this method and implement template path
        joining here.
        """
        return template

    @internalcode
    def _load_template(self, name, globals):
        if self.loader is None:
            raise TypeError('no loader for this environment specified')
        cache_key = (weakref.ref(self.loader), name)
        if self.cache is not None:
            template = self.cache.get(cache_key)
            if template is not None and (not self.auto_reload or
                                             template.is_up_to_date):
                return template
        template = self.loader.load(self, name, globals)
        if self.cache is not None:
            self.cache[cache_key] = template
        return template

    @internalcode
    def get_template(self, name, parent=None, globals=None):
        """Load a template from the loader.  If a loader is configured this
        method ask the loader for the template and returns a :class:`Template`.
        If the `parent` parameter is not `None`, :meth:`join_path` is called
        to get the real template name before loading.

        The `globals` parameter can be used to provide template wide globals.
        These variables are available in the context at render time.

        If the template does not exist a :exc:`TemplateNotFound` exception is
        raised.

        .. versionchanged:: 2.4
           If `name` is a :class:`Template` object it is returned from the
           function unchanged.
        """
        if isinstance(name, Template):
            return name
        if parent is not None:
            name = self.join_path(name, parent)
        return self._load_template(name, self.make_globals(globals))

    @internalcode
    def select_template(self, names, parent=None, globals=None):
        """Works like :meth:`get_template` but tries a number of templates
        before it fails.  If it cannot find any of the templates, it will
        raise a :exc:`TemplatesNotFound` exception.

        .. versionadded:: 2.3

        .. versionchanged:: 2.4
           If `names` contains a :class:`Template` object it is returned
           from the function unchanged.
        """
        if not names:
            raise TemplatesNotFound(message=u'Tried to select from an empty list '
                                            u'of templates.')
        globals = self.make_globals(globals)
        for name in names:
            if isinstance(name, Template):
                return name
            if parent is not None:
                name = self.join_path(name, parent)
            try:
                return self._load_template(name, globals)
            except TemplateNotFound:
                pass
        raise TemplatesNotFound(names)

    @internalcode
    def get_or_select_template(self, template_name_or_list,
                               parent=None, globals=None):
        """Does a typecheck and dispatches to :meth:`select_template`
        if an iterable of template names is given, otherwise to
        :meth:`get_template`.

        .. versionadded:: 2.3
        """
        if isinstance(template_name_or_list, string_types):
            return self.get_template(template_name_or_list, parent, globals)
        elif isinstance(template_name_or_list, Template):
            return template_name_or_list
        return self.select_template(template_name_or_list, parent, globals)

    def from_string(self, source, globals=None, template_class=None):
        """Load a template from a string.  This parses the source given and
        returns a :class:`Template` object.
        """
        globals = self.make_globals(globals)
        cls = template_class or self.template_class
        return cls.from_code(self, self.compile(source), globals, None)

    def make_globals(self, d):
        """Return a dict for the globals."""
        if not d:
            return self.globals
        return dict(self.globals, **d)


class Template(object):
    """The central template object.  This class represents a compiled template
    and is used to evaluate it.

    Normally the template object is generated from an :class:`Environment` but
    it also has a constructor that makes it possible to create a template
    instance directly using the constructor.  It takes the same arguments as
    the environment constructor but it's not possible to specify a loader.

    Every template object has a few methods and members that are guaranteed
    to exist.  However it's important that a template object should be
    considered immutable.  Modifications on the object are not supported.

    Template objects created from the constructor rather than an environment
    do have an `environment` attribute that points to a temporary environment
    that is probably shared with other templates created with the constructor
    and compatible settings.

    >>> template = Template('Hello {{ name }}!')
    >>> template.render(name='John Doe') == u'Hello John Doe!'
    True
    >>> stream = template.stream(name='John Doe')
    >>> next(stream) == u'Hello John Doe!'
    True
    >>> next(stream)
    Traceback (most recent call last):
        ...
    StopIteration
    """

    def __new__(cls, source,
                block_start_string=BLOCK_START_STRING,
                block_end_string=BLOCK_END_STRING,
                variable_start_string=VARIABLE_START_STRING,
                variable_end_string=VARIABLE_END_STRING,
                comment_start_string=COMMENT_START_STRING,
                comment_end_string=COMMENT_END_STRING,
                line_statement_prefix=LINE_STATEMENT_PREFIX,
                line_comment_prefix=LINE_COMMENT_PREFIX,
                trim_blocks=TRIM_BLOCKS,
                lstrip_blocks=LSTRIP_BLOCKS,
                newline_sequence=NEWLINE_SEQUENCE,
                keep_trailing_newline=KEEP_TRAILING_NEWLINE,
                extensions=(),
                optimized=True,
                undefined=Undefined,
                finalize=None,
                autoescape=False,
                enable_async=False):
        env = get_spontaneous_environment(
            block_start_string, block_end_string, variable_start_string,
            variable_end_string, comment_start_string, comment_end_string,
            line_statement_prefix, line_comment_prefix, trim_blocks,
            lstrip_blocks, newline_sequence, keep_trailing_newline,
            frozenset(extensions), optimized, undefined, finalize, autoescape,
            None, 0, False, None, enable_async)
        return env.from_string(source, template_class=cls)

    @classmethod
    def from_code(cls, environment, code, globals, uptodate=None):
        """Creates a template object from compiled code and the globals.  This
        is used by the loaders and environment to create a template object.
        """
        namespace = {
            'environment':  environment,
            '__file__':     code.co_filename
        }
        exec(code, namespace)
        rv = cls._from_namespace(environment, namespace, globals)
        rv._uptodate = uptodate
        return rv

    @classmethod
    def from_module_dict(cls, environment, module_dict, globals):
        """Creates a template object from a module.  This is used by the
        module loader to create a template object.

        .. versionadded:: 2.4
        """
        return cls._from_namespace(environment, module_dict, globals)

    @classmethod
    def _from_namespace(cls, environment, namespace, globals):
        t = object.__new__(cls)
        t.environment = environment
        t.globals = globals
        t.name = namespace['name']
        t.filename = namespace['__file__']
        t.blocks = namespace['blocks']

        # render function and module
        t.root_render_func = namespace['root']
        t._module = None

        # debug and loader helpers
        t._debug_info = namespace['debug_info']
        t._uptodate = None

        # store the reference
        namespace['environment'] = environment
        namespace['__jinja_template__'] = t

        return t

    def render(self, *args, **kwargs):
        """This method accepts the same arguments as the `dict` constructor:
        A dict, a dict subclass or some keyword arguments.  If no arguments
        are given the context will be empty.  These two calls do the same::

            template.render(knights='that say nih')
            template.render({'knights': 'that say nih'})

        This will return the rendered template as unicode string.
        """
        vars = dict(*args, **kwargs)
        try:
            return concat(self.root_render_func(self.new_context(vars)))
        except Exception:
            exc_info = sys.exc_info()
        return self.environment.handle_exception(exc_info, True)

    def render_async(self, *args, **kwargs):
        """This works similar to :meth:`render` but returns a coroutine
        that when awaited returns the entire rendered template string.  This
        requires the async feature to be enabled.

        Example usage::

            await template.render_async(knights='that say nih; asynchronously')
        """
        # see asyncsupport for the actual implementation
        raise NotImplementedError('This feature is not available for this '
                                  'version of Python')

    def stream(self, *args, **kwargs):
        """Works exactly like :meth:`generate` but returns a
        :class:`TemplateStream`.
        """
        return TemplateStream(self.generate(*args, **kwargs))

    def generate(self, *args, **kwargs):
        """For very large templates it can be useful to not render the whole
        template at once but evaluate each statement after another and yield
        piece for piece.  This method basically does exactly that and returns
        a generator that yields one item after another as unicode strings.

        It accepts the same arguments as :meth:`render`.
        """
        vars = dict(*args, **kwargs)
        try:
            for event in self.root_render_func(self.new_context(vars)):
                yield event
        except Exception:
            exc_info = sys.exc_info()
        else:
            return
        yield self.environment.handle_exception(exc_info, True)

    def generate_async(self, *args, **kwargs):
        """An async version of :meth:`generate`.  Works very similarly but
        returns an async iterator instead.
        """
        # see asyncsupport for the actual implementation
        raise NotImplementedError('This feature is not available for this '
                                  'version of Python')

    def new_context(self, vars=None, shared=False, locals=None):
        """Create a new :class:`Context` for this template.  The vars
        provided will be passed to the template.  Per default the globals
        are added to the context.  If shared is set to `True` the data
        is passed as it to the context without adding the globals.

        `locals` can be a dict of local variables for internal usage.
        """
        return new_context(self.environment, self.name, self.blocks,
                           vars, shared, self.globals, locals)

    def make_module(self, vars=None, shared=False, locals=None):
        """This method works like the :attr:`module` attribute when called
        without arguments but it will evaluate the template on every call
        rather than caching it.  It's also possible to provide
        a dict which is then used as context.  The arguments are the same
        as for the :meth:`new_context` method.
        """
        return TemplateModule(self, self.new_context(vars, shared, locals))

    def make_module_async(self, vars=None, shared=False, locals=None):
        """As template module creation can invoke template code for
        asynchronous exections this method must be used instead of the
        normal :meth:`make_module` one.  Likewise the module attribute
        becomes unavailable in async mode.
        """
        # see asyncsupport for the actual implementation
        raise NotImplementedError('This feature is not available for this '
                                  'version of Python')

    @internalcode
    def _get_default_module(self):
        if self._module is not None:
            return self._module
        self._module = rv = self.make_module()
        return rv

    @property
    def module(self):
        """The template as module.  This is used for imports in the
        template runtime but is also useful if one wants to access
        exported template variables from the Python layer:

        >>> t = Template('{% macro foo() %}42{% endmacro %}23')
        >>> str(t.module)
        '23'
        >>> t.module.foo() == u'42'
        True

        This attribute is not available if async mode is enabled.
        """
        return self._get_default_module()

    def get_corresponding_lineno(self, lineno):
        """Return the source line number of a line number in the
        generated bytecode as they are not in sync.
        """
        for template_line, code_line in reversed(self.debug_info):
            if code_line <= lineno:
                return template_line
        return 1

    @property
    def is_up_to_date(self):
        """If this variable is `False` there is a newer version available."""
        if self._uptodate is None:
            return True
        return self._uptodate()

    @property
    def debug_info(self):
        """The debug info mapping."""
        return [tuple(imap(int, x.split('='))) for x in
                self._debug_info.split('&')]

    def __repr__(self):
        if self.name is None:
            name = 'memory:%x' % id(self)
        else:
            name = repr(self.name)
        return '<%s %s>' % (self.__class__.__name__, name)


@implements_to_string
class TemplateModule(object):
    """Represents an imported template.  All the exported names of the
    template are available as attributes on this object.  Additionally
    converting it into an unicode- or bytestrings renders the contents.
    """

    def __init__(self, template, context, body_stream=None):
        if body_stream is None:
            if context.environment.is_async:
                raise RuntimeError('Async mode requires a body stream '
                                   'to be passed to a template module.  Use '
                                   'the async methods of the API you are '
                                   'using.')
            body_stream = list(template.root_render_func(context))
        self._body_stream = body_stream
        self.__dict__.update(context.get_exported())
        self.__name__ = template.name

    def __html__(self):
        return Markup(concat(self._body_stream))

    def __str__(self):
        return concat(self._body_stream)

    def __repr__(self):
        if self.__name__ is None:
            name = 'memory:%x' % id(self)
        else:
            name = repr(self.__name__)
        return '<%s %s>' % (self.__class__.__name__, name)


class TemplateExpression(object):
    """The :meth:`jinja2.Environment.compile_expression` method returns an
    instance of this object.  It encapsulates the expression-like access
    to the template with an expression it wraps.
    """

    def __init__(self, template, undefined_to_none):
        self._template = template
        self._undefined_to_none = undefined_to_none

    def __call__(self, *args, **kwargs):
        context = self._template.new_context(dict(*args, **kwargs))
        consume(self._template.root_render_func(context))
        rv = context.vars['result']
        if self._undefined_to_none and isinstance(rv, Undefined):
            rv = None
        return rv


@implements_iterator
class TemplateStream(object):
    """A template stream works pretty much like an ordinary python generator
    but it can buffer multiple items to reduce the number of total iterations.
    Per default the output is unbuffered which means that for every unbuffered
    instruction in the template one unicode string is yielded.

    If buffering is enabled with a buffer size of 5, five items are combined
    into a new unicode string.  This is mainly useful if you are streaming
    big templates to a client via WSGI which flushes after each iteration.
    """

    def __init__(self, gen):
        self._gen = gen
        self.disable_buffering()

    def dump(self, fp, encoding=None, errors='strict'):
        """Dump the complete stream into a file or file-like object.
        Per default unicode strings are written, if you want to encode
        before writing specify an `encoding`.

        Example usage::

            Template('Hello {{ name }}!').stream(name='foo').dump('hello.html')
        """
        close = False
        if isinstance(fp, string_types):
            if encoding is None:
                encoding = 'utf-8'
            fp = open(fp, 'wb')
            close = True
        try:
            if encoding is not None:
                iterable = (x.encode(encoding, errors) for x in self)
            else:
                iterable = self
            if hasattr(fp, 'writelines'):
                fp.writelines(iterable)
            else:
                for item in iterable:
                    fp.write(item)
        finally:
            if close:
                fp.close()

    def disable_buffering(self):
        """Disable the output buffering."""
        self._next = partial(next, self._gen)
        self.buffered = False

    def _buffered_generator(self, size):
        buf = []
        c_size = 0
        push = buf.append

        while 1:
            try:
                while c_size < size:
                    c = next(self._gen)
                    push(c)
                    if c:
                        c_size += 1
            except StopIteration:
                if not c_size:
                    return
            yield concat(buf)
            del buf[:]
            c_size = 0

    def enable_buffering(self, size=5):
        """Enable buffering.  Buffer `size` items before yielding them."""
        if size <= 1:
            raise ValueError('buffer size too small')

        self.buffered = True
        self._next = partial(next, self._buffered_generator(size))

    def __iter__(self):
        return self

    def __next__(self):
        return self._next()


# hook in default template class.  if anyone reads this comment: ignore that
# it's possible to use custom templates ;-)
Environment.template_class = Template