from setuptools import setup


def requirements(path):
    with open(path) as f:
        return f.read().splitlines()


setup(
    name="x-trainer-convert",
    version=open("VERSION").read().replace("\n", ""),
    author="Lars Munch",
    author_email="lars@segv.dk",
    description="Convert indoor bike workout data from X-Trainer "
                "CSV format to TCX files.",
    url="https://github.com/lmunch/x-trainer-convert",
    license="MIT",
    keywords="X-Trainer CVS TCX convert Garmin Connect upload",
    packages=["x_trainer_convert"],
    install_requires=requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "x-trainer-convert = x_trainer_convert.main:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
    ],
)
