# -*- coding: utf-8 -*-

"""
Copyright (C) 2006-2008 Adolfo González Blázquez <code@infinicode.org>

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

import TreeViewTooltips as tvt
from gettext import gettext as _

class ToolTips(tvt.TreeViewTooltips):

    def __init__(self,column):
        self.column = column
        tvt.TreeViewTooltips.__init__(self)


    def get_tooltip(self, view, column, path):

        model = view.get_model()
        oldpath = model[path][1]
        newpath = model[path][3]
        if newpath != None:
        	return _("<b>Original: </b> %s\n<b>Renamed: </b> %s") % (oldpath, newpath)
        else:
        	return _("<b>Original: </b> %s") % oldpath
        	
        """if column is self.column:
            filepath = model[path][3]
            return '<b>New filename: </b> %s' % filepath
        else:
            filepath = model[path][1]
            return '<b>Original filename: </b> %s' % filepath"""
