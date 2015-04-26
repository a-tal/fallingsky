"""The Tragedy of the Falling Sky's setup.py."""


try:
    import pygame  # have this setup beforehand
except ImportError:
    raise SystemExit("unable to import pygame.")


from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


with open("fallingsky/__init__.py", "r") as openinit:
    for line in openinit.readlines():
        if line.startswith("__version__ ="):
            __version__ = line[14:].replace('"', "").replace('"', "").strip()
            break
    else:
        __version__ = "0.0.0"


class PyTest(TestCommand):
    """Shim in pytest to be able to use it with setup.py test."""

    def finalize_options(self):
        """Stolen from http://pytest.org/latest/goodpractises.html."""

        TestCommand.finalize_options(self)
        self.test_args = ["-v", "-rf", "--cov-report", "term-missing", "--cov",
                          "fallingsky", "test"]
        self.test_suite = True

    def run_tests(self):
        """Also shamelessly stolen."""

        # have to import here, outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


setup(
    name="fallingsky",
    version=__version__,
    author="Adam Talsma",
    author_email="adam@talsma.ca",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["kezmenu", "appdirs"],
    dependency_links=[
        "https://gitlab.com/a-tal/kezmenu/repository/archive.tar.bz2#egg=kezmenu",
    ],
    entry_points={"console_scripts": ["fallingsky = fallingsky.main:play"]},
    url="https://github.com/a-tal/fallingsky",
    description="A game of falling blocks with RPG elements, uses pygame.",
    long_description=(
        "The Tragedy of the Falling Sky intends to be a RPG style block game. "
        "It is still in very early development though, so many features are "
        "missing. Also the artwork is very preliminary and will be improved "
        "upon. Feel free to contribute to the project on GitHub, all pull "
        "requests are welcomed."
    ),
    download_url="https://github.com/a-tal/fallingsky",
    tests_require=["pytest", "pytest-cov"],
    cmdclass={"test": PyTest},
    license="GPLv2",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Arcade",
        "Topic :: Games/Entertainment :: Puzzle Games",
        "Topic :: Software Development :: Libraries :: pygame",
    ],
)
