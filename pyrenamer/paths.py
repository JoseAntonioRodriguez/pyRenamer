# Copyright (C) 2006-2007 Adolfo González Blázquez <code@infinicode.org>
# Copyright (C) 2022 Jose Antonio Rodríguez Fernández <joseantonio.rguez.fdez@gmail.com>
#
# This file is part of pyRenamer.
#
# pyRenamer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyRenamer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyRenamer. If not, see <https://www.gnu.org/licenses/>.

import os.path
from pathlib import Path


def is_relative_to(this, other):
    try:
        Path(this).relative_to(other)
        return True
    except ValueError:
        return False


def validate_root_dir(root_dir, must_be_absolute=False):
    if root_dir == "":
        raise ValueError("root_dir cannot be an empty string.")

    root_dir = Path(root_dir)

    if must_be_absolute and not root_dir.is_absolute():
        raise ValueError("root_dir must be an absolute path.")

    try:
        if not root_dir.is_dir():
            raise ValueError("root_dir must be an existing directory.")
    except PermissionError:
        raise ValueError("root_dir must be an accessible directory.")

    # We are not using Path.resolve() here to avoid resolving symbolic links
    return os.path.abspath(root_dir)


def validate_active_dir(active_dir, root_dir, must_be_absolute=False):
    if active_dir == "" or root_dir == "":
        raise ValueError("active_dir and root_dir cannot be an empty string.")

    active_dir = Path(active_dir)

    if must_be_absolute and not active_dir.is_absolute():
        raise ValueError("active_dir must be an absolute path.")

    try:
        if not active_dir.is_dir():
            raise ValueError("active_dir must be an existing directory.")
    except PermissionError:
        raise ValueError("active_dir must be an accessible directory.")

    if not is_relative_to(os.path.abspath(active_dir), os.path.abspath(root_dir)):
        raise ValueError("active_dir must be a subdirectory of root_dir.")

    # We are not using Path.resolve() here to avoid resolving symbolic links
    return os.path.abspath(active_dir)

