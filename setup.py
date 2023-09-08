import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    sys.exit('Python3 version < 3.6 is not supported')

setup(
    name='echos',
    version='0.1.0',
    url='https://github.com/tai-yin/echos',
    author='Tai Yin',
    description='Dispatch and execute python functions on Cloud',
    long_description="echos provides easy to use interface to let you execute your python functions on Cloud",
    author_email='yt8630@gmail.com',
    packages=find_packages(),
    install_requires=[
        'rich', 'boto3'
    ],
    tests_requires=[
        'pytest', 'numpy',
    ],
    entry_points={
        'console_scripts': ['echos-setup=echos.scripts.setup:setup_infra',
                            'echos-cleanup=echos.scripts.cleanup:cleanup_infra']},
    package_data={
        'echos': ['aws_config.yaml']},
    include_package_data=True
)
