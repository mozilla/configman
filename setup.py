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


setup(
    name='configman',
    version=read('configman/version.txt'),
    description='Flexible reading and writing of namespaced configuration options',
    long_description=read('README.md'),
    author='K Lars Lohn, Peter Bengtsson',
    author_email='lars@mozilla.com, peterbe@mozilla.com',
    url='https://github.com/mozilla/configman',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Environment :: Console',
    ],
    packages=['configman'],
    package_data={'configman': ['*/*', 'version.txt']},
    tests_required=['nose'],
    test_suite='nose.collector',
    zip_safe=False,
),
