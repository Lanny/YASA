import re

class ParseError(Exception):
    pass

class EOLException(Exception):
    pass

class ParsedKeyError(KeyError):
    pass

class ParsedDict(dict):
    """
    Special dict type. The only difference is that it raises ParsedKeyErrors
    rather than regular KeyError which will allow us to catch a special class
    of exceptions comming from insufficient data being transmitted.
    """
    def __getitem__(self, key):
        try:
            return super(ParsedDict, self).__getitem__(key)
        except KeyError, e:
            excpt = ParsedKeyError(e.message)
            excpt.missing_key = key

            raise excpt

# Parser states
IN_KEY = 0
IN_VALUE = 1
OUTSIDE = 2

class _Parser(object):
    def __init__(self, string):
        self._parsed = ParsedDict()
        self._idx = 0
        self._mark = self._idx
        self._string = string
        self._mode = OUTSIDE
        self._key = None
        self._value = None

    def _flip(self):
        """
        Clears the buffer (_string), returns the parsed object, and resets
        the parser to accept the next line.
        """
        ret = self._parsed

        self._parsed = ParsedDict()
        self._string = self._string[self._idx:]
        self._idx = 0
        self._mark = self._idx
        self._key = None
        self._value = None
        self._mode = OUTSIDE

        return ret

    def _partial_parse(self):
        """
        Parses the remainder of the string, may leave parsing partially
        complete.
        """
        slen = len(self._string)
        while self._idx < slen:
            c = self._string[self._idx]

            if self._mode == OUTSIDE:
                if c == '(':
                    self._mode = IN_KEY
                    self._mark = self._idx+1

                elif c == '\n':
                    self._idx += 1
                    raise EOLException('End of line reached.')

            elif self._mode == IN_KEY:
                cp = ord(c)
                if c == ' ':
                    self._key = self._string[self._mark:self._idx]
                    self._mode = IN_VALUE
                    self._mark = self._idx+1

                elif cp < 33 or cp > 126 or cp == 40 or cp == 41:
                    raise ParseError('Invalid code point %d in key at idx %d' %
                                     (cp, self._idx))

            elif self._mode == IN_VALUE and c == ')' and \
                    self._string[self._idx-1] != '\\':
                self._value = unescape(self._string[self._mark:self._idx])
                self._parsed[self._key.upper()] = self._value
                self._mode = OUTSIDE

            self._idx += 1

    def parse(self):
        """
        Parses the remainder of the string, assumes the string represents a
        complete map.
        """
        self._partial_parse()

        if self._mode != OUTSIDE:
            raise ParseError('Unmatched parentheses at index %d' % 
                             (self._mark-1,))

    def line_generator(self, socket, catch_parse_errors=True):
        """
        Takes a socket (or anything that implements the `recv` method) and
        returns a generator which will parse and return data comming over
        the socket by line, as the lines come in. If `catch_parse_errors` is
        set, will yeild parse errors instead of throwing them.
        """
        data = socket.recv(1024).decode('utf-8')

        while data:
            self._string += data

            try:
                self._partial_parse()
            except EOLException, e:
                yield self._flip()
            except ParseError, e:
                if catch_parse_errors:
                    self._idx = len(self._string)
                    self._flip() # Clear parser state
                    yield e
                else:
                    raise e

            data = socket.recv(1024).decode('utf-8')


def unescape(string):
    """
    Takes a string and unescapes it per the spec
    """
    return (string.replace('\\\\', '<PSEUDOBSLASH>')
                  .replace('\\)', ')')
                  .replace('<PSEUDOBSLASH>', '\\'))

def escape(string):
    """
    Takes a string and escapes it per the spec
    """
    return (string.replace('\\', '\\\\')
                  .replace(')', '\\)'))

def dumps(value):
    """
    Recursively transforms a python dictionary into a YASA style map.
    """
    s = u''

    if isinstance(value, basestring):
        s = unicode(value)

    elif isinstance(value, list):
        items = ['(LENGTH %d)' % len(value)]

        for idx, sub_v in enumerate(value):
            items.append('(%d %s)' % (idx, dumps(sub_v)))

        s = ' '.join(items)

    elif isinstance(value, dict):
        pairs = []
        for key, sub_value in value.items():
            pairs.append(u'(%s %s)' % (unicode(key),
                                       escape(dumps(sub_value))))
        s += ' '.join(pairs)
    else:
        s = unicode(value)

    return s

def loads(string):
    """
    Parses a YASA style map and returns a dictionary. No attempt at recursive
    parsing of sub-maps is made.
    """
    parser = _Parser(string)
    parser.parse()
    return parser._parsed

def recv_load(socket, catch_parse_errors=True):
    p = _Parser("")
    return p.line_generator(socket, catch_parse_errors=True)

def listify(l):
    """
    Takes a YASA syle list (already parsed into a dictionary) and returns a
    python list.
    """
    arr = [None] * int(l.get('length', 0))
    for k, v in l.items():
        if k.upper() == 'LENGTH':
            continue

        arr[int(k)] = v

    return arr

def is_valid(string):
    try:
        loads(string)
    except ParseError:
        return False
    else:
        return True
