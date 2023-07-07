"""
Setup.py file.
Install once-off with:  "pip install ."
For development:        "pip install -e .[dev]"
"""
import setuptools


with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

PROJECT_NAME = "pipeline"

setuptools.setup(
    name=PROJECT_NAME,
    version="0.1",
    author="Tijs Ziere",
    author_email="tziere@redcross.nl",
    description="KoBoto121 pipeline",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=install_requires,
    extras_require={
        "dev": [  # Place NON-production dependencies in this list - so for DEVELOPMENT ONLY!
            "black",
            "flake8"
        ],
    },
    entry_points={
        'console_scripts': [
            f"kobo-121 = {PROJECT_NAME}.pipeline:main",
        ]
    }
)