# -*- coding: utf-8 -*-

"""
Copyright (C) 2006-07 Adolfo González Blázquez <code@infinicode.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

If you find any bugs or have any suggestions email: code@infinicode.org
"""

import pyrenamer_filefuncs as renamerfilefuncs

class PyrenamerUndo:

    def __init__(self):
        self.undo_memory = []

    def clean(self):
        self.undo_memory = []

    def add(self, original, renamed):
        self.undo_memory.append([original, renamed])

    def undo(self):
        for i in self.undo_memory:
            renamerfilefuncs.rename_file(i[1], i[0])
            print "Undo: %s -> %s" % (i[1] , i[0])

    def redo(self):
        for i in self.undo_memory:
            renamerfilefuncs.rename_file(i[0], i[1])
            print "Redo: %s -> %s" % (i[0] , i[1])