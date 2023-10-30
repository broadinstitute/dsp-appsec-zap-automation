from setuptools import setup, find_packages

packages = ["zap_helper"]

setup(
    name='zap_helper',
    version='0.1',
    author="Sarah Gibson",
    author_email="sgibson@broadinstitute.org",
    description="Helper functions for setting up and managing authenticated ZAP scans",
    url="https://github.com/broadinstitute/dsp-appsec-zap-automation",
    packages=find_packages(),
    install_requires=[
        'requests'
    ]
)