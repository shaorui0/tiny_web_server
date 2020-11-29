import unittest
from app.response import Response
from app.router import Router

class RouterTesting(unittest.TestCase):
    def test_router_can_add_routes(self):
        router = Router()
        def get_example(request):
            return Response()
        
        router.add_router("get_example", "GET", "/example", get_example)
        print(router.lookup("GET", "/example"))
        print(router.lookup("GET", "/example").func)
        print(router.lookup("GET", "/example").args)
        print(router.lookup("GET", "/example").keywords)
        self.assertEqual(router.lookup("GET", "/example").func is get_example, True)
        self.assertEqual(router.lookup("GET", "/missing") is None, True)
        
    def test_router_can_add_routes_with_dynamic_segments(self):
        router = Router()
        # And a route handler
        def get_example(name):
            return name

        router.add_router("get_example", "GET", "/users/{name}", get_example)
        
        handler = router.lookup("GET", "/users/Jim")
        self.assertEqual(handler.func is get_example, True)
        
        print(handler) # function like closure + args
        self.assertEqual(handler(), 'Jim')
    
    def test_router_fails_to_add_routes_with_duplicate_names(self):
        router = Router()
        
        def get_example(name):
            return name
        
        with self.assertRaises(ValueError) as context:
            router.add_router("get_example", "GET", "/users/{name}", get_example)
            router.add_router("get_example", "GET", "/users/{name}", get_example)
            
        self.assertTrue("A route named get_example already exists." in str(context.exception))


if __name__ == '__main__':
    unittest.main()