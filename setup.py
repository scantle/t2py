from setuptools import setup, find_packages

setup(
    name='t2py',
    version='0.0.2',
    packages=find_packages(),
    install_requires=['numpy','pandas'],
    url='https://github.com/scantle/t2py',
    license='MIT',
    author='Leland Scantlebury',
    author_email='leland@sspa.com',
    description='Texture2Par Python Package'
)
