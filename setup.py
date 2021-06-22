#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

from compatibility import _version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="compatibility",
    version=f"{_version.__version__}",
    author="Rüdiger Voigt",
    author_email="projects@ruediger-voigt.eu",
    description="""A library that checks whether the running version of Python is compatible and tested.
                   Remind the user to check for updates of the library.""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RuedigerVoigt/compatibility",
    package_data={
        "compatibility": ["py.typed"]},
    include_package_data=True,
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities",
        "Typing :: Typed"
    ],
)
