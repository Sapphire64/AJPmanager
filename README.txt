AJPmanager README
==================

Goals of the project
---------------
Develop tool for easy installation of Xen VMs from presets.
Presets are packages containing all configuration files (for Xen, for OS, for additional software to install).

Software:
  - Python 2.7 (not 3.2 because of python-xenapi)
  - Pyramid framework
  - Kickstrap HTML/CSS framework
  - JQuery AJAX
  - Optional: Redis for storing settings and users


Difficulties (Help needed!)
---------------
1) Integration with Xen via XenAPI.
2) Development of package manager with optimal architecture:
    - usage of special config files with autosetup (like autoanswer in debian installation)
    - automatical installation and configuration of the optional packages

Getting Started
---------------
To make this project run:

- cd <directory containing this file>

- $venv/bin/python setup.py develop

- $venv/bin/pserve development.ini

- browse to http://127.0.0.1:8081

