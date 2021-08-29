#!/usr/bin/env python
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

"""
This is an example on how to use treefilebrowser.py, which is a
tree-like file browser, like the one found on Nautilus.
"""

import pygtk
pygtk.require('2.0')
import gtk
from pyrenamer import treefilebrowser

def make_buttons(list):
    buttonbox = gtk.HBox()
    buttonbox.set_spacing(10)
    for label, func in list:
        button = gtk.Button()
        button.set_label(label)
        button.connect("clicked", func)
        button.show()
        buttonbox.pack_start(button, expand=False, fill=False)
    buttonbox.show()
    return buttonbox


tree = None

def show_hidden(*args):
    tree.set_show_hidden(not tree.get_show_hidden())

def show_only_dirs(*args):
    tree.set_show_only_dirs(not tree.get_show_only_dirs())
    
def show_rows(*args):
    tree.set_rules_hint(not tree.get_rules_hint())

def quit(*args):
    gtk.main_quit()
    
def selected(*args):
    print tree.get_selected()

def expanded(obj, data):
    print "expanded", data
    
def cursor(obj, data):
    print "cursor", data

def main():
    global tree
    
    root = '/'
    acti = '/home'
    
    print "Root: %s\nActive dir: %s" % (root, acti)
    
    tree = treefilebrowser.TreeFileBrowser(root)
    tree.set_active_dir(acti)
    
    tree.connect('row-expanded', expanded)
    tree.connect('cursor-changed', cursor)
    scrolled = tree.get_scrolled()

    buttonbox = make_buttons([("Toggle show hidden files", show_hidden), 
                              ("Toggle show only dirs",  show_only_dirs), 
                              ("Toggle show rows background",   show_rows),
                              ("Selected", selected),
                              ("Quit", quit)])
    
    
    vbox = gtk.VBox()
    vbox.set_border_width(10)
    vbox.set_spacing(10)
    vbox.pack_start(scrolled, expand=True, fill=True)
    vbox.pack_start(buttonbox, expand=False, fill=False)
    vbox.show()

    # Create toplevel window to show it all.
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.connect("delete_event", gtk.main_quit)
    win.add(vbox)
    win.show()
    win.resize(300, 500)
    
    # Run the Gtk+ main loop.
    gtk.main()
    
if __name__ == "__main__":
    main()