from setuptools import setup, find_packages

setup(
    name="pokemon_rom_player",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "pyautogui>=0.9.53",
        "pytesseract>=0.3.8",
        "Pillow>=8.0.0",
        "colorlog>=6.7.0",
        "pyyaml>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "mypy>=0.910",
            "black>=24.1.0",
            "flake8>=7.0.0",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    description="An AI-powered Pokemon ROM player",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 