import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()

setuptools.setup(
    name="b3book",
    version="0.0.1",
    author="Eduardo Fonseca Brasil",
    author_email="efbrasil@gmail.com",
    description="B3 Limit Order Book handling",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/efbrasil/b3book",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
