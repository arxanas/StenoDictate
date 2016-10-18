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
        "appdirs>=1.4.0",
        "py>=1.4.31",
        "pyttsx>=1.1",
        "textstat>=0.3.1",
    ]

    if "win32" in sys.platform:
        # Should probably include PyWin32.
        raise NotImplementedError()
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
