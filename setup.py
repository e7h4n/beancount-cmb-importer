"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""


import pathlib
from setuptools import setup, find_packages
from beancmb import __version__

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='beancount-cmb-importer',

    version=__version__,

    description='A beancount importer for CMB.',

    long_description=long_description,

    long_description_content_type='text/markdown',

    url='https://github.com/e7h4n/beancount-cmb-importer',

    author='e7h4n',

    author_email='ethan.pw@icloud.com',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Office/Business :: Financial :: Accounting',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],

    keywords='beancount, importer',

    package_dir={'beancount-cmb-importer': 'src'},

    python_requires='>=3.6, <4',

    packages=find_packages(exclude=['experiments*']),

    install_requires=[
        'beancount==2.3.4',
    ],

    extras_require={
        'dev': [],
        'test': [
            'coverage',
            'pycodestyle',
            'pyflakes',
            'pylint',
            'flake8',
            'mypy',
            'pytest',
            'python-coveralls',
            'beautifulsoup4'
        ],
    },

project_urls={
    'Bug Reports': 'https://github.com/e7h4n/beancount-cmb-importer/issues',
    'Source': 'https://github.com/e7h4n/beancount-cmb-importer/',
},
)
