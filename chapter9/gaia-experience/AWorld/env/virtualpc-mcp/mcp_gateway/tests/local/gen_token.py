import os, time, jwt


def gen_auth_token(app: str = "agiopenwebui-vnc-proxy"):
    # novnc_server_secret = "123321"
    novnc_server_secret = "AwOrld@0DF0-41F9-4d47-9730-35F706B76045@20250820"
    pay_load = {"app": app, "version": 1, "time": time.time()}
    token = jwt.encode(payload=pay_load, key=novnc_server_secret, algorithm="HS256")
    return token


token = gen_auth_token(app="aworldcore-agent")
print(token)
