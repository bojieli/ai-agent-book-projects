import time
import jwt


def gen_auth_token(root_token: str, app: str):
    pay_load = {"app": app, "version": 1, "time": time.time()}
    token = jwt.encode(payload=pay_load, key=root_token, algorithm="HS256")
    return token


def test_gen_token():
    root_token = "123321"
    token = gen_auth_token(root_token, "local_debug")
    print(token)


if __name__ == "__main__":
    test_gen_token()
