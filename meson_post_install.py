#!/usr/bin/env python3

import os
from pathlib import Path
import shlex
import subprocess

prefix = Path(os.environ.get('MESON_INSTALL_PREFIX', '/usr'))
data_dir = prefix / 'share'

# Packaging tools define DESTDIR and this isn't needed for them
if 'DESTDIR' not in os.environ:
    print('Updating icon cache...')
    icon_cache_dir = str(data_dir / 'icons' / 'hicolor')
    subprocess.run(['gtk-update-icon-cache', '-qtf', shlex.quote(icon_cache_dir)], check=True)

    print("Compiling the schema...")
    schema_dir = str(data_dir / 'glib-2.0' / 'schemas')
    subprocess.run(['glib-compile-schemas', shlex.quote(schema_dir)], check=True)

    print('Updating desktop database...')
    desktop_database_dir = str(data_dir / 'applications')
    subprocess.run(['update-desktop-database', shlex.quote(desktop_database_dir)], check=True)
