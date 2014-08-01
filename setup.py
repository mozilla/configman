import codecs
import os
from setuptools import setup


# Prevent spurious errors during `python setup.py test`, a la
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html:
try:
    import multiprocessing
except ImportError:
    pass


def read(fname):
    fpath = os.path.join(os.path.dirname(__file__), fname)
    with codecs.open(fpath, 'r', 'utf8') as f:
        return f.read().strip()


def find_install_requires():
    return [x.strip() for x in
            read('requirements.txt').splitlines()
            if x.strip() and not x.startswith('#')]


def find_tests_require():
    return [x.strip() for x in
            read('test-requirements.txt').splitlines()
            if x.strip() and not x.startswith('#')]


setup(
    name='configman',
    version=read('configman/version.txt'),
    description=(
        'Flexible reading and writing of namespaced configuration options'
    ),
    long_description=read('README.md'),
    author='K Lars Lohn, Peter Bengtsson',
    author_email='lars@mozilla.com, peterbe@mozilla.com',
    url='https://github.com/mozilla/configman',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'Environment :: Console',
    ],
    packages=['configman'],
    package_data={'configman': ['*/*', 'version.txt']},
    install_requires=find_install_requires(),
    tests_require=find_tests_require(),
    test_suite='nose.collector',
    zip_safe=False,
),
