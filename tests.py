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
        
        d = parse.loads('(ACTION SEHSAH-TSIL) SHALOM (HASHES (1 2 3 4\\))')
        assert len(d.keys()) == 2
        assert 'SHALOM' not in d

    def test_dumps(self):
        s = parse.dumps({'ACTION': 'LIST-HASHES'})
        assert s == '(ACTION LIST-HASHES)'

        s = parse.dumps({'ACTION': 'SEHSAH-TSIL', 'HASHES': 'HEY!'})
        assert s == '(ACTION SEHSAH-TSIL) (HASHES HEY!)'

        s = parse.dumps({'ACTION': 'SEHSAH-TSIL',
                         'HASHES': {'K1': 'V1'}})
        assert s == '(ACTION SEHSAH-TSIL) (HASHES (K1 V1\\))'

        s = parse.dumps({'ACTION': 'SEHSAH-TSIL',
                         'HASHES': ['what', 'is', 'up']})
        assert s == ('(ACTION SEHSAH-TSIL) (HASHES (LENGTH 3\\) '
                     '(0 what\\) (1 is\\) (2 up\\))')

    def test_unescape(self):
        assert parse.unescape(r'(HASHES (1 2 3 4\))') == '(HASHES (1 2 3 4))'
        assert parse.unescape(r'(HASHES \(1 2 3 4\))') == r'(HASHES \(1 2 3 4))'
        assert parse.unescape('TEST 123') == 'TEST 123'
        assert parse.unescape(r'\(HASHES 1\\)') == r'\(HASHES 1\)'

if __name__ == '__main__':
    unittest.main()

