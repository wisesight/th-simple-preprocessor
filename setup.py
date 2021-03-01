from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setup(
    name="th-simple-preprocessor",
    version="0.4.0",
    author="WISESIGHT Product Development",
    author_email="tequila@wisesight.com",
    description="Simple Thai Preprocess Functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wisesight/th-simple-preprocessor",
    install_requires=requirements,
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: Thai",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
        "Topic :: Text Processing :: General",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.6",
)
