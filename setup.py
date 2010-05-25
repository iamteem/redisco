#!/usr/bin/env python

version = '0.1.dev5'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='redisco',
      version=version,
      description='Python Containers and Simple Models for Redis',
      url='http://github.com/iamteem/redisco',
      download_url='',
      long_description=open('README.rst').read(),
      author='Tim Medina',
      author_email='iamteem@gmail.com',
      maintainer='Tim Medina',
      maintainer_email='iamteem@gmail.com',
      keywords=['Redis', 'model', 'container'],
      license='MIT',
      packages=['redisco', 'redisco.models'],
      test_suite='tests.all_tests',
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'],
    )

