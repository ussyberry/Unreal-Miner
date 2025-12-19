from setuptools import setup, find_packages

setup(
    name="unreal_miner",
    version="0.2.0",
    description="AI-powered satellite data processing for mineral exploration",
    author="Unreal Miner Team",
    packages=find_packages(),
    install_requires=[
        "rasterio>=1.3.0",
        "gdal>=3.0.0",
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "scikit-learn>=1.0.0",
        "imageio>=2.9.0",
        "Pillow>=9.0.0",
        "pandas>=1.3.0",
        "requests>=2.27.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0",
            "matplotlib>=3.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "unreal-miner-process=unreal_miner.process_fusion:main",
            "unreal-miner-export=unreal_miner.export_unreal:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
