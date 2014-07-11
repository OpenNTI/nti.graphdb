import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
    'console_scripts': [
        "nti_graph_constructor = nti.graphdb.utils.constructor:main",
    ],
    'z3c.autoinclude.plugin': [
        'target = nti.dataserver',
    ],
}

setup(
    name='nti.graphdb',
    version=VERSION,
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI graphdb",
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    license='Proprietary',
    keywords='pyramid preference',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        ],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti'],
	install_requires=[
		'setuptools',
        'nti.async',
        'py2neo'
	],
	entry_points=entry_points
)
