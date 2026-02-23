from setuptools import setup, find_packages

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
    long_description_content_type = "text/markdown"
except FileNotFoundError:
    long_description = "File Auto-Sorter - автоматическая сортировка файлов"
    long_description_content_type = "text/plain"

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="dfsort",
    version="1.0.2",
    author="Vladislav Malygin",
    author_email="malyginvlad6220@gmail.com",
    description="File Auto-Sorter - автоматическая сортировка файлов",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vladislav/dfsort",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "dfsort = dfsort.cli:main",
        ],
    },
    data_files=[
        ('/etc/dfsort', ['config/config.yaml']),
        ('/usr/lib/systemd/user', ['systemd/dfsort.service']),
    ],
    include_package_data=True,
)