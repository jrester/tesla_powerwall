from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="tesla_powerwall",
    version="0.3.6",
    description="API for Tesla Powerwall",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jrester/tesla_powerwall",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=["requests>=2.22.0", "packaging>=20.0"],
)
