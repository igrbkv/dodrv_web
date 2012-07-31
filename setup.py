
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

#datafiles=[('/etc/dodrv', ['htpasswd', 'filters.conf']),]
packagedir={'doweb': ''}
packagedata={'doweb': ['static/*.css', 'static/*.png', 'static/*.ico',
    'templates/*.html', 'templates/*.xml']}

setup(name='doweb',
    version='0.0.0',
    packages=['doweb'],
    package_dir=packagedir,
    package_data=packagedata,
    data_files=datafiles,
    )
