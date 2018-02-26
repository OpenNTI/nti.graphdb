import codecs
from setuptools import setup 
from setuptools import find_packages

entry_points = {
	'z3c.autoinclude.plugin': [
		'target = nti.dataserver',
	],
	'console_scripts': [
		"nti_graph_constructor = nti.graphdb.utils.constructor:main",
	],
}

TESTS_REQUIRE = [
	'fudge',
    'nti.testing',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.graphdb',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI Graph Database",
    long_description=(
        _read('README.rst') 
        + '\n\n' 
        + _read("CHANGES.rst")
    ),
    license='Apache',
    keywords='graph database',
    classifiers=[
        'Framework :: Zope3',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/NextThought/nti.graphdb",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
		'setuptools',
		'neo4j_driver',
		'nti.assessment',
		'nti.asynchronous',
		'nti.base',
		'nti.contentlibrary',
		'nti.contenttypes.courses',
		'nti.contenttypes.presentation',
		'nti.coremetadata',
		'nti.externalization',
		'nti.ntiids',
		'nti.property',
		'nti.schema',
		'six',
		'zope.cachedescriptors',
		'zope.component',
		'zope.configuration',
		'zope.interface',
		'zope.intid',
		'zope.lifecycleevent',
		'zope.schema',
		'zope.security',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points=entry_points,
)
