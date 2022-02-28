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


import os
import re
import fnmatch
from threading import Thread
from enum import IntEnum, unique
from xml.sax.saxutils import escape as escape_xml

from gi.repository import Gtk, GLib, GObject

from pyrenamer.conf import RESOURCE_BASE_PATH


@unique
class Column(IntEnum):
    ORIGINAL_ICON = 0
    ORIGINAL_NAME = 1
    ORIGINAL_PATH = 2
    RENAMED_ICON = 3
    RENAMED_NAME = 4
    RENAMED_PATH = 5
    TOOLTIP = 6


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/FileBrowser.ui')
class FileBrowser(Gtk.Bin):
    """This widget implements a simple file browser showing the contents of a directory and the new names after
       applying the renaming operations1."""

    __gtype_name__ = 'FileBrowser'

    MODES = ('files', 'directories', 'both')

    current_dir = GObject.Property(type=str, default='/', nick='Directory whose files/directories will be listed')
    recursive = GObject.Property(type=bool, default=False, nick='Add files and directory recursively')
    mode = GObject.Property(type=str, default='files', nick="Show 'files', 'directories' or 'both'")
    show_hidden = GObject.Property(type=bool, default=False, nick='Show hidden files and directories')
    file_pattern = GObject.Property(type=str, default=None, nick='Show files that match the shell pattern')
    multiple_selection = GObject.Property(type=bool, default=True, nick='Allow multiple files to be selected')

    __gsignals__ = {
        'load-started': (GObject.SignalFlags.RUN_LAST, None, (str,)),
        'load-ended': (GObject.SignalFlags.RUN_LAST, None, (str, int, int)),
        'load-cancelled': (GObject.SignalFlags.RUN_LAST, None, (str,)),
        'selection-changed': (GObject.SignalFlags.RUN_LAST, None, (object,))
    }

    view = Gtk.Template.Child('tree_view_file_browser')
    selection = Gtk.Template.Child('tree_selection_file_browser')
    model = Gtk.Template.Child('list_store_file_browser')
    progress = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()

    _extensions = {
        'audio': ('mp3', 'ogg', 'wav', 'aiff', 'mp4', 'aac'),
        'image': ('jpg', 'gif', 'png', 'tiff', 'tif', 'jpeg', 'xcf', 'psd', 'svg'),
        'video': ('avi', 'ogm', 'mpg', 'mpeg', 'mov', 'mkv'),
        'package': ('rar', 'zip', 'gz', 'tar', 'bz2', 'tgz', 'deb', 'rpm')
    }

    def __init__(self, current_dir=None, recursive=False, mode='files', show_hidden=False, file_pattern=None, **kwargs):
        super().__init__(**kwargs)
        self.current_dir = current_dir
        self.recursive = recursive
        self.mode = mode
        self.show_hidden = show_hidden
        self.file_pattern = file_pattern

        self._loading_dir = None
        self._total_dirs = 0
        self._total_files = 0
        self._cancel_loading = False
        self._listing_thread = None
        self._view_filling_event_source_id = None
        self._progress_event_source_id = None

        Gtk.IconTheme.get_default().connect('changed', self.on_icon_theme_changed)
        self._load_icons()
        if self.current_dir:
           self._load()

        self._set_progress_background_color()
        self.view.connect('style-updated', self.on_view_style_updated)

        self.connect('notify::current-dir', self.on_current_dir_changed)
        self.connect('notify::recursive', self.on_property_changed)
        self.connect('notify::mode', self.on_property_changed)
        self.connect('notify::show-hidden', self.on_property_changed)
        self.connect('notify::file-pattern', self.on_property_changed)
        self.connect('notify::multiple-selection', self.on_multiple_selection_changed)

    @GObject.Property(type=int, default=0, nick='Total number of loaded directories', flags=GObject.ParamFlags.READABLE)
    def total_dirs(self):
        return self._total_dirs

    @GObject.Property(type=int, default=0, nick='Total number of loaded files', flags=GObject.ParamFlags.READABLE)
    def total_files(self):
        return self._total_files

    def on_icon_theme_changed(self, icon_theme):
        self._load_icons()
        if self.current_dir:
            self._load()

    def on_view_style_updated(self, widget):
        self._set_progress_background_color()

    def on_current_dir_changed(self, obj, prop):
        if not os.path.isdir(self.current_dir):
            raise ValueError(f"current_dir '{self.current_dir}' is not a valid directory.")
        self._load()

    def on_property_changed(self, obj, prop):
        if prop.name == 'mode':
            if self.mode not in self.MODES:
                raise ValueError(f"{self.__gtype_name__}: '{prop.name}' must be one of: {', '.join(self.MODES)}.")

        if self.current_dir:
            self._load()

    def on_multiple_selection_changed(self, obj, prop):
        if self.multiple_selection:
            self.selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        else:
            _, selected_rows = self.selection.get_selected_rows()
            if selected_rows:
                self.selection.set_mode(Gtk.SelectionMode.SINGLE)
            else:
                # For some reason, when setting selection mode to SINGLE after having unselected all rows, the TreeView
                # no longer allows selecting rows. To prevent that, when there are no rows selected, first all rows are
                # selected, then SINGLE mode is set, and finally rows are unselected.
                self.selection.select_all()
                self.selection.set_mode(Gtk.SelectionMode.SINGLE)
                self.selection.unselect_all()

    @Gtk.Template.Callback()
    def on_tree_selection_file_browser_changed(self, tree_selection):
        selected_files = []
        model, selected_paths = tree_selection.get_selected_rows()
        if selected_paths:
            selected_iters = [model.get_iter(path) for path in selected_paths]
            selected_files = [(model[iter][1], model[iter][2], model[iter][4], model[iter][5]) for iter in selected_iters]
        self.emit('selection-changed', selected_files)

    @Gtk.Template.Callback()
    def on_button_cancel_clicked(self, button):
        self.cancel_loading()

    def _set_progress_background_color(self):
        # Set progress window background to the same color than the TreeView background
        view_background_color = self.view.get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(f"""
            frame {{
                background-color: {view_background_color.to_string()};
            }}
        """.encode())
        self.progress.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _load_icons(self):
        icon_theme = Gtk.IconTheme.get_default()

        # Load directory icon
        icon_names = ('folder', 'gnome-fs-directory', 'gtk-directory')
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_folder = None if icon_info is None else icon_info.load_icon()

        # Load file icon
        icon_names = ('text-x-generic', )
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_file = None if icon_info is None else icon_info.load_icon()

        # Load image icon
        icon_names = ('image-x-generic', )
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_image = None if icon_info is None else icon_info.load_icon()

        # Load audio icon
        icon_names = ('audio-x-generic', )
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_audio = None if icon_info is None else icon_info.load_icon()

        # Load video icon
        icon_names = ('video-x-generic', )
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_video = None if icon_info is None else icon_info.load_icon()

        # Load package icon
        icon_names = ('package-x-generic', )
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_package = None if icon_info is None else icon_info.load_icon()

    def _get_icon(self, filename):
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        if ext in self._extensions['image']:
            return self._icon_image
        elif ext in self._extensions['audio']:
            return self._icon_audio
        elif ext in self._extensions['video']:
            return self._icon_video
        elif ext in self._extensions['package']:
            return self._icon_package
        else:
            return self._icon_file

    def _get_dirs_and_files(self):
        show_files = self.mode in ('files', 'both')
        show_dirs = self.mode in ('directories', 'both')
        dirs_and_files = {}
        for dirpath, dirnames, filenames in os.walk(self._loading_dir):
            if not self.show_hidden:
                # Modifying 'dirnames' in-place prevents os.walk() from visiting hidden directories
                dirnames[:] = [d for d in dirnames if d[0] != '.']
                if show_files:
                    filenames = [f for f in filenames if f[0] != '.']

            if self.file_pattern and self.file_pattern != '*' and show_files:
                regex = re.compile(fnmatch.translate(self.file_pattern))
                filenames = list(filter(regex.match, filenames))

            # Sorting 'dirnames' in-place forces os.walk() to visit directories in alphabetical order
            dirnames.sort(key=str.lower)
            if show_files:
                filenames.sort(key=str.lower)

            dirs_and_files[dirpath] = (
                [] if not show_dirs else [(d, os.path.join(dirpath, d)) for d in dirnames],
                [] if not show_files else [(f, os.path.join(dirpath, f)) for f in filenames]
            )
            if not self.recursive or self._cancel_loading:
                break

        return dirs_and_files

    def _get_dirs_and_files_thread(self):
        dirs_and_files = self._get_dirs_and_files()

        if not self._cancel_loading:
            add_item_to_view = self._add_items_to_view(dirs_and_files)
            self._view_filling_event_source_id = GLib.idle_add(lambda: next(add_item_to_view))

    def _make_tooltip(self, original_path, renamed_path=None):
        if renamed_path is None:
            return _("<b>Original: </b>{}").format(escape_xml(original_path))
        else:
            return _("<b>Original: </b>{}\n<b>Renamed: </b>{}").format(escape_xml(original_path), escape_xml(renamed_path))

    def _add_items_to_view(self, dirs_and_files):
        for directories, files in dirs_and_files.values():
            self._total_dirs += len(directories)
            for dirname, dirpath in directories:
                self.model.append(
                    (self._icon_folder, dirname, dirpath, None, None, None, self._make_tooltip(dirpath)))
                yield True
            self._total_files += len(files)
            for filename, filepath in files:
                self.model.append(
                    (self._get_icon(filename), filename, filepath, None, None, None, self._make_tooltip(filepath)))
                yield True

        self.view.set_model(self.model)
        self.view.columns_autosize()

        self._hide_progress()
        self.emit('load-ended', self._loading_dir, self.total_dirs, self.total_files)
        self._loading_dir = None

        yield False

    def _show_progress(self):
        def show_progress():
            self.view.set_sensitive(False)
            self.button_cancel.set_sensitive(True)
            self.progress.show()
            return False  # Run only once

        self._progress_event_source_id = GLib.timeout_add(200, show_progress)

    def _hide_progress(self):
        if self._progress_event_source_id:
            if GLib.MainContext.default().find_source_by_id(self._progress_event_source_id):
                GLib.source_remove(self._progress_event_source_id)
        self.progress.hide()
        self.view.set_sensitive(True)

    def _load(self):
        if self._loading_dir:
            self.cancel_loading()

        self._loading_dir = self.current_dir
        self._cancel_loading = False
        self._total_dirs = 0
        self._total_files = 0

        self._show_progress()
        self.emit('load-started', self._loading_dir)

        self.view.set_model(None)  # Don't display items in the view while loading
        self.model.clear()

        self._listing_thread = Thread(target=self._get_dirs_and_files_thread, daemon=True)
        self._listing_thread.start()

    def cancel_loading(self):
        self.button_cancel.set_sensitive(False)

        self._cancel_loading = True
        if self._listing_thread:
            self._listing_thread.join()

        if self._view_filling_event_source_id:
            if GLib.MainContext.default().find_source_by_id(self._view_filling_event_source_id):
                GLib.source_remove(self._view_filling_event_source_id)

        self._hide_progress()
        self.emit('load-cancelled', self._loading_dir)
        self._loading_dir = None
        self._cancel_loading = False

    def _update_renamed_row(self, model, path, iter, data):
        selected_paths, rename = data

        if self.selection.get_mode() == Gtk.SelectionMode.SINGLE and not selected_paths:
            # Do nothing is selection mode is single and no rows are selected
            return
        if selected_paths and path not in selected_paths:
            # Do nothing if some rows are selected and the current row is not in the selection
            return

        original_path = model[iter][Column.ORIGINAL_PATH]
        renamed_path = rename(original_path)
        if renamed_path != original_path:
            renamed_name = os.path.relpath(renamed_path, start=os.path.commonpath([original_path, renamed_path]))
            model[iter][Column.RENAMED_ICON] = self._icon_folder if model[iter][Column.ORIGINAL_ICON] is self._icon_folder else self._get_icon(renamed_name)
            model[iter][Column.RENAMED_NAME] = renamed_name
            model[iter][Column.RENAMED_PATH] = renamed_path
            model[iter][Column.TOOLTIP] = self._make_tooltip(original_path, renamed_path)
        else:
            model[iter][Column.RENAMED_ICON] = model[iter][Column.RENAMED_NAME] = model[iter][Column.RENAMED_PATH] = None
            model[iter][Column.TOOLTIP] = self._make_tooltip(original_path)

    def update_renamed(self, rename):
        _, selected_paths = self.selection.get_selected_rows()
        self.model.foreach(self._update_renamed_row, (selected_paths, rename))
        self.view.columns_autosize()

    def _clear_renamed_row(self, model, path, iter, selected_paths):
        if selected_paths and path not in selected_paths:
            return

        model[iter][Column.RENAMED_ICON] = model[iter][Column.RENAMED_NAME] = model[iter][Column.RENAMED_PATH] = None
        model[iter][Column.TOOLTIP] = self._make_tooltip(model[iter][Column.ORIGINAL_PATH])

    def clear_renamed(self):
        _, selected_paths = self.selection.get_selected_rows()
        self.model.foreach(self._clear_renamed_row, selected_paths)
        self.view.columns_autosize()

    def get_renamed(self):
        renamed = []
        iter = self.model.get_iter_first()
        while iter:
            original_path = self.model[iter][Column.ORIGINAL_PATH]
            renamed_path = self.model[iter][Column.RENAMED_PATH]
            if renamed_path:
                renamed.append((original_path, renamed_path))
            iter = self.model.iter_next(iter)
        return renamed

    def select_previous(self):
        if self.selection.get_mode() == Gtk.SelectionMode.SINGLE:
            model, iter = self.selection.get_selected()
            if iter:
                path = int(model.get_string_from_iter(iter))
                if path > 0:
                    self.selection.select_iter(model.get_iter_from_string(str(path - 1)))

    def select_next(self):
        if self.selection.get_mode() == Gtk.SelectionMode.SINGLE:
            model, iter = self.selection.get_selected()
            if iter:
                next_iter = model.iter_next(iter)
                if next_iter:
                    self.selection.select_iter(next_iter)

    def select_all(self):
        if self.selection.get_mode() != Gtk.SelectionMode.SINGLE:
            self.selection.select_all()

    def unselect_all(self):
        self.selection.unselect_all()
