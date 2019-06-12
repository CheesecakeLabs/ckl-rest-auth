import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='cklauth',
    version='0.4.0',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',
    description='An opinionated Django app to provide user authentication.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/CheesecakeLabs/ckl-rest-auth',
    author='Cheesecake Labs',

    install_requires=[
        'Django >= 2.1',
        'djangorestframework >= 3.9',
        'django-cors-headers >= 3.0',
        'requests >= 2.18'
    ],

    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
