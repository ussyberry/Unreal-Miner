from setuptools import setup, find_packages

setup(
    name="unreal_miner",
    version="0.1.0",
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
        "joblib>=1.1.0",
    ],
    entry_points={
        "console_scripts": [
            "unreal-miner-process=unreal_miner.process_fusion:main",
            "unreal-miner-export=unreal_miner.export_unreal:main",
        ],
    },
)
