import unittest

from app.headers import Headers

class HeadersTesting(unittest.TestCase):
    def test_can_add_headers(self):
        headers = Headers()
        headers.add('a-header', 'a value')
        self.assertEqual(headers.get('a-header'), 'a value')
    
    def test_headers_are_case_insensitive(self):
        headers = Headers()
        headers.add('A-HEADER', 'a value')
        self.assertEqual(headers.get('a-header'), 'a value')
    
    def test_getting_a_missing_header_returns_none(self): 
        headers = Headers()
        self.assertEqual(headers.get("not exist"), None)
    
    def test_can_get_headers_with_fallback(self):
        headers = Headers()
        self.assertEqual(headers.get('not exist', 'fallback'), 'fallback')
    
    def test_can_get_all_of_a_headers_values(self):
        headers = Headers()
        headers.add('a-header', 'a value')
        headers.add('a-header', 'other value')
        self.assertEqual(headers.get_all('a-header'), ['a value', 'other value'])
    
    def test_can_get_last_of_headers_value(self):
        headers = Headers()
        headers.add('a-header', 'a value')
        headers.add('a-header', 'other value')
        self.assertEqual(headers.get('a-header'), 'other value')

if __name__ == '__main__':
    unittest.main()