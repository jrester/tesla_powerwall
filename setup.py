from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="tesla_powerwall",
    author="Jrester",
    author_email="jrester379@gmail.com",
    version='0.3.16',
    description="API for Tesla Powerwall",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jrester/tesla_powerwall",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    package_data={
        'tesla_powerwall': ["py.typed"]
    },
    install_requires=["requests>=2.22.0"],
)
