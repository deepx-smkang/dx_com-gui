#!/usr/bin/env python3
"""
Setup script for DXCom GUI application.
Alternative to pyproject.toml for older Python/pip versions.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="dxcom-gui",
    version="1.0.0",
    description="Professional GUI for compiling ONNX models to DXNN format using DXCom compiler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="contact@example.com",
    url="https://github.com/deepx-smkang/dx_com-gui",
    project_urls={
        "Documentation": "https://github.com/deepx-smkang/dx_com-gui/blob/main/README.md",
        "Source": "https://github.com/deepx-smkang/dx_com-gui",
        "Tracker": "https://github.com/deepx-smkang/dx_com-gui/issues",
    },
    
    # Package configuration
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    include_package_data=True,
    package_data={
        "": ["*.png", "*.qss", "*.json"],
    },
    
    # Dependencies
    python_requires=">=3.8",
    install_requires=requirements,
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-qt>=4.0.0",
            "flake8>=5.0.0",
            "black>=22.0.0",
            "mypy>=0.990",
        ],
    },
    
    # Entry points
    entry_points={
        "console_scripts": [
            "dxcom-gui=src.__main__:main",
        ],
    },
    
    # Metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Compilers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
    ],
    
    keywords="onnx dxnn model-compiler neural-network deep-learning gui qt pyside6",
    
    # Additional metadata
    license="Proprietary",
    platforms=["Linux"],
    
    # Zip safety
    zip_safe=False,
)
