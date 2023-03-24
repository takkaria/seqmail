from setuptools import setup

setup(
    name="seqmail",
    version="0.1a",
    py_modules=["seqmail"],
    install_requires=[
        "requests",
        "todoist-python",
        "simple-term-menu",
        "mypy",
        "ansicolors",
        "xdg-base-dirs",
        "click",
        "black[d]",
        "typedload",
    ],
    entry_points={
        "console_scripts": [
            "seqmail = seqmail.cli:cli",
        ],
    },
)
