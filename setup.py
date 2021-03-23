import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Algorithmic Trading Bot",
    version="1.6.0",
    author="Jake Thomson",
    author_email="jakethomson0@gmail.com",
    description="The backend of the algorithmic trading bot project.",
    long_description="long_description",
    long_description_content_type="text/markdown",
    url="https://github.com/JakeThomson/ATB_back-end",
    project_urls={
        "UI": "https://diss.jake-t.codes",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)