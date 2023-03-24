from setuptools import setup

setup(
    name="seqmail",
    version="0.1.0-alpha",
    py_modules=["seqmail"],
    install_requires=[
        "requests",
        "todoist-python",
        "simple-term-menu",
        "ansicolors",
        "xdg-base-dirs",
        "click",
        "typedload",
    ],
    extras_require={"dev": ["mypy", "black[d]", "pre-commit"]},
    entry_points={
        "console_scripts": [
            "seqmail = seqmail.cli:cli",
        ],
    },
)
