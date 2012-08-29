You need to copy libvirt's site-packages folder into your virtualenv:

    cp libs/site-packages/* $venv/local/lib/python{X}.{Y}/site-packages/

Or you can install libvirt to your system if you are not using virtualenv:

    For Debian: aptitude install python-libvirt