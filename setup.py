from setuptools import setup, find_packages

from tesla_powerwall import VERSION

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="tesla_powerwall",
    version=VERSION,
    description="API for Tesla Powerwall",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jrester/tesla_powerwall",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7"
    ],
    install_requires=[
        "requests>=2.22.0"
    ],
    tests_require=[
        "requests>=2.22.0"
        "responses>="
    ],
    test_suite="unittest"
)
