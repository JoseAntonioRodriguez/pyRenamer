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

try:
    import pygtk
    pygtk.require('2.0')
except:
      print "PyGtk 2.0 or later required for this app to run"
      raise SystemExit

try:
    import gtk
    import gtk.glade
    import gobject
except:
    raise SystemExit

import pyrenamer_globals as pyrenamerglob

from gettext import gettext as _
import os

class PyrenamerPatternEditor:

    def __init__(self, main):

        self.main = main

        # Check if config directory exists
        self.config_dir = os.path.join(pyrenamerglob.config_dir, 'patterns')
        if not os.path.isdir(self.config_dir):
            os.makedirs(self.config_dir)


    def get_patterns(self, selector):

        patterns = []

        default_patterns = {
            "main_ori": "{X}\n",
            "main_dest": "{1}\n",
            "images_ori": "{X}\n",
            "images_dest": "{1}\n" \
                           "{imageyear}{imagemonth}{imageday}_{imagetime}_{1}\n" \
                           "{imagewidth}x{imageheight}_{1}\n",
            "music_ori": "{X}\n",
            "music_dest": "{1}\n" \
                          "{track} - {artist} ({album}) - {title}\n" \
                          "{track} - {artist}\n",
                            }

        config_file = os.path.join(self.config_dir, selector)

        # If the config file doesn't exist, create it with default options
        if not os.path.isfile(config_file):
            f = open(config_file, 'w')
            try:
                f.write(default_patterns[selector])
            finally:
                f.close()

        # Read patterns from file
        f = open(config_file, 'r')
        try:
            for line in f:
                line = line.rstrip("\r\n")
                patterns.append(line)
        finally:
            f.close()

        # Return found patterns
        if patterns == []:
            if "ori" in selector: patterns.append('{X}')
            else: patterns.append('{1}')
        return patterns


    def save_patterns(self, selector):

        config_file = os.path.join(self.config_dir, selector)
        f = open(config_file, 'w')
        iter = self.model.get_iter_first()
        try:
            while iter != None:
                val = self.model.get_value(iter, 0)
                f.write(val + "\n")
                iter = self.model.iter_next(iter)
        finally:
            f.close()


    def add_pattern(self, selector, pattern):

        config_file = os.path.join(self.config_dir, selector)
        f = open(config_file, 'a')
        try:
            f.write(pattern + "\n")
        finally:
            f.close()


    def create_window(self, selector):
        """ Create pattern editor dialog and connect signals """

        # Save the selector for the future
        self.selector = selector

        # Create the window
        self.pattern_edit_tree = gtk.glade.XML(pyrenamerglob.gladefile, "pattern_edit_window")

        # Get widgets
        self.pattern_edit_window = self.pattern_edit_tree.get_widget('pattern_edit_window')
        self.pattern_edit_treeview = self.pattern_edit_tree.get_widget('pattern_edit_treeview')

        # Signals
        signals = {
                   "on_pattern_edit_add_clicked": self.on_pattern_edit_add_clicked,
                   "on_pattern_edit_del_clicked": self.on_pattern_edit_del_clicked,
                   "on_pattern_edit_edit_clicked": self.on_pattern_edit_edit_clicked,
                   "on_pattern_edit_up_clicked": self.on_pattern_edit_up_clicked,
                   "on_pattern_edit_down_clicked": self.on_pattern_edit_down_clicked,
                   "on_pattern_edit_close_clicked": self.on_prefs_close_clicked,
                   "on_pattern_edit_treeview_button_press_event": self.on_pattern_edit_treeview_button_press_event,
                   "on_pattern_edit_window_destroy": self.on_pattern_edit_destroy,
                   }
        self.pattern_edit_tree.signal_autoconnect(signals)

        # Set prefs window icon
        self.pattern_edit_window.set_icon_from_file(pyrenamerglob.icon)

        # Set window name
        if 'main' in selector:
            self.pattern_edit_window.set_title(_('Patterns editor'))
        elif 'images' in selector:
            self.pattern_edit_window.set_title(_('Image patterns editor'))
        elif 'music' in selector:
            self.pattern_edit_window.set_title(_('Music patterns editor'))

        self.populate_treeview(selector)


    def populate_treeview(self, selector):

        # Get data from main variable
        if selector == "main_ori":
            data = self.main.patterns["main_ori"]
        elif selector == "main_dest":
            data = self.main.patterns["main_dest"]
        elif selector == "images_ori":
            data = self.main.patterns["images_ori"]
        elif selector == "images_dest":
            data = self.main.patterns["images_dest"]
        elif selector == "music_ori":
            data = self.main.patterns["music_ori"]
        elif selector == "music_dest":
            data = self.main.patterns["music_dest"]

        # Create model
        self.model = gtk.ListStore(gobject.TYPE_STRING)
        for p in data:
            self.model.append([p])
        self.pattern_edit_treeview.set_model(self.model)

        # Draw treeview
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('edited', self.on_cell_edited, self.model)
        column = gtk.TreeViewColumn("Pattern",renderer, text=0)
        self.pattern_edit_treeview.append_column(column)
        self.pattern_edit_treeview.set_headers_visible(False)


    def on_cell_edited(self, cell, path, new_text, model):
        iter = model.get_iter(path)
        model.set_value(iter, 0, new_text)

    def on_pattern_edit_add_clicked(self, widget):

        # Run add dialog and get data
        dialog, entry = self.create_add_dialog()
        output = dialog.run()

        if output == 1:
            data = entry.get_text()
            dialog.destroy()
        else:
            dialog.destroy()
            return False

        if data == None or data == '':
            return False

        # Add the data
        selection = self.pattern_edit_treeview.get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            iter = model.insert_after(iter, [data])
        else:
            iter = model.append([data])

        selection.select_iter(iter)


    def on_pattern_edit_del_clicked(self, widget):
        selection = self.pattern_edit_treeview.get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            iter = model.remove(iter)
        else:
            return



    def on_pattern_edit_edit_clicked(self, widget):

        # Get data from treeview
        selection = self.pattern_edit_treeview.get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            data = model.get_value(iter, 0)
        else:
            return False

        # Run edit dialog
        dialog, entry = self.create_add_dialog()
        entry.set_text(data)
        output = dialog.run()

        if output == 1:
            data = entry.get_text()
            dialog.destroy()
        else:
            dialog.destroy()
            return False

        if data == None or data == '':
            return False

        # Edit the data
        model.set_value(iter, 0, data)


    def on_pattern_edit_up_clicked(self, widget):
        model, iter = self.pattern_edit_treeview.get_selection().get_selected()
        iter_prev = self.iter_prev(model, iter)
        if iter_prev != None:
            model.swap(iter, iter_prev)


    def on_pattern_edit_down_clicked(self, widget):
        model, iter = self.pattern_edit_treeview.get_selection().get_selected()
        iter_next = model.iter_next(iter)
        if iter_next != None:
            model.swap(iter, iter_next)


    def on_prefs_close_clicked(self, widget):
        self.pattern_edit_window.destroy()


    def on_pattern_edit_destroy(self, widget):
        self.save_patterns(self.selector)
        self.main.populate_pattern_combos()


    def on_pattern_edit_treeview_button_press_event(self, widget, event):
        """ If clicked in a clean part of the listview, unselect all rows """
        x, y = event.get_coords()
        if self.pattern_edit_treeview.get_path_at_pos(int(x), int(y)) == None:
            self.pattern_edit_treeview.get_selection().unselect_all()


    def iter_prev(self, model, iter):
        path = model.get_string_from_iter(iter)
        if path == "0":
            return None
        prev_path = int(path) -1
        return model.get_iter_from_string(str(prev_path))


    def create_add_dialog(self,):
        """ Create pattern add dialog and connect signals """

        # Create the dialog
        tree = gtk.glade.XML(pyrenamerglob.gladefile, "add_pattern_dialog")

        # Get widgets
        dialog = tree.get_widget('add_pattern_dialog')
        entry = tree.get_widget('add_pattern_entry')

        return dialog, entry
