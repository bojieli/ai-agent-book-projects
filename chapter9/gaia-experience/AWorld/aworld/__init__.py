# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import atexit
import os

try:
    from aworld.utils.import_package import import_package

    import_package("dotenv", install_name="python-dotenv")
    from dotenv import load_dotenv

    sucess = load_dotenv()
    if not sucess:
        load_dotenv(os.path.join(os.getcwd(), ".env"))
except Exception as e:
    print(e)


def cleanup():
    import re

    try:
        value = os.environ.get("LOCAL_TOOLS_ENV_VAR", '')
        if value:
            for action_file in value.split(";"):
                v = re.split(r"\w{6}__tmp", action_file)[0]
                if v == action_file:
                    continue
                tool_file = action_file.replace("_action.py", ".py")
                try:
                    os.remove(action_file)
                    os.remove(tool_file)
                except:
                    pass
    except:
        pass
    os.environ["LOCAL_TOOLS_ENV_VAR"] = ''


atexit.register(cleanup, )
