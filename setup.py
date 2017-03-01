
import re
import ast
from setuptools import setup


setup(
    name='Flask',
    version="0.0.1",
    license='BSD',
    author='Ali Arda Orhan',
    author_email='arda.orhan@dogantv.com.tr',
    description='A microframework based on Werkzeug, Jinja2 '
                'and good intentions',
    long_description=__doc__,
    packages=['flasky'],
    platforms='any',
    install_requires=[
        'tornado==4.4.2'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points='''
        [console_scripts]
        flask=flask.cli:main
    '''
)