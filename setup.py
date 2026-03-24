"""Setup for cnovita."""

from setuptools import setup, find_packages

setup(
    name="cnovita",
    version="0.3.0",
    description="CLI for all Novita AI APIs - LLM, images, video, audio, GPU, serverless",
    long_description=(
        (open("README.md").read() if __import__("os").path.exists("README.md") else "")
        + "\n\n"
        + (open("CHANGELOG.md").read() if __import__("os").path.exists("CHANGELOG.md") else "")
    ),
    long_description_content_type="text/markdown",
    author="jaxzhang-novita",
    url="https://github.com/jaxzhang-novita/cnovita",
    python_requires=">=3.8",
    packages=find_packages(include=["cnovita", "cnovita.*"]),
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
    ],
    entry_points={
        "console_scripts": [
            "novita=cnovita.novita_cli:main",
            "cnovita=cnovita.novita_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
