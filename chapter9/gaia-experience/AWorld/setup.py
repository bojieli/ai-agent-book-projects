# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import logging
import os
import sys
import re
import subprocess

from setuptools import setup, find_packages
from setuptools.command.sdist import sdist
from setuptools.command.install import install
from setuptools.dist import Distribution

from aworld.version_gen import __version__

logger = logging.getLogger("setup")

version_template = """
# auto generated
class VersionInfo(object):
    @property
    def build_date(self):
      return "{BUILD_DATE}"

    @property
    def version(self):
      return "{BUILD_VERSION}"

    @property
    def build_user(self):
      return "{BUILD_USER}"
"""


def check_output(cmd):
    import subprocess

    output = subprocess.check_output(cmd)
    return output.decode("utf-8")


def get_build_date():
    import datetime
    import time

    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def build_version_template():
    import getpass

    return version_template.format(
        BUILD_USER=getpass.getuser(),
        BUILD_VERSION=__version__,
        BUILD_DATE=get_build_date(),
    )


def call_process(cmd, raise_on_error=True, logging=True):
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False  # cmd should be list of args

    try:
        subprocess.check_call(cmd, shell=shell, timeout=60)
    except subprocess.CalledProcessError as e:
        if raise_on_error:
            raise e
        logger.error(f"Fail to execute {cmd}, {e}")
        return e.returncode

    if logging:
        logger.info(f"Successfully execute: {cmd}")
    return 0


class AWorldPackage(sdist):
    def run(self):
        from aworld.version_gen import generate_version_info

        home = os.path.join(os.path.dirname(__file__), "aworld")
        with open(os.path.join(home, "version.py"), "w") as f:
            version_info = build_version_template()
            f.write(version_info)

        generate_version_info(scenario="AWORLD_SDIST")

        sdist.run(self)


class AWorldInstaller(install):
    EXTRA_ENV = "AWORLD_EXTRA"
    BASE = "framework"
    BASE_OPT = "optional"

    def __init__(self, *args, **kwargs):
        super(AWorldInstaller, self).__init__(*args, **kwargs)
        self._requirements = parse_requirements("aworld/requirements.txt")
        self._extra = os.getenv(self.EXTRA_ENV)
        logger.info(f"{os.getcwd()}: Install AWORLD using extra: {self._extra}")

    def run(self):
        # 1. build wheel using this setup.py, thus using the right install_requires according to ALPS_EXTRA
        # 2. install this wheel into pip
        install.run(self)

        reqs = self._requirements.get(self.BASE, [])
        self._install_reqs(reqs, ignore_error=True)

        # install optional requirements here since pip install doesn't ignore requirement error
        reqs = self._requirements.get(self.BASE_OPT, [])
        self._install_reqs(reqs, ignore_error=True)

    def _contains_module(self, module):
        if self._extra is None:
            return False

        modules = [mod.strip() for mod in self._extra.split(",")]
        try:
            modules.index(module)
            return True
        except ValueError:
            return False

    @staticmethod
    def _install_reqs(reqs, ignore_error=False, no_deps=False):
        """
        Install a list of requirements using pip.
        Use argument lists (no shell) to avoid quoting issues on Windows (single quotes are literal).
        """
        base_cmd = [sys.executable, "-m", "pip", "install"]
        if no_deps:
            base_cmd.append("--no-deps")
        if ignore_error:
            # install requirements one by one so a failure doesn't stop the rest
            for req in reqs:
                try:
                    cmd = base_cmd + [req]
                    call_process(cmd)
                    logger.info(f"Installing optional package {req} have succeeded.")
                except Exception:
                    logger.warning(
                        f"Installing optional package {req} is failed, Ignored."
                    )  # ignore
        elif reqs:
            cmd = base_cmd + list(reqs)
            call_process(cmd)
            logger.info(f"Packages {str(reqs)} have been installed.")


def parse_requirements(req_fname):
    requirements = {}
    module_name = "unknown"
    for line in open(req_fname, "r"):
        match = re.match(r"#+\s+\[(\w+)\]\s+#+", line.strip())
        if match:
            # the beginning of a module
            module_name = match.group(1)
        else:
            req = line.strip()
            if not req or req.startswith("#"):
                continue

            # it's a requirement, strip trailing comments
            pos = req.find("#")
            if pos > 0:
                req = req[:pos]
                req = req.strip()

            if module_name not in requirements:
                requirements[module_name] = []
            requirements[module_name].append(req)

    return requirements


def get_install_requires(extra, requirements):
    modules = [AWorldInstaller.BASE]
    if extra is None:
        # old style of `pip install alps`, install all requirements for compatibility
        for mod in requirements:
            if mod in [AWorldInstaller.BASE, AWorldInstaller.BASE_OPT]:
                continue
            modules.append(mod)
    else:
        for mod in extra.split(","):
            mod = mod.strip()
            if mod != AWorldInstaller.BASE:
                modules.append(mod)

    install_reqs = []
    for mod in modules:
        install_reqs.extend(requirements.get(mod, []))
    return install_reqs


def get_python_requires():
    return ">=3.11"


class BinaryDistribution(Distribution):
    """This class is needed in order to create OS specific wheels."""

    @staticmethod
    def has_ext_modules():
        return True


requirements = parse_requirements("aworld/requirements.txt")
extra = os.getenv(AWorldInstaller.EXTRA_ENV, None)

setup(
    name="aworld",
    version=__version__,
    description="Ant Agent Package",
    url="https://github.com/inclusionAI/AWorld",
    author="Ant AI",
    author_email="",
    long_description="",
    long_description_content_type="text/markdown",
    packages=find_packages(
        where=".",
        exclude=[
            "tests",
            "tests.*",
            "*.tests",
            "*.tests.*",
            "test",
            "*.test",
            "*.test.*",
            "test.*",
        ],
    ),
    package_data={
        "aworld": [
            "virtual_environments/browsers/script/*.js",
            "dataset/gaia/gaia.npy",
            "requirements.txt",
            "config/*.yaml",
            "config/*.json",
            "config/*.tiktoken",
            "cmd/web/webui/public/trace_ui.html",
            "cmd/web/webui/dist/**",
        ],
        "examples": [
            "**/mcp.json",
            "gaia/GAIA/**",
        ],
    },
    license="MIT",
    platforms=["any"],
    keywords=["multi-agent", "agent", "environment", "tool", "sandbox"],
    cmdclass={
        "sdist": AWorldPackage,
        "install": AWorldInstaller,
    },
    install_requires=get_install_requires(extra, requirements),
    python_requires=get_python_requires(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "aworld = aworld.__main__:main",
        ]
    },
)
