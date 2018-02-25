import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'z3c.autoinclude.plugin': [
		'target = nti.dataserver',
	],
	'console_scripts': [
		"nti_graph_constructor = nti.graphdb.utils.constructor:main",
	],
}

TESTS_REQUIRE = [
	'nose',
	'nose-timer',
	'nose-pudb',
	'nose-progressive',
	'nose2[coverage_plugin]',
	'pyhamcrest',
	'zope.testing',
	'nti.nose_traceback_info',
	'nti.testing'
]

setup(
	name='nti.graphdb',
	version=VERSION,
	author='Jason Madden',
	author_email='jason@nextthought.com',
	description="NTI graphdb",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
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
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti'],
	install_requires=[
		'setuptools',
		'neo4j_driver',
		'nti.asynchronous',
		'nti.externalization',
		'nti.property',
		'nti.schema',
		'zope.component',
		'zope.configuration',
		'zope.interface',
		'zope.schema',
		'zope.security',
	],
	extras_require={
		'test': TESTS_REQUIRE,
	},
	entry_points=entry_points
)
