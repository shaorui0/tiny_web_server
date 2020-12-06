from io import BytesIO

from app.application import Application
from app.headers import Headers
from app.request import Request
from app.response import Response

# app

app = Application()

@app.route("/")
def static_handler(request):
    return Response(content="static")

@app.route("/people/{name}/{age}")
def dynamic_handler(request, name, age):
    return Response(content=f"{name} is {age} years old!")

# 注册


# test里面使用，每个函数都要用到

class ApplicationTesting(unittest.TestCase):
    def test_Application_can_add_routes(self):
        # 输入是什么，输出是什么？
        # 如何访问静态和动态？
        # 创建一个requst？创建一个socket？
        # 怎么执行？
        # response = app(requstxxx)
        # 然后和什么对比？对比值 static，那看看这个感觉？
        response = app(Request(method="GET", path="/", headers=Headers(), body=BytesIO()))
        self.assertEqual(response.content, b"static")
        
if __name__ == '__main__':
    unittest.main()