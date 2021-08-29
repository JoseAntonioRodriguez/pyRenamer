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

try:
    import gconf
    HAS_GCONF = True
except:
    HAS_GCONF = False

from os import path as ospath

import pyrenamer_globals as pyrenamerglob

from gettext import gettext as _

class PyrenamerPrefs:

    def __init__(self, main):

        self.main = main

        self.gconf_path = '/apps/' + pyrenamerglob.name
        self.gconf_root_dir = self.gconf_path + '/root_dir'
        self.gconf_active_dir = self.gconf_path + '/active_dir'
        self.gconf_window_maximized = self.gconf_path + '/window_maximized'
        self.gconf_pane_position = self.gconf_path + '/pane_position'
        self.gconf_window_width = self.gconf_path + '/window_width'
        self.gconf_window_height = self.gconf_path + '/window_height'
        self.gconf_window_posx = self.gconf_path + '/window_posx'
        self.gconf_window_posy = self.gconf_path + '/window_posy'
        self.gconf_options_shown = self.gconf_path + '/options_shown'
        self.gconf_filedir = self.gconf_path + '/filedir'
        self.gconf_keepext = self.gconf_path + '/keepext'
        self.gconf_autopreview  = self.gconf_path + '/autopreview'


    def create_preferences_dialog(self):
        """ Create Preferences dialog and connect signals """

        # Create the window
        self.preferences_tree = gtk.glade.XML(pyrenamerglob.gladefile, "prefs_window")

        # Get text entries and buttons
        self.prefs_window = self.preferences_tree.get_widget('prefs_window')
        self.prefs_entry_root = self.preferences_tree.get_widget('prefs_entry_root')
        self.prefs_entry_active = self.preferences_tree.get_widget('prefs_entry_active')
        self.prefs_browse_root = self.preferences_tree.get_widget('prefs_browse_root')
        self.prefs_browse_active = self.preferences_tree.get_widget('prefs_browse_active')
        self.prefs_close = self.preferences_tree.get_widget('prefs_close')

        # Signals
        signals = {
                   "on_prefs_browse_root_clicked": self.on_prefs_browse_root_clicked,
                   "on_prefs_browse_active_clicked": self.on_prefs_browse_active_clicked,
                   "on_prefs_close_clicked": self.on_prefs_close_clicked,
                   "on_prefs_window_destroy": self.on_prefs_destroy,
                   }
        self.preferences_tree.signal_autoconnect(signals)

        # Fill the panel with gconf values or actual values (if gconf is empty)
        client = gconf.client_get_default()
        root_dir = client.get_string(self.gconf_root_dir)
        if root_dir == (None or ''): root_dir = self.main.root_dir
        active_dir = client.get_string(self.gconf_active_dir)
        if active_dir == (None or ''): active_dir = self.main.active_dir
        self.prefs_entry_root.set_text(root_dir)
        self.prefs_entry_active.set_text(active_dir)

        # Set prefs window icon
        self.prefs_window.set_icon_from_file(pyrenamerglob.icon)


    def on_prefs_browse_root_clicked(self, widget):
        """ Browse root clicked """
        f = gtk.FileChooserDialog(_('Select root directory'),
                                  self.prefs_window,
                                  gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                                   )
        f.set_current_folder(self.prefs_entry_root.get_text())
        response = f.run()
        if response == gtk.RESPONSE_ACCEPT:
            self.prefs_entry_root.set_text(f.get_filename())
        elif response == gtk.RESPONSE_REJECT:
            pass
        f.destroy()


    def on_prefs_browse_active_clicked(self, widget):
        """ Browse active clicked """
        f = gtk.FileChooserDialog(_('Select active directory'),
                                  self.prefs_window,
                                  gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                                   )
        f.set_current_folder(self.prefs_entry_active.get_text())
        response = f.run()
        if response == gtk.RESPONSE_ACCEPT:
            self.prefs_entry_active.set_text(f.get_filename())
        elif response == gtk.RESPONSE_REJECT:
            pass
        f.destroy()


    def on_prefs_close_clicked(self, widget):
        """ Prefs close button clicked """

        root = self.prefs_entry_root.get_text()
        active = self.prefs_entry_active.get_text()
        if root != "" and active != "":
            if not self.check_root_dir(root):
                self.display_error_dialog(_("\nThe root directory is not valid!\nPlease select another directory."))
                self.prefs_entry_root.set_text('/')
            elif not self.check_active_dir(root, active):
                self.main.display_error_dialog(_("\nThe active directory is not valid!\nPlease select another directory."))
                self.prefs_entry_active.set_text(root)
            else:
                self.main.root_dir = root
                self.main.active_dir = active
                self.prefs_window.destroy()
                self.preferences_save_dirs()
        else:
            self.main.display_error_dialog(_("\nPlease set both directories!"))
            if root == '': self.prefs_entry_root.set_text(self.main.root_dir)
            if active == '': self.prefs_entry_active.set_text(self.main.active_dir)


    def on_prefs_destroy(self, widget):
        """ Prefs window destroyed """

        root = self.prefs_entry_root.get_text()
        active = self.prefs_entry_active.get_text()
        if root != "" and active != "":
            if not self.check_root_dir(root):
                self.main.display_error_dialog(_("\nThe root directory is not valid!\nPlease select another directory."))
                self.create_preferences_dialog()
                self.prefs_entry_root.set_text('/')
            elif not self.check_active_dir(root, active):
                self.main.display_error_dialog(_("\nThe active directory is not valid!\nPlease select another directory."))
                self.create_preferences_dialog()
                self.prefs_entry_active.set_text(root)
            else:
                self.main.root_dir = root
                self.main.active_dir = active
                self.prefs_window.destroy()
                self.preferences_save_dirs()
        else:
            self.main.display_error_dialog(_("\nPlease set both directories!"))
            self.create_preferences_dialog()
            if root == '': self.prefs_entry_root.set_text(self.main.root_dir)
            if active == '': self.prefs_entry_active.set_text(self.main.active_dir)


    def on_add_recursive_toggled(self, widget):
        """ Reload current dir, but with Recursive flag enabled """
        self.main.dir_reload_current()

    def on_filedir_combo_changed(self, combo):
        filedir = combo.get_active()
        self.main.filedir = filedir
        self.main.dir_reload_current()

    def on_extensions_check_toggled(self, check):
        self.main.keepext = check.get_active()

    def on_autopreview_check_toggled(self, check):
        self.main.autopreview = check.get_active()

    def check_root_dir(self, root):
        """ Checks if the root dir is correct """
        return ospath.isdir(ospath.abspath(root))


    def check_active_dir(self, root, active):
        """ Checks if active dir is correct """
        root = ospath.abspath(root)
        active = ospath.abspath(active)
        return ospath.isdir(active) and (root in active)


    def preferences_save(self):
        """ Width and height are saved on the configure_event callback for main_window """
        client = gconf.client_get_default()
        client.set_int(self.gconf_pane_position, self.main.pane_position)
        client.set_bool(self.gconf_window_maximized, self.main.window_maximized)
        client.set_int(self.gconf_window_width, self.main.window_width)
        client.set_int(self.gconf_window_height, self.main.window_height)
        client.set_int(self.gconf_window_posx, self.main.window_posx)
        client.set_int(self.gconf_window_posy, self.main.window_posy)
        client.set_bool(self.gconf_options_shown, self.main.options_shown)
        client.set_int(self.gconf_filedir, self.main.filedir)
        client.set_bool(self.gconf_keepext, self.main.keepext)
        client.set_bool(self.gconf_autopreview, self.main.autopreview)


    def preferences_save_dirs(self):
        """ Save default directories """
        client = gconf.client_get_default()
        client.set_string(self.gconf_root_dir, self.main.root_dir)
        client.set_string(self.gconf_active_dir, self.main.active_dir)

    def preferences_read(self):
        """ The name says it all... """
        client = gconf.client_get_default()

        root_dir = client.get_string(self.gconf_root_dir)
        if root_dir != None and root_dir != '': self.main.root_dir = root_dir

        active_dir = client.get_string(self.gconf_active_dir)
        if active_dir != None and active_dir != '': self.main.active_dir = active_dir

        pane_position = client.get_int(self.gconf_pane_position)
        if pane_position != None: self.main.pane_position = pane_position

        maximized = client.get_bool(self.gconf_window_maximized)
        if maximized != None: self.main.window_maximized = maximized

        width = client.get_int(self.gconf_window_width)
        height = client.get_int(self.gconf_window_height)
        if width != None and height != None:
            self.main.window_width = width
            self.main.window_height = height

        posx = client.get_int(self.gconf_window_posx)
        posy = client.get_int(self.gconf_window_posy)
        if posx != None and posy != None:
            self.main.window_posx = posx
            self.main.window_posy = posy

        options_shown = client.get_bool(self.gconf_options_shown)
        if options_shown != None: self.main.options_shown = options_shown

        filedir = client.get_int(self.gconf_filedir)
        if filedir != None: self.main.filedir = filedir

        keepext = client.get_bool(self.gconf_keepext)
        if keepext != None: self.main.keepext = keepext

        autopreview = client.get_bool(self.gconf_autopreview)
        if autopreview != None: self.main.autopreview = autopreview
