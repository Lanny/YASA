import re

class ParseError(Exception):
    pass

class EOLException(Exception):
    pass

# Parser states
IN_KEY = 0
IN_VALUE = 1
OUTSIDE = 2

class _Parser(object):
    def __init__(self, string):
        self._parsed = {}
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

        self._parsed = {}
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
                self._parsed[self._key] = self._value
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

    def line_generator(self, socket):
        """
        Takes a socket (or anything that implements the `recv` method) and
        returns a generator which will parse and return data comming over
        the socket by line, as the lines come in.
        """
        data = socket.recv(1024)

        while data:
            self._string += data

            try:
                self._partial_parse()
            except EOLException:
                yield self._flip()

            data = socket.recv(1024)


def unescape(string):
    """
    Takes a string and unescapes it per the spec
    """
    return (string.replace('\\\\', '<PSEUDOBSLASH>')
                  .replace('\\)', ')')
                  .replace('<PSEUDOBSLASH>', '\\'))

def loads(string):
    """
    Parses a YASA style map and returns a dictionary. No attempt at recursive
    parsing of sub-maps is made.
    """
    parser = _Parser(string)
    parser.parse()
    return parser._parsed

def recv_load(socket):
    p = _Parser("")
    return p.line_generator(socket)

def is_valid(string):
    try:
        loads(string)
    except ParseError:
        return False
    else:
        return True
