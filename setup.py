import os
from distutils.core import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read().strip()


setup(
    name='configman',
    version=read('configman/version.txt'),
    description='Flexible reading and writing of namespaced configuration options',
    long_description=read('README.md'),
    author='Lars Lohn, Peter Bengtsson',
    author_email='lars@mozilla.com, peterbe@mozilla.com',
    url='https://github.com/twobraids/configman',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Environment :: Console',
    ],
    packages=['configman'],
    package_data={'configman': ['*/*', 'version.txt']},
    scripts=[],
    zip_safe=False,
),
