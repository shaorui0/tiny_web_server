from io import BytesIO
from textwrap import dedent

import unittest

from app.request import Request

class StubSocket:
    """
    mock a socket
    """
    # push data to socket for testing
    def __init__(self, data: str):
        # byte stream
        self._buff = BytesIO(data.encode())

    def recv(self, n):
        # recv from buffer
        return self._buff.read(n)

def make_request(s: str):
    return dedent(s).replace("\n", "\r\n")

class RequestTesting(unittest.TestCase):
    def test_get_request(self):
        a_request = make_request("""\
        GET / HTTP/1.0
        Accept: text/html

        """)
        request = Request.from_socket(StubSocket(a_request))

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.path, "/")
        self.assertEqual(request.headers.get("accept"), "text/html")
        self.assertEqual(request.body.read(16384), b"")
    
    def test_post_request(self):
        a_request = make_request("""\
        POST /users HTTP/1.0
        Accept: application/json
        Content-type: application/json
        Content-length: 2
        
        {}""")
        request = Request.from_socket(StubSocket(a_request))

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.path, "/users")
        self.assertEqual(request.headers.get("accept"), "application/json")
        self.assertEqual(request.headers.get("content-type"), "application/json")
        self.assertEqual(request.headers.get("content-length"), "2")
        self.assertEqual(request.body.read(16384), b"{}")

    # test exception
    def test_not_exist_header_in_request(self):
        a_request = make_request("""\

        """)
        with self.assertRaises(ValueError) as context:
            Request.from_socket(StubSocket(a_request))

        self.assertTrue("Request line error." in str(context.exception))


    def test_incomplete_content_of_header_in_request(self):
        a_request = make_request("""\
        GET
        """)
        with self.assertRaises(ValueError) as context:
            Request.from_socket(StubSocket(a_request))

        self.assertTrue("Malformed request line 'GET'." in str(context.exception))
        
    def test_body_cannot_partition_by_colon_in_request(self):
        a_request = make_request("""\
        GET / HTTP/1.0
        Content-type
        """)

        with self.assertRaises(ValueError) as context:
            Request.from_socket(StubSocket(a_request))

        self.assertTrue("Malformed header line b'Content-type'." in str(context.exception))


if __name__ == '__main__':
    unittest.main()