import re

class ParseError(Exception):
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
        self._slen = len(string)
        self._string = string
        self._mode = OUTSIDE
        self._key = None
        self._value = None

    def parse(self):
        """
        Parses the remainder of the string.
        """
        while self._idx < self._slen:
            c = self._string[self._idx]

            if self._mode == OUTSIDE and c == '(':
                self._mode = IN_KEY
                self._mark = self._idx+1

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

        if self._mode != OUTSIDE:
            raise ParseError('Unmatched parentheses at index %d' % 
                             (self._mark-1,))
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

def is_valid(string):
    try:
        loads(string)
    except ParseError:
        return False
    else:
        return True
