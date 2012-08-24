AJPmanager README
==================

Goals of the project
---------------
Develop tool for easy installation of VMs from presets.
Presets are packages containing all configuration files (for VM manager, for OS, for additional software).

Software:
  - Python 2.7 (not 3.2 because of python-xenapi and python-libvirt)
  - Pyramid framework
  - Kickstrap HTML/CSS framework
  - JQuery AJAX
  - Optional: Redis for storing settings and users


Difficulties (Help needed!)
---------------
1) Integration with Xen via XenAPI. Or maybe it can be integrated via libvirt - we need people who will test it.
2) Development of package manager with optimal architecture:
    - usage of special config files with autosetup (like autoanswer in debian installation)
    - automatical installation and configuration of the optional packages


Current packages management
---------------
For the moment we are using complete VM images and copy them to new machine.
Our program will generate unique config file (with random UUID and MAC) for new machine.
We are storing VMs in /kvm/presets/. Each folder inside of it is a new machine preset.

Structure:
/kvm/presets/base:
  - image.img
  - config.xml
  - description.txt

New images will be moved to /kvm/images/ also in unique folder. 

Each machine in preset folder have autoupdater script for boot time, 
so for keeping machines up to date server will launch them from time to time.

---------------
This is not the best choice for package management so we hope somebody can help us make it better.
---------------


Requirements
---------------
  - Python 2.7 (not tested with earlied versions)
  - virtualenv
  - Redis DB (optional)
  - Anything other will be installed into virtualenv automatically (except libvirt)


Getting Started
---------------
To make this project run:

- cd <directory containing this file>

Libvirt library can't be installed from PYPI:
- cp libs/site-packages/* $venv/local/lib/python{X}.{Y}/site-packages/

- $venv/bin/python setup.py develop

- $venv/bin/pserve development.ini

- browse to http://127.0.0.1:8081

