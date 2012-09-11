import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'transaction',
    'pyramid_beaker',
    'pyramid_jinja2',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'redis',
    'beaker_extensions',
    'passlib',
    'py-bcrypt'
    'waitress',
    ]

setup(name='ajpmanager',
      version='0.1',
      description='ajpmanager',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi pylons pyramid libvirt',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='ajpmanager',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = ajpmanager:main
      [console_scripts]
      initialize_ajpmanager_db = ajpmanager.scripts.initializedb:main
      """,
      )

