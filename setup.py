#!/usr/bin/python
import sys
from setuptools import setup
import django_crud

description = 'CRUD controllers for django: Create, Retrieve, Update, Delete, List'
long_description = description
if 'upload' in sys.argv:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')

setup(
    name='django_crud',
    version=django_crud.__version__,
    description=description,
    long_description=long_description,
    author='Samuel Colvin',
    license='MIT',
    author_email='S@muelColvin.com',
    url='https://github.com/samuelcolvin/django_crud',
    packages=['django_crud'],
    platforms='any',
    install_requires=[
        'django>=1.8',
        'django-jinja>=1.4.1',
        'django-jinja-bootstrap-form>=4.1.1',
    ],
    keywords=(
        'Python, django, CRUD, BREAD, Controllers,'
        'Create, Retrieve, Update, Delete, List'
    ),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Environment :: Web Environment',
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8'
    ],
)
