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

import logging

from gi.repository import Gtk, GObject, Gio

from pyrenamer.conf import RESOURCE_BASE_PATH
from pyrenamer.paths import validate_active_dir


logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/PreferencesDialog.ui')
class PreferencesDialog(Gtk.Dialog):
    __gtype_name__ = 'PreferencesDialog'

    root_dir = GObject.Property(type=str)
    active_dir = GObject.Property(type=str)

    folder_chooser_button_root = Gtk.Template.Child()
    label_root = Gtk.Template.Child()
    folder_chooser_button_active = Gtk.Template.Child()
    label_active = Gtk.Template.Child()

    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)

        self.bind_property('root-dir', self.label_root, 'label', GObject.BindingFlags.DEFAULT)
        self.bind_property('root-dir', self.label_root, 'tooltip-text', GObject.BindingFlags.DEFAULT)
        self.bind_property('active-dir', self.label_active, 'label', GObject.BindingFlags.DEFAULT)
        self.bind_property('active-dir', self.label_active, 'tooltip-text', GObject.BindingFlags.DEFAULT)

        settings.bind('root-dir', self, 'root-dir', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('active-dir', self, 'active-dir', Gio.SettingsBindFlags.DEFAULT)

        self.folder_chooser_button_root.set_filename(self.root_dir)
        self.folder_chooser_button_active.set_filename(self.active_dir)

        self.show_all()

    @Gtk.Template.Callback()
    def on_folder_chooser_button_root_file_set(self, button):
        self.root_dir = button.get_filename()

        # Check whether the active dir is still valid after the root dir has changed
        try:
            validate_active_dir(self.active_dir, self.root_dir)
        except:
            # If the active dir is not a subdirectory of the new root dir, set the active dir to the root dir
            logger.warning("Invalid active dir selected. Setting active dir to the root dir.")
            self.active_dir = self.root_dir
            self.folder_chooser_button_active.set_filename(self.active_dir)

    @Gtk.Template.Callback()
    def on_folder_chooser_button_active_file_set(self, button):
        active_dir = button.get_filename()

        # Check whether the active dir is valid
        try:
            validate_active_dir(active_dir, self.root_dir)
            self.active_dir = active_dir
        except ValueError:
            # If the new active dir is not a subdirectory of the root dir, show a message and restore the active dir
            dialog = Gtk.MessageDialog(
                transient_for=self,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=_("Invalid active directory"),
            )
            dialog.format_secondary_text(_("The active directory must be a subdirectory of the root directory."))
            dialog.run()
            dialog.destroy()

            self.folder_chooser_button_active.set_filename(self.active_dir)

    @Gtk.Template.Callback()
    def on_response(self, dialog, response_id):
        self.destroy()
