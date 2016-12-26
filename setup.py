# coding=utf8
__author__ = 'liming'

from setuptools import setup

setup(name='flask_doc',
      version='0.0.2',
      description='generate api-documentation from doc string',
      url='https://github.com/ipconfiger/flask-apidoc',
      author='Alexander.Li',
      author_email='superpowerlee@gmail.com',
      license='GNU GENERAL PUBLIC LICENSE',
      packages=['flask_doc'],
      package_data = {
            "flask_doc": ["*.html"],
      },
      install_requires=[
          'flask',
      ],
      entry_points = {
        'console_scripts': ['fkapidoc=flask_doc.generator:main'],
      },
      zip_safe=False)