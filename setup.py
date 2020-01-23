import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-etesync-journal',
    version='1.2.0',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    license='AGPL-3.0-only',
    description='The server side implementation of the EteSync protocol.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://www.etesync.com/',
    author='EteSync',
    author_email='development@etesync.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
