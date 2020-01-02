# Copyright (C) 2018 Arrai Innovations Inc. - All Rights Reserved
from setuptools import setup
from extraneous import __version__

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as req:
    setup(
        name='extraneous',
        url='https://github.com/arrai-innovations/extraneous/',
        version=__version__,
        description='Find extraneous pip packages not listed in your requirements.txt or as a sub-dependency.',
        long_description=long_description,
        long_description_content_type='text/markdown',
        author='Arrai Innovations',
        author_email='support@arrai.com',
        packages=['extraneous'],
        scripts=['extraneous/extraneous.py'],
        install_requires=[x for x in req.read().split('\n') if x],
        license='LICENSE',
        test_suite='tests',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'License :: OSI Approved :: BSD License',
            'Environment :: Console',
            'Intended Audience :: Developers',
        ]
    )
