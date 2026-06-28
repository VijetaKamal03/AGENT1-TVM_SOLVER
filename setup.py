from setuptools import setup, find_packages

setup(
    name="tvm-solver-agent",
    version="0.1.0",
    description="Streamlit-based TVM solver with Claude-powered reasoning",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "anthropic>=0.40.0",
        "streamlit>=1.40.0",
    ],
)
