from setuptools import setup

setup(
    name="mini-vcs",
    version="0.1",
    description="A minimal version control system in Python",
    py_modules=["vcs"],
    entry_points={
        "console_scripts": [
            "vcs = vcs:main",  # vcs command maps to main() in vcs.py
        ],
    },
)
