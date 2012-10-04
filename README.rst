AJPmanager
==================

Goals of the project
---------------
Develop tool for:
1) Easy installation of VMs from presets.
2) Easy use of VM terminal or desktop via web interface remotely (including from mobile devices).
3) Make possible to grant rights to control VMs to remote users.

Presets
---------------
Presets are packages containing all configuration files (for VM manager, for OS, for additional software).

Groups structure
---------------
In AJPmanager we have 3 types of groups:
* admins
* moderators
* rest of the users with any other group name
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
Mostly, this software is developed for education purposes. Technical stuff (admins)
create user accounts for teachers (moderators), and teachers will make accounts for students.
Teachers also can make as many VMs as they wish for students so they can work in separated
environment. Each moment teacher can connect to student's VM to help or to check the results.

Difficulties (Help needed!)
---------------
1) Integration with Xen (via xenapi or via libvirt). We need people who will test it.
2) Development of package manager with optimal architecture:
    - usage of special config files with autosetup (like autoanswer in debian installation)
    - automatical installation and configuration of the optional packages

Current packages management
---------------
For the moment we are using complete VM images and copy them to new machine.
Our program will generate unique config file (with random UUID and MAC) for new machine.
We are storing VMs in `/kvm/presets/` (default). This can be updated in manager's settings.
Each folder inside of the path is a machine's preset.

Filestructure of image named `base`:
/kvm/presets/base:
  - image.img
  - config.xml
  - description.txt << this going to be converted to `.html` in future releases

New images are moving into unique folder in `/kvm/images/`.

Each machine in preset folder have autoupdater script for boot time, 
so for keeping machines up to date server will launch them from time to time.

This is not the best choice for package management so we hope somebody can help us make it better.

TODO
--------------
1) Testings
2) VM rooms to separate physical hardware for classroomes (far future)

Requirements
---------------
  - Python 2.7 (not tested with earlier versions)
  - virtualenv
  - Redis DB
  - Anything other will be installed into virtualenv automatically (except libvirt, see `Gettings Started<https://github.com/Sapphire64/AJPmanager/tree/users#getting-started>`_`)

Getting Started
---------------
To make this project run:

- cd <directory containing this file>

Libvirt library can't be installed from PYPI:
- cp libs/site-packages/* $venv/local/lib/python{X}.{Y}/site-packages/

- $venv/bin/python setup.py develop

- $venv/bin/pserve development.ini

- browse to http://127.0.0.1:8081

