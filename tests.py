#!/usr/bin/env python
import unittest
import parse

class TestParse(unittest.TestCase):
    def test_valid(self):
        assert parse.is_valid('(ACTION LIST-HASHES)')
        assert parse.is_valid('(ACTION )')
        assert parse.is_valid('(ACTION SEHSAH-TSIL) (HASHES \\(1 2 3 4\\))')

        assert not parse.is_valid('(ACTION LIST-HASHES')
        assert not parse.is_valid('(ACTION)')
        assert not parse.is_valid('(ACTION) (HASHES 1)')
        assert parse.is_valid('(ACTION SEHSAH-TSIL) (HASHES (1 2 3 4))')

    def test_loads(self):
        d = parse.loads('(ACTION LIST-HASHES)')
        assert 'ACTION' in d
        assert d['ACTION'] == 'LIST-HASHES'

        d = parse.loads('(ACTION SEHSAH-TSIL) (HASHES (1 2 3 4\\))')
        assert 'HASHES' in d
        assert d['HASHES'] == '(1 2 3 4)'

    def test_unescape(self):
        assert parse.unescape(r'(HASHES (1 2 3 4\))') == '(HASHES (1 2 3 4))'
        assert parse.unescape(r'(HASHES \(1 2 3 4\))') == r'(HASHES \(1 2 3 4))'
        assert parse.unescape('TEST 123') == 'TEST 123'
        assert parse.unescape(r'\(HASHES 1\\)') == r'\(HASHES 1\)'

if __name__ == '__main__':
    unittest.main()

