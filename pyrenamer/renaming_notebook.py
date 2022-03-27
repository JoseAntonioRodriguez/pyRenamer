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


from enum import IntEnum, unique

from gi.repository import Gtk, GObject

from pyrenamer.conf import RESOURCE_BASE_PATH
from pyrenamer.patterns_page import PatternsPage
from pyrenamer.substitutions_page import SubstitutionsPage
from pyrenamer.insert_delete_page import InsertDeletePage
from pyrenamer.manual_page import ManualPage


@unique
class Page(IntEnum):
    PATTERNS = 0
    SUBSTITUTIONS = 1
    INSERT_DELETE = 2
    MANUAL = 3
    PATTERNS_IMAGES = 4
    PATTERNS_MUSIC = 5


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/RenamingNotebook.ui')
class RenamingNotebook(Gtk.Notebook):
    __gtype_name__ = 'RenamingNotebook'

    __gsignals__ = {
        'next': (GObject.SignalFlags.RUN_LAST, None, ()),
        'previous': (GObject.SignalFlags.RUN_LAST, None, ()),
        'changed': (GObject.SignalFlags.RUN_LAST, None, (object,))
    }

    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self._selected_filename = ''
        self._multiple_renaming = True

        self.patterns_page = PatternsPage(settings, PatternsPage.Mode.GENERIC)
        self.patterns_page.connect('changed', self.on_renaming_rules_changed)
        self.append_page(self.patterns_page, Gtk.Label(_("Patterns")))

        self.substitutions_page = SubstitutionsPage()
        self.substitutions_page.connect('changed', self.on_renaming_rules_changed)
        self.append_page(self.substitutions_page, Gtk.Label(_("Substitutions")))

        self.insert_delete_page = InsertDeletePage()
        self.insert_delete_page.connect('changed', self.on_renaming_rules_changed)
        self.append_page(self.insert_delete_page, Gtk.Label(_("Insert / Delete")))

        self.manual_page = ManualPage()
        self.manual_page.connect('changed', self.on_renaming_rules_changed)
        self.manual_page.connect('previous', lambda page: self.emit('previous'))
        self.manual_page.connect('next', lambda page: self.emit('next'))
        self.append_page(self.manual_page, Gtk.Label(_("Manual rename")))

        self.images_patterns_page = PatternsPage(settings, PatternsPage.Mode.IMAGES)
        self.images_patterns_page.connect('changed', self.on_renaming_rules_changed)
        self.append_page(self.images_patterns_page, Gtk.Label(_("Images")))

        self.music_patterns_page = PatternsPage(settings, PatternsPage.Mode.MUSIC)
        self.music_patterns_page.connect('changed', self.on_renaming_rules_changed)
        self.append_page(self.music_patterns_page, Gtk.Label(_("Music")))

    @GObject.Property(type=bool, default=True, nick='Whether the current page allows renaming multiple files',
                      flags=GObject.ParamFlags.READABLE | GObject.ParamFlags.EXPLICIT_NOTIFY)
    def multiple_renaming(self):
        return self._multiple_renaming

    @Gtk.Template.Callback()
    def on_switch_page(self, notebook, page, page_num):
        self._multiple_renaming = page_num != Page.MANUAL
        self.notify('multiple-renaming')

        self.emit('changed', page.get_renaming_rules())

        if page_num == Page.MANUAL:
            self.manual_page.set_filename(self._selected_filename)

    def on_renaming_rules_changed(self, page, renaming_rules):
        self.emit('changed', renaming_rules)

    def set_selected_files(self, selected_files):
        current_page = self.get_current_page()
        if selected_files:
            original_filename, _, renamed_filename, _  = selected_files[0]
            if current_page == Page.MANUAL and renamed_filename:
                self._selected_filename = renamed_filename
            else:
                self._selected_filename = original_filename
        else:
            self._selected_filename = ''

        if self.get_current_page() == Page.MANUAL:
            self.manual_page.set_filename(self._selected_filename)

    def clear(self):
        current_page = self.get_current_page()
        if current_page == Page.MANUAL:
            self.manual_page.set_filename(self._selected_filename)
        else:
            self.get_nth_page(current_page).clear()
