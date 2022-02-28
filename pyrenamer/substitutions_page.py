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


from gi.repository import Gtk, GObject

from pyrenamer.conf import RESOURCE_BASE_PATH
from pyrenamer.renaming_rules import (RenamingRuleSpaces, RenamingRuleReplace, RenamingRuleCapitalization,
                                      RenamingRuleRemoveAccents, RenamingRuleFixDuplicated)


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/SubstitutionsPage.ui')
class SubstitutionsPage(Gtk.Bin):
    __gtype_name__ = 'SubstitutionsPage'

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, (object,))
    }

    check_spaces = Gtk.Template.Child()
    combo_spaces = Gtk.Template.Child()
    check_replace = Gtk.Template.Child()
    entry_replace_old = Gtk.Template.Child()
    entry_replace_new = Gtk.Template.Child()
    check_capitalization = Gtk.Template.Child()
    combo_capitalization = Gtk.Template.Child()
    check_accents = Gtk.Template.Child()
    check_duplicated = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._defaults = {
            'check_spaces': self.check_spaces.get_active(),
            'combo_spaces': self.combo_spaces.get_active(),
            'check_replace': self.check_replace.get_active(),
            'entry_replace_old': self.entry_replace_old.get_text(),
            'entry_replace_new': self.entry_replace_new.get_text(),
            'check_capitalization': self.check_capitalization.get_active(),
            'combo_capitalization': self.combo_capitalization.get_active(),
            'check_accents': self.check_accents.get_active(),
            'check_duplicated': self.check_duplicated.get_active(),
        }

        self.check_spaces.bind_property('active', self.combo_spaces, 'sensitive', GObject.BindingFlags.DEFAULT)
        self.check_replace.bind_property('active', self.entry_replace_old, 'sensitive', GObject.BindingFlags.DEFAULT)
        self.check_replace.bind_property('active', self.entry_replace_new, 'sensitive', GObject.BindingFlags.DEFAULT)
        self.check_capitalization.bind_property('active', self.combo_capitalization, 'sensitive', GObject.BindingFlags.DEFAULT)

    @Gtk.Template.Callback()
    def on_changed(self, widget):
        self.emit('changed', self.get_renaming_rules())

    def get_renaming_rules(self):
        renaming_rules = []

        if self.check_spaces.get_active():
            renaming_rules.append(RenamingRuleSpaces(self.combo_spaces.get_active_id()))

        if self.check_replace.get_active():
            renaming_rules.append(RenamingRuleReplace(self.entry_replace_old.get_text(), self.entry_replace_new.get_text()))

        if self.check_capitalization.get_active():
            renaming_rules.append(RenamingRuleCapitalization(self.combo_capitalization.get_active_id()))

        if self.check_accents.get_active():
            renaming_rules.append(RenamingRuleRemoveAccents())

        if self.check_duplicated.get_active():
            renaming_rules.append(RenamingRuleFixDuplicated())

        return renaming_rules

    def clear(self):
        self.check_spaces.set_active(self._defaults['check_spaces'])
        self.combo_spaces.set_active(self._defaults['combo_spaces'])
        self.check_replace.set_active(self._defaults['check_replace'])
        self.entry_replace_old.set_text(self._defaults['entry_replace_old'])
        self.entry_replace_new.set_text(self._defaults['entry_replace_new'])
        self.check_capitalization.set_active(self._defaults['check_capitalization'])
        self.combo_capitalization.set_active(self._defaults['combo_capitalization'])
        self.check_accents.set_active(self._defaults['check_accents'])
        self.check_duplicated.set_active(self._defaults['check_duplicated'])
