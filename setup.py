# coding=utf8
__author__ = 'liming'

from setuptools import setup

setup(name='flask-apidoc',
      version='0.0.1',
      description='generate api-documentation from doc string',
      url='https://github.com/ipconfiger/flask-apidoc',
      author='Alexander.Li',
      author_email='superpowerlee@gmail.com',
      license='GNU GENERAL PUBLIC LICENSE',
      packages=['flask_apidoc'],
      package_data  = {
            "flask_apidoc": ["*.html"],
      },
      install_requires=[
          'flask',
      ],
      entry_points = {
        'console_scripts': ['fkapidoc=flask_apidoc.generator:main'],
      },
      zip_safe=False)