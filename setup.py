import re
import sys

from setuptools import setup

try:
    from pyqt_distutils.build_ui import build_ui
    cmdclass = {"build_ui": build_ui}
except ImportError:
    cmdclass = {}


def _get_version():
    with open("stenodictate/__init__.py") as f:
        version = re.search(r"""
            __version__
            [ ]=[ ]
            "
                (?P<version>[^"]+)
            "
        """, f.read(), re.VERBOSE)
        return version.group("version")


def _get_requirements():
    requirements = [
        "PyQt5==5.7",
        "appdirs>=1.4.0",
        "py>=1.4.31",

        # Technically, textstat doesn't support Python 3. In fact, it returns
        # different results in its tests between Python 2 and 3 for most of it
        # sfunctions functions. But the results are consistent for the syllable
        # count function, which is the one we care about.
        "textstat>=0.3.1",
    ]

    if "win32" in sys.platform:
        requirements.extend([
            "pypiwin32>=219",
        ])
    elif "darwin" in sys.platform:
        requirements.extend([
            "pyobjc>=3.1.1",
        ])

    return requirements


setup(
    name="stenodictate",
    version=_get_version(),
    description="Dictates text and grades transcriptions "
                "for stenographer students.",
    url="https://github.com/arxanas/StenoDictate",
    author="Waleed Khan",
    author_email="me@waleedkhan.name",
    license="GPL3",
    packages=["stenodictate"],
    cmdclass=cmdclass,
    install_requires=_get_requirements(),
)
