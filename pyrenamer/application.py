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

from pathlib import Path
import logging

from gi.repository import Gtk, Gio, GLib, GObject

import pyrenamer.conf
from pyrenamer.paths import validate_root_dir, validate_active_dir
from pyrenamer.application_window import ApplicationWindow
from pyrenamer.preferences import PreferencesDialog


logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=pyrenamer.conf.APPLICATION_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        GLib.set_application_name(pyrenamer.conf.APPLICATION_NAME)
        Gtk.Window.set_default_icon_name(pyrenamer.conf.APPLICATION_ID)
        self.set_resource_base_path(pyrenamer.conf.RESOURCE_BASE_PATH)

        self._application_window = None

        self.add_main_option('root', ord('r'), GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
                             _("Root of the directory tree"), _("ROOT_DIR"))
        self.add_main_option('version', ord('v'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
                             _("Show release version"), None)
        self.add_main_option(GLib.OPTION_REMAINING, 0, GLib.OptionFlags.NONE, GLib.OptionArg.STRING_ARRAY,
                             "", _("[ACTIVE_DIR]"))

        self._settings = self.load_settings(pyrenamer.conf.APPLICATION_ID)
        self._root_dir = self._settings.get_string('root-dir')
        self._active_dir = self._settings.get_string('active-dir')

    @GObject.Property(type=Gio.Settings, flags=GObject.ParamFlags.READABLE)
    def settings(self):
        return self._settings

    @GObject.Property(type=str, flags=GObject.ParamFlags.READABLE)
    def root_dir(self):
        return self._root_dir

    @GObject.Property(type=str, flags=GObject.ParamFlags.READABLE)
    def active_dir(self):
        return self._active_dir

    def load_settings(self, schema_id):
        if pyrenamer.conf.UNINSTALLED:
            schema_source = Gio.SettingsSchemaSource.new_from_directory(
                directory=str(pyrenamer.conf.DATA_DIR), parent=Gio.SettingsSchemaSource.get_default(), trusted=False)
            schema = schema_source.lookup(schema_id, recursive=False)
            settings = Gio.Settings.new_full(schema=schema, backend=None, path=None)
        else:
            settings = Gio.Settings.new(schema_id)

        # If the root dir from GSettings is empty or it is not valid, set the root dir to the user home directory,
        # and if the home directory is not valid, set the root dir to '/'
        settings_root_dir = settings.get_string('root-dir')
        try:
            root_dir = validate_root_dir(settings_root_dir, must_be_absolute=True)
        except ValueError:
            logger.warning("GSettings 'root-dir' is empty or not valid. Setting 'root-dir' to the home directory.")
            root_dir = Path().home()
            try:
                root_dir = validate_root_dir(root_dir, must_be_absolute=True)
            except ValueError:
                logger.warning("GSettings 'root-dir' cannot be set to the home directory. Setting 'root-dir' to the root directory.")
                root_dir = '/'
        if root_dir != settings_root_dir:
            settings.set_string('root-dir', root_dir)

        # If the active dir from GSettings is empty or it is not valid, set the active dir to the root dir
        settings_active_dir = settings.get_string('active-dir')
        try:
            active_dir = validate_active_dir(settings_active_dir, root_dir, must_be_absolute=True)
        except ValueError:
            logger.warning("GSettings 'active-dir' is empty or not valid. Setting 'active-dir' to 'root-dir'.")
            active_dir = root_dir
        if active_dir != settings_active_dir:
            settings.set_string('active-dir', root_dir)

        return settings

    def do_startup(self):
        Gtk.Application.do_startup(self)

        accelerators = {
            'win.refresh': 'F5',
            'win.preview': '<Primary>P',
            'win.clear': '<Primary>L',
            'win.rename': '<Primary>R',
            'win.undo': '<Primary>Z',
            'win.redo': '<Primary><Shift>Z',
            'win.options': 'F9',
            'win.hamburger-menu': 'F10',
            'win.select-all': '<Primary>A',
            'win.unselect-all': '<Primary>D',
            'win.page-patterns': '<Primary>1',
            'win.page-substitutions': '<Primary>2',
            'win.page-insert-delete': '<Primary>3',
            'win.page-manual': '<Primary>4',
            'win.page-patterns-images': '<Primary>5',
            'win.page-patterns-music': '<Primary>6',
            'app.preferences': '<Primary>plus',
            'app.quit': '<Primary>Q'
        }
        for action_name, accel in accelerators.items():
            accel = accel if isinstance(accel, tuple) else (accel,)
            self.set_accels_for_action(action_name, accel)

        actions = (
            ('preferences', self.on_preferences),
            ('about', self.on_about),
            ('quit', self.on_quit)
        )
        for name, handler in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', handler)
            self.add_action(action)

    def do_activate(self):
        if not self._application_window:
            self._application_window = ApplicationWindow(application=self)

        self._application_window.present()

    def do_handle_local_options(self, options):
        if options.contains('version'):
            print(GLib.get_application_name(), pyrenamer.conf.VERSION)
            return 0

        return -1

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        root_dir = options.lookup_value('root')
        if root_dir is not None:
            root_dir = root_dir.get_string()
            try:
                self._root_dir = validate_root_dir(root_dir)
            except ValueError as e:
                command_line.do_printerr_literal(command_line, _("Error: ROOT_DIR must be an existing directory\n"))
                return 1

        remaining_args = options.lookup_value(GLib.OPTION_REMAINING)
        if remaining_args is not None:
            if len(remaining_args) > 1:
                command_line.do_printerr_literal(command_line, _("Error: Only one ACTIVE_DIR is allowed\n"))
                return 1
            active_dir = remaining_args[0]
            try:
                self._active_dir = validate_active_dir(active_dir, self._root_dir)
            except ValueError as e:
                command_line.do_printerr_literal(
                    command_line, _("Error: ACTIVE_DIR must be an existing subdirectory of ROOT_DIR\n"))
                return 1
        else:
            # If the active dir from GSettings is not a subdirectory of the new root dir,
            # change the active dir to be the root dir.
            try:
                validate_active_dir(self._active_dir, self._root_dir)
            except ValueError:
                self._active_dir = self._root_dir

        self.activate()
        return 0

    def on_preferences(self, action, param):
        dialog = PreferencesDialog(settings=self._settings, transient_for=self.get_active_window())
        dialog.present()

    def on_about(self, action, param):
        builder = Gtk.Builder.new_from_resource(f'{pyrenamer.conf.RESOURCE_BASE_PATH}/ui/AboutDialog.ui')
        dialog = builder.get_object('about-dialog')
        dialog.set_program_name(pyrenamer.conf.APPLICATION_NAME)
        dialog.set_version(pyrenamer.conf.VERSION)
        dialog.set_logo_icon_name(pyrenamer.conf.APPLICATION_ID)
        dialog.set_transient_for(self.get_active_window())
        dialog.run()
        dialog.destroy()

    def on_quit(self, action, param):
        self.quit()
