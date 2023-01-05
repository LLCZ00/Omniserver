import os
from setuptools import setup, find_packages


with open(os.path.join("omniserver", "version.py"), "r") as vfile:
    exec(vfile.read())


this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, "README.md"), "r") as file:
    readme = file.read()

requirements = [
    "dnslib"
    ]

setup(
    name="omniserver",
    version=__version__,
    author="LLCZ00",
    description="Networking CLI tool and module",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/LLCZ00/Omniserver",
    license="Apache 2.0",
    keywords="malware analysis detection",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    zip_safe=False,
    install_requires=requirements,
    packages=find_packages()
)

