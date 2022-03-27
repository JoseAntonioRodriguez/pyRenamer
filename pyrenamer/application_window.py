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

from gi.repository import Gtk, GLib, Gio, GObject

from pyrenamer.conf import RESOURCE_BASE_PATH
from pyrenamer.window_state import WindowState
from pyrenamer.tree_file_browser import TreeFileBrowser
from pyrenamer.file_browser import FileBrowser
from pyrenamer.options_pane import OptionsPane
from pyrenamer.renaming_notebook import RenamingNotebook, Page
from pyrenamer.renamer import Renamer


logger = logging.getLogger(__name__)


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/ApplicationWindow.ui')
class ApplicationWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'ApplicationWindow'

    auto_preview = GObject.Property(type=bool, default=False, nick='Auto preview changes')
    keep_extensions = GObject.Property(type=bool, default=False, nick='Keep file extensions')

    toggle_button_options = Gtk.Template.Child()
    menu_button_hamburger = Gtk.Template.Child()
    box_main = Gtk.Template.Child()
    box_upper = Gtk.Template.Child()
    paned_files = Gtk.Template.Child()
    status_bar = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application)

        actions = (
            ('refresh', self.on_action_refresh),
            ('preview', self.on_action_preview),
            ('clear', self.on_action_clear),
            ('rename', self.on_action_rename),
            ('undo', self.on_action_undo),
            ('redo', self.on_action_redo),
            ('select-all', self.on_action_select_all),
            ('unselect-all', self.on_action_unselect_all),
            ('page-patterns', self.on_action_page),
            ('page-substitutions', self.on_action_page),
            ('page-insert-delete', self.on_action_page),
            ('page-manual', self.on_action_page),
            ('page-patterns-images', self.on_action_page),
            ('page-patterns-music', self.on_action_page)
        )
        for name, callback in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', callback)
            self.add_action(action)
            setattr(self, f'action_{name.replace("-", "_")}', action)

        stateful_actions = (
            ('options', self.on_action_options, GLib.Variant.new_boolean(False)),
            ('hamburger-menu', None, GLib.Variant.new_boolean(False))
        )
        for name, callback, state in stateful_actions:
            action = Gio.SimpleAction.new_stateful(name, None, state)
            if callback:
                action.connect('change-state', callback)
            self.add_action(action)
            setattr(self, f'action_{name.replace("-", "_")}', action)

        WindowState().bind(self)

        self._renamer = Renamer()
        self._renaming_rules = []
        self._ignore_errors = False

    def do_realize(self):
        Gtk.ApplicationWindow.do_realize(self)
        application = self.get_application()

        self.action_clear.set_enabled(False)
        self.action_preview.set_enabled(False)
        self.action_rename.set_enabled(False)
        self.action_undo.set_enabled(False)
        self.action_redo.set_enabled(False)

        menu = application.get_menu_by_id('hamburger-menu')
        self.menu_button_hamburger.set_popover(Gtk.Popover.new_from_model(self.menu_button_hamburger, menu))

        self.status_bar_context_id = self.status_bar.get_context_id('file_browser')

        application.settings.bind('separator-position', self.paned_files, 'position', Gio.SettingsBindFlags.DEFAULT)

        self.tree_file_browser = TreeFileBrowser(application.root_dir, show_only_dirs=True)
        self.paned_files.add1(self.tree_file_browser)
        application.settings.bind('show-hidden', self.tree_file_browser, 'show-hidden', Gio.SettingsBindFlags.DEFAULT)

        self.file_browser = FileBrowser()
        self.paned_files.add2(self.file_browser)
        self.file_browser.connect('load-started', self.on_file_browser_load_started)
        self.file_browser.connect('load-ended', self.on_file_browser_load_ended)
        self.file_browser.connect('load-cancelled', self.on_file_browser_load_cancelled)

        application.settings.bind('add-recursive', self.file_browser, 'recursive', Gio.SettingsBindFlags.DEFAULT)
        application.settings.bind('rename-mode', self.file_browser, 'mode', Gio.SettingsBindFlags.DEFAULT)
        application.settings.bind('show-hidden', self.file_browser, 'show-hidden', Gio.SettingsBindFlags.DEFAULT)
        application.settings.bind('selection-pattern', self.file_browser, 'file-pattern', Gio.SettingsBindFlags.DEFAULT)

        self.tree_file_browser.connect('cursor-changed', self.on_tree_file_browser_cursor_changed)
        self.tree_file_browser.set_selected(application.active_dir)

        self.options_pane = OptionsPane(application.settings)
        self.box_upper.pack_start(self.options_pane, False, True, 0)

        self.on_action_options(self.action_options, application.settings.get_value('options-shown'))
        application.settings.bind('options-shown', self.options_pane, 'visible', Gio.SettingsBindFlags.DEFAULT)

        self.renaming_notebook = RenamingNotebook(application.settings)
        self.renaming_notebook.connect('changed', self.on_renaming_rules_changed)
        self.renaming_notebook.connect('previous', self.on_renaming_rules_previous)
        self.renaming_notebook.connect('next', self.on_renaming_rules_next)
        self.renaming_notebook.bind_property('multiple-renaming', self.file_browser, 'multiple-selection', GObject.BindingFlags.SYNC_CREATE)
        self.file_browser.connect('selection-changed', self.on_file_browser_selection_changed)
        self.box_main.pack_start(self.renaming_notebook, False, True, 0)

        self.connect('notify::keep-extensions', self.on_keep_extensions_changed)
        application.settings.bind('auto-preview', self, 'auto-preview', Gio.SettingsBindFlags.GET)
        application.settings.bind('keep-extensions', self, 'keep-extensions', Gio.SettingsBindFlags.GET)

    def on_tree_file_browser_cursor_changed(self, tree_file_browser, path):
        self.file_browser.current_dir = path

    def on_file_browser_load_started(self, file_browser, root_dir):
        self.status_bar.push(
            self.status_bar_context_id,
            _("Reading contents of directory '{}'...").format(root_dir))

    def on_file_browser_load_ended(self, file_browser, root_dir, total_dirs, total_files):
        self.status_bar.push(
            self.status_bar_context_id,
            _("Directory '{}' contains {} directories and {} files").format(root_dir, f"{total_dirs:n}", f"{total_files:n}"))

        # if self.auto_preview:
        #     self.on_action_preview(self.action_preview, None)

    def on_file_browser_load_cancelled(self, file_browser, root_dir):
        self.status_bar.push(self.status_bar_context_id, "")

    def on_file_browser_selection_changed(self, file_browser, selected_files):
        self.renaming_notebook.set_selected_files(selected_files)

    def on_keep_extensions_changed(self, obj, prop):
        if self.auto_preview:
            self.on_action_preview(self.action_preview, None)

    def on_renaming_rules_changed(self, notebook, renaming_rules):
        self._renaming_rules = renaming_rules
        self.action_preview.set_enabled(bool(self._renaming_rules))
        self.action_rename.set_enabled(False)
        if self.auto_preview:
            self.on_action_preview(self.action_preview, None)

    def on_renaming_rules_previous(self, notebook):
        self.on_action_preview(self.on_action_preview, None)
        self.file_browser.select_previous()

    def on_renaming_rules_next(self, notebook):
        self.on_action_preview(self.on_action_preview, None)
        self.file_browser.select_next()

    def on_action_refresh(self, action, parameter):
        self.tree_file_browser.refresh()

    def on_action_options(self, action, state):
        action.set_state(state)
        self.get_application().settings.set_value('options-shown', state)
        if state:
            self.toggle_button_options.set_tooltip_text(_("Hide the options pane"))
        else:
            self.toggle_button_options.set_tooltip_text(_("Show the options pane"))

    def on_action_select_all(self, action, parameter):
        self.file_browser.select_all()

    def on_action_unselect_all(self, action, parameter):
        self.file_browser.unselect_all()
        self.renaming_notebook.set_selected_files([])

    def on_action_page(self, action, parameter):
        action_name = action.get_name()
        if action_name == 'page-patterns':
            self.renaming_notebook.set_current_page(Page.PATTERNS)
        elif action_name == 'page-substitutions':
            self.renaming_notebook.set_current_page(Page.SUBSTITUTIONS)
        elif action_name == 'page-insert-delete':
            self.renaming_notebook.set_current_page(Page.INSERT_DELETE)
        elif action_name == 'page-manual':
            self.renaming_notebook.set_current_page(Page.MANUAL)
        elif action_name == 'page-patterns-images':
            self.renaming_notebook.set_current_page(Page.PATTERNS_IMAGES)
        elif action_name == 'page-patterns-music':
            self.renaming_notebook.set_current_page(Page.PATTERNS_MUSIC)

    def on_action_preview(self, action, parameter):
        for renaming_rule in self._renaming_rules:
            renaming_rule.reset()
        self.file_browser.update_renamed(self._get_renamed_path)
        total_renamed = len(self.file_browser.get_renamed())
        self.action_clear.set_enabled(total_renamed > 0)
        self.action_rename.set_enabled(total_renamed > 0)

    def _get_renamed_path(self, path):
        renamed_path = path
        for renaming_rule in self._renaming_rules:
            renamed_path = renaming_rule.rename(renamed_path, self.keep_extensions)
        return renamed_path

    def on_action_clear(self, action, parameter):
        self.file_browser.clear_renamed()
        total_renamed = len(self.file_browser.get_renamed())
        self.renaming_notebook.clear()
        self.action_clear.set_enabled(total_renamed > 0)
        self.action_rename.set_enabled(total_renamed > 0)

    def on_action_rename(self, action, parameter):
        self._renamer.clear()
        for original_path, renamed_path in self.file_browser.get_renamed():
            try:
                self._renamer.rename(original_path, renamed_path)
            except OSError as e:
                logger.error("Could not rename file '%s' to '%s' (%s)", original_path, renamed_path, e.strerror)
                if not self._ignore_errors:
                    self._show_error(_("Could not rename file '{}' to '{}'\n{}").format(
                        original_path, renamed_path, e.strerror))

        self.action_undo.set_enabled(self._renamer.undoable)
        self.action_redo.set_enabled(self._renamer.redoable)
        self.action_rename.set_enabled(False)
        # self.renaming_notebook.clear()
        self.tree_file_browser.refresh()
        self.action_clear.set_enabled(len(self.file_browser.get_renamed()) > 0)
        self._ignore_errors = False

    def on_action_undo(self, action, parameter):
        self._renamer.undo()
        self.tree_file_browser.refresh()
        self.action_undo.set_enabled(self._renamer.undoable)
        self.action_redo.set_enabled(self._renamer.redoable)

    def on_action_redo(self, action, parameter):
        self._renamer.redo()
        self.tree_file_browser.refresh()
        self.action_undo.set_enabled(self._renamer.undoable)
        self.action_redo.set_enabled(self._renamer.redoable)

    def _show_error(self, error_message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.NONE,
            text = error_message)
        dialog.add_button(_("Ignore errors"), Gtk.ResponseType.REJECT)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.REJECT:
            self._ignore_errors = True
        dialog.destroy()
