# Copyright Sierra

from setuptools import find_packages, setup

setup(
    name="tau_bench",
    version="0.1.0",
    description="The Tau-Bench package",
    long_description=open("README.md").read(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "openai>=1.13.3",
        "mistralai>=0.4.0",
        "anthropic>=0.26.1",
        "google-generativeai>=0.5.4",
        "tenacity>=8.3.0",
        "termcolor>=2.4.0",
        "numpy>=1.26.4",
        "litellm>=1.41.0",
    ],
)
