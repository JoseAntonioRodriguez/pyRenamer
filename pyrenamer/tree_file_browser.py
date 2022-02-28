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
from pathlib import Path

from gi.repository import Gtk, GObject

from pyrenamer.conf import RESOURCE_BASE_PATH


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/TreeFileBrowser.ui')
class TreeFileBrowser(Gtk.Bin):
    """This widget implements a tree-like file browser."""

    __gtype_name__ = 'TreeFileBrowser'

    root_dir = GObject.Property(type=str, default='/', nick='Root of the directory tree')
    show_hidden = GObject.Property(type=bool, default=False, nick='Show hidden files and directories')
    show_only_dirs = GObject.Property(type=bool, default=True, nick='Show only directories, not files')

    __gsignals__ = {
        'row-expanded': (GObject.SignalFlags.RUN_LAST, None, (str,)),
        'cursor-changed': (GObject.SignalFlags.RUN_LAST, None, (str,))
    }

    view = Gtk.Template.Child('tree_view_file_browser')
    model = Gtk.Template.Child('tree_store_file_browser')

    def __init__(self, root_dir, show_hidden=False, show_only_dirs=True, **kwargs):
        super().__init__(**kwargs)
        self.root_dir = root_dir
        self.show_hidden = show_hidden
        self.show_only_dirs = show_only_dirs

        Gtk.IconTheme.get_default().connect('changed', self.on_icon_theme_changed)
        self._load_icons()
        self._load_tree()

        self.connect('notify::root-dir', self.on_root_dir_changed)
        self.connect('notify::show-hidden', self.on_show_changed)
        self.connect('notify::show-only-dirs', self.on_show_changed)

    def refresh(self):
        selected = self.get_selected()
        self._load_tree()
        if selected is not None:
            self.set_selected(selected)

    def on_icon_theme_changed(self, icon_theme):
        self._load_icons()
        selected = self.get_selected()
        self._load_tree()
        if selected is not None:
            self.set_selected(selected)

    def on_root_dir_changed(self, obj, prop):
        if not os.path.isdir(self.root_dir):
            raise ValueError(f"root_dir '{self.root_dir}' is not a valid directory.")
        self._load_tree()

    def on_show_changed(self, obj, prop):
        selected = self.get_selected()
        self._load_tree()
        if selected is not None:
            self.set_selected(selected)

    @Gtk.Template.Callback()
    def on_row_expanded(self, tree_view, iter, path):
        self.model[iter][0] = self._icon_folder_opened
        self._add_children(iter, self.model[iter][2])
        self._remove_empty_child(iter)

        self.emit('row-expanded', self.model[iter][2])

    @Gtk.Template.Callback()
    def on_row_collapsed(self, tree_view, iter, path):
        self.model[iter][0] = self._icon_folder_closed
        while self.model.iter_has_child(iter):
            self.model.remove(self.model.iter_children(iter))
        self._add_empty_child(iter)

    @Gtk.Template.Callback()
    def on_row_activated(self, tree_view, path, column):
        if tree_view.row_expanded(path):
            tree_view.collapse_row(path)
        else:
            tree_view.expand_row(path, False)

    @Gtk.Template.Callback()
    def on_cursor_changed(self, tree_view):
        selected = self.get_selected()
        self.emit('cursor-changed', selected)

    def _is_relative_to_root(self, directory):
        try:
            Path(directory).relative_to(self.root_dir)
            return True
        except ValueError:
            return False

    def _load_icons(self):
        icon_theme = Gtk.IconTheme.get_default()

        # Load closed directory icon
        icon_names = ('folder', 'gnome-fs-directory', 'gtk-directory')
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_folder_closed = None if icon_info is None else icon_info.load_icon()

        # Load opened directory icon
        icon_names = ('folder-open', 'gnome-fs-directory-accept', 'gtk-directory')
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_folder_opened = None if icon_info is None else icon_info.load_icon()

        # Load file icon
        icon_names = ('text-x-generic', )
        icon_info = icon_theme.choose_icon(icon_names, Gtk.IconSize.MENU, 0)
        self._icon_file = None if icon_info is None else icon_info.load_icon()

    def _get_directory_children_names(self, directory):
        try:
            _, dirnames, filenames = next(os.walk(directory))
        except StopIteration:
            dirnames = filenames = []

        if not self.show_hidden:
            dirnames = [d for d in dirnames if d[0] != '.']
            if not self.show_only_dirs:
                filenames = [f for f in filenames if f[0] != '.']

        dirnames.sort(key=str.lower)
        if not self.show_only_dirs:
            filenames.sort(key=str.lower)

        return dirnames, [] if self.show_only_dirs else filenames

    def _has_directory_children(self, directory):
        dirs, files = self._get_directory_children_names(directory)
        return len(dirs) + len(files) > 0

    def _add_empty_child(self, iter):
        self.model.append(iter, None)

    def _remove_empty_child(self, iter):
        self.model.remove(self.model.iter_children(iter))

    def _add_children(self, iter, directory):
        dirs, files = self._get_directory_children_names(directory)

        for name in dirs:
            icon = self._icon_folder_closed
            path = os.path.join(directory, name)
            child_iter = self.model.append(iter, (icon, name, path))
            if self._has_directory_children(path):
                self._add_empty_child(child_iter)

        for name in files:
            icon = self._icon_file
            path = os.path.join(directory, name)
            self.model.append(iter, (icon, name, path))

    def _add_root(self):
        icon = self._icon_folder_closed
        name = Path(self.root_dir).parts[-1]
        path = os.path.abspath(self.root_dir)

        iter = self.model.append(None, (icon, name, path))
        if self._has_directory_children(self.root_dir):
            self.model.append(iter, None)

        return iter

    def _expand_row(self, iter):
        path = self.model.get_path(iter)
        if not self.view.row_expanded(path):
            self.view.expand_row(path, False)

    def _set_cursor(self, iter):
        if iter is not None:
            self.view.set_cursor(self.model.get_path(iter))

    def _unset_cursor(self):
        self.view.set_cursor('1')

    def _load_tree(self):
        self._unset_cursor()  # To avoid emitting cursor-changed signals while clearing the model
        self.model.clear()
        iter = self._add_root()
        self._expand_row(iter)

    def get_selected(self):
        """Returns the path to the currently selected file/directory."""
        model, iter = self.view.get_selection().get_selected()
        return None if iter is None else model[iter][2]

    def set_selected(self, selected):
        """Expands the tree looking for the given file/directory path and make it the selected item."""
        selected = Path(selected)

        if not (selected.is_dir() or selected.is_file()):
            return False
        if not self._is_relative_to_root(selected):
            return False
        if selected.is_file() and self.show_only_dirs:
            return False
        if any(part for part in selected.parts if part.startswith('.')) and not self.show_hidden:
            return False

        if selected == Path(self.root_dir):
            self._set_cursor(self.model.get_iter_first())
            return True

        iter = self.model.get_iter_first()
        self._expand_row(iter)

        names = selected.relative_to(self.root_dir).parts
        for i, name in enumerate(names):
            iter = self.model.iter_children(iter)
            while self.model[iter][1] != name:
                iter = self.model.iter_next(iter)
            if i < len(names) - 1:
                self._expand_row(iter)

        self._set_cursor(iter)
        self.view.scroll_to_cell(self.model.get_path(iter), use_align=True, row_align=0.5)
        return True
