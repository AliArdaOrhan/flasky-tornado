from setuptools import setup


setup(
    name='FlaskyTornado',
    version="0.0.2",
    license='BSD',
    author='Ali Arda Orhan',
    author_email='arda.orhan@dogantv.com.tr',
    description='A microframework based on Tornado and Flask '
                'and good intentions',
    long_description=__doc__,
    packages=['flasky'],
    platforms='any',
    install_requires=[
        'tornado==4.4.2',
        'jsonschema==2.6.0',
        'PyJWT==1.4.2'
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
    ]
)
