import time

class TestClassA:

    def classa_function_1(self):
        print("classa_function_1")

    def classa_function_2(self):
        time.sleep(0.02)
        print("classa_function_2")

    def classa_function_3(self):
        print("classa_function_3")

class TestClassB:
    def classb_function_1(self):
        time.sleep(0.02)
        print("classb_function_1")
    def classb_function_2(self):
        a = TestClassA()
        a.classa_function_1()
        a.classa_function_2()
        a.classa_function_3()
        print("classb_function_2")