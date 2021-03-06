from setuptools import setup, find_packages
import btclib

with open('README.md', 'r') as fh:
    longdescription = fh.read()

setup(
    name=btclib.name,
    version=btclib.__version__,
    url='https://btclib.org',
    license=btclib.__license__,
    author=btclib.__author__,
    description="A library for 'bitcoin cryptography'.",
    long_description=longdescription,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "btclib": ["dictdata/*", "tests/data/*"],
    },
    test_suite="btclib.tests",
    keywords=('bitcoin cryptography elliptic-curves ecdsa schnorr RFC-6979 '
              'bip32 bip39 electrum base58 bech32 segwit message-signing '
              'bip340'
              ),
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',

        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',

        'License :: OSI Approved :: MIT License',

        'Natural Language :: English',

        'Operating System :: OS Independent',

        'Topic :: Security :: Cryptography',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
