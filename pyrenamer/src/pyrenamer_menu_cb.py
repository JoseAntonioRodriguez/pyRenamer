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

class PyrenamerMenuCB:

    def __init__(self, main):
        self.main = main

    def on_menu_undo_activate(self, widget):
        self.main.undo_manager.undo()
        self.main.dir_reload_current()
        self.main.menu_undo.set_sensitive(False)
        self.main.menu_redo.set_sensitive(True)

    def on_menu_redo_activate(self, widget):
        self.main.undo_manager.redo()
        self.main.dir_reload_current()
        self.main.menu_undo.set_sensitive(True)
        self.main.menu_redo.set_sensitive(False)

    def on_menu_refresh_activate(self, widget):
        self.main.file_browser.create_new()
        self.main.file_browser.set_active_dir(self.main.active_dir)

    def on_menu_patterns_activate(self, widget):
        self.main.notebook.set_current_page(0)

    def on_menu_substitutions_activate(self, widget):
        self.main.notebook.set_current_page(1)

    def on_menu_insert_activate(self, widget):
        self.main.notebook.set_current_page(2)

    def on_menu_manual_activate(self, widget):
        self.main.notebook.set_current_page(3)

    def on_menu_images_activate(self, widget):
        self.main.notebook.set_current_page(4)

    def on_menu_music_activate(self, widget):
        self.main.notebook.set_current_page(5)

    def on_menu_show_options_activate(self, widget):
        self.main.options_panel_state(widget.get_active())