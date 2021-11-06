# -*- coding: utf-8 -*-
import os.path

from setuptools import find_packages, setup


def requirements(path):
    assert os.path.exists(path), "Missing requirements {}.format(path)"
    with open(path) as f:
        return list(map(str.strip, f.read().splitlines()))


install_requires = requirements("requirements.txt")

setup(
    name="horae-text-reuse",
    version=0.1,
    description="HORAE Text-reuse evaluation package",
    author="IRHT-Teklia",
    author_email="charlotte.mauvezin@protonmail.com",
    install_requires=install_requires,
    packages=find_packages("src"),
    package_dir={"": "src"},
)
