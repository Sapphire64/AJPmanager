AJPmanager
==================

.. image:: https://user-images.githubusercontent.com/1443567/46786148-4b4b0000-cd34-11e8-9742-ddd4c41fb7e9.png

Goals of the project
---------------

1. Easy installation of VMs from presets.
2. Easy use of VM terminal or desktop via web interface remotely (including from mobile devices).
3. Make possible to grant rights to control selected VMs to remote users.
4. Make this app friendly for educational process.

What is done
--------------
1) Complete AJAX-powered interface
2) Integration with QEMU-KVM
3) Permissions model with per-user allowed machines control, admins and moderators roles (as supervisors)
4) Start & Stop of virtual machines
5) Installation of new machines from presets with new processed config files
6) Complex VNC client integration with permissions check


Presets
---------------
Presets are packages containing all configuration files (for VM manager, for OS, for additional software).

Groups structure
---------------
In AJPmanager we have 3 types of groups:

- admins
- moderators
- rest of the users with any other group name

Admins have all the rights of moderators, but they are extended with ability to create
moderators accounts, other administrators and so on. Both admins and moderators can
spy for other users' VM sessions (see `Application in the education process <https://github.com/Sapphire64/AJPmanager/tree/users#application-in-the-educational-process>`_), both can
make new users, new users groups, new VMs, grant permissions to VMs to users etc.
Regular users are able to control granted VMs, see their terminal, see users list.

Software
---------------

  - Python 2.7 (not 3.2 because of python-xenapi and python-libvirt)
  - Pyramid framework + AJAJ JQuery
  - Kickstrap HTML/CSS framework
  - Redis as storage and caching utility

Application in the educational process
---------------
Mostly, this software was developed for university's purposes as the part of the master's thesis.
Technical stuff (admins) create user accounts for teachers (moderators), and teachers will make
accounts for students. Teachers also can make as many VMs as they wish for students so they can
work in separated environment. Each moment teacher can connect to student's VM to help or to check the results.

Difficulties (Help needed!)
---------------
1) Integration with Xen (via xenapi or via libvirt). We need people who will test it.
2) Development of package manager with optimal architecture:
    - usage of special config files with autosetup (like autoanswer in debian installation)
    - automatical installation and configuration of the optional packages
3) General project testing on different environments.
4) General code fixes

Current packages management
---------------
For the moment we are using complete VM images and copy them to new machine.
Our program will generate unique config file (with random UUID and MAC) for new machine.
We are storing VMs in ``/kvm/presets/`` (by default). This can be updated in manager's settings.
Each folder inside of the path is a machine's preset.

Filestructure of image named **base**:

/kvm/presets/base:
  - image.img
  - config.xml
  - description.txt << this going to be converted to `.html` in future releases

New images are moving into unique folder in ``/kvm/images/``.

Each machine in preset folder have autoupdater script for boot time, 
so for keeping machines up to date server will launch them from time to time.

This is not the best choice for package management so we hope somebody can help us make it better.

TODO
--------------
1) Full test coverage
2) SSL
3) Package for much easier installation of the manager
4) Machines pause :)
5) Clone non-presetted machines, save state, detailed machine info
6) Friendly interface for screens with resolution less than 1280x720
7) VNC screen size adjustments
8) VM rooms to separate physical hardware for classroomes (far future)

Requirements
---------------
  - Python 2.7 (not tested with earlier versions)
  - virtualenv
  - Redis DB
  - Anything other will be installed into virtualenv automatically (except libvirt, see `Gettings Started <https://github.com/Sapphire64/AJPmanager/tree/users#getting-started>`_)

Getting Started
---------------
To make this project run:

- cd <directory containing this file>

- cp libs/site-packages/* $venv/local/lib/python{X}.{Y}/site-packages/

- $venv/bin/python setup.py develop

- $venv/bin/python ajpmanager/scripts/initialize_redis.py

- $venv/bin/pserve development.ini

- browse to http://127.0.0.1:8081

Please note, we are copying libvirt packages to your python distribution because they cannot be installed by PYPI.
