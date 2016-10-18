from setuptools import setup

try:
    from pyqt_distutils.build_ui import build_ui
    cmdclass = {"build_ui": build_ui}
except ImportError:
    cmdclass = {}

setup(
    name="stenodictate",
    version="0.1",
    description="Dictates text and grades transcriptions "
                "for stenographer students.",
    url="https://github.com/arxanas/StenoDictate",
    author="Waleed Khan",
    author_email="me@waleedkhan.name",
    license="GPL3",
    packages=["stenodictate"],
    cmdclass=cmdclass,
)
