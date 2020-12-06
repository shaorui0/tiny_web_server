import unittest
from io import BytesIO

from app.application import Application
from app.headers import Headers
from app.request import Request
from app.response import Response

app = Application()

@app.route("/")
def static_handler(request):
    return Response("200", content="static")

@app.route("/people/{name}/{age}")
def dynamic_handler(request, name, age):
    return Response(content=f"{name} is {age} years old!")


class ApplicationTesting(unittest.TestCase):
    def test_application_can_run_static_request(self):
        response = app(Request(method="GET", path="/", headers=Headers(), body=BytesIO()))
        self.assertEqual(response.body.read(), b"static")
       
        
if __name__ == '__main__':
    unittest.main()