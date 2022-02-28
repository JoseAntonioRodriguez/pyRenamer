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

import os
import errno
from contextlib import suppress


class Renamer:
    def __init__(self):
        self._renamed_files = []
        self._undoable = False
        self._redoable = False

    @property
    def undoable(self):
        return self._undoable

    @property
    def redoable(self):
        return self._redoable

    def clear(self):
        self._renamed_files.clear()
        self._undoable = False
        self._redoable = False

    def rename(self, original, renamed):
        self._rename(original, renamed)
        self._renamed_files.append((original, renamed))
        self._undoable = True

    def undo(self):
        if not self._undoable:
            return

        with suppress(OSError):
            for original, renamed in self._renamed_files:
                self._rename(renamed, original)
        self._undoable = False
        self._redoable = True

    def redo(self):
        if not self._redoable:
            return

        with suppress(OSError):
            for original, renamed in self._renamed_files:
                self._rename(original, renamed)
        self._redoable = False
        self._undoable = True

    @staticmethod
    def _rename(old, new):
        if old and new and old != new:
            if os.path.exists(new):
                raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), new)
            os.renames(old, new)
