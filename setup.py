#!/usr/bin/env python

version = '0.1'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='redisco',
      version=version,
      description='Containers and Simple Model for Redis',
      url='http://github.com/iamteem/redisco',
      download_url='',
      author='Tim Medina',
      author_email='iamteem@gmail.com',
      maintainer='Tim Medina',
      maintainer_email='iamteem@gmail.com',
      keywords=['Redis', 'model'],
      license='MIT',
      packages=['redisco'],
      test_suite='tests.all_tests',
      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'],
    )

