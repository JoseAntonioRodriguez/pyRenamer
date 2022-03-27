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


from gi.repository import Gtk, GObject, Gio

from pyrenamer.conf import RESOURCE_BASE_PATH


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/OptionsPane.ui')
class OptionsPane(Gtk.Bin):
    __gtype_name__ = 'OptionsPane'

    rename_mode = GObject.Property(type=str)

    combo_rename_mode = Gtk.Template.Child()
    entry_selection_pattern = Gtk.Template.Child()
    check_show_hidden = Gtk.Template.Child()
    check_add_recursive = Gtk.Template.Child()
    check_keep_extensions = Gtk.Template.Child()
    check_auto_preview = Gtk.Template.Child()

    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)

        settings.bind('rename-mode', self.combo_rename_mode, 'active-id', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('selection-pattern', self.entry_selection_pattern, 'text', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('show-hidden', self.check_show_hidden, 'active', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('add-recursive', self.check_add_recursive, 'active', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('keep-extensions', self.check_keep_extensions, 'active', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('auto-preview', self.check_auto_preview, 'active', Gio.SettingsBindFlags.DEFAULT)
