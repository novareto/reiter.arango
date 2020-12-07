import os
from setuptools import setup, find_packages


version = "0.1"

install_requires = [
    'pyarango',
    'pydantic',
]

test_requires = [
    'pytest',
    'docker',
]


setup(
    name='reiter.arango',
    version=version,
    author='Souheil CHELFOUH',
    author_email='trollfot@gmail.com',
    url='http://gitweb.dolmen-project.org',
    download_url='http://pypi.python.org/pypi/reiter.arango',
    description='Arango Models implementation for Horseman',
    long_description=(open("README.txt").read() + "\n" +
                      open(os.path.join("docs", "HISTORY.txt")).read()),
    license='ZPL',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python:: 3 :: Only',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['reiter',],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'test': test_requires,
    },
    entry_points={
       'pytest11': [
           'standard = fixtures',
           'arangodb = fixtures.arangodb',
       ],
    },
)
