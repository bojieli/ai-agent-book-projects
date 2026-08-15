# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import os
import getpass
import time

__version__ = '0.2.7'

version_template = \
    """# auto generated
class VersionInfo:
    BUILD_DATE = "{BUILD_DATE}"
    BUILD_VERSION = "{BUILD_VERSION}"
    BUILD_USER = "{BUILD_USER}" 
    SCENARIO = "{SCENARIO}"
"""


def generate_version_info(directory_path: str = None, scenario: str = "", version: str = None):
    if directory_path is None:
        directory_path = os.path.dirname(__file__)
    with open(os.path.join(directory_path, "version_info.py"), "w") as f:
        version_info = _build_version_template(scenario=scenario, version=version)
        f.write(version_info)


def _build_version_template(scenario: str = "", version: str = None) -> str:
    if version is None:
        version = __version__
    return version_template.format(
        BUILD_USER=getpass.getuser(),
        BUILD_VERSION=version,
        BUILD_DATE=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        SCENARIO=scenario,
    )
