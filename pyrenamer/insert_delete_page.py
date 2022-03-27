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
from pyrenamer.renaming_rules import RenamingRuleInsert, RenamingRuleDelete


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/InsertDeletePage.ui')
class InsertDeletePage(Gtk.Bin):
    __gtype_name__ = 'InsertDeletePage'

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, (object,))
    }

    radio_insert = Gtk.Template.Child()
    box_insert = Gtk.Template.Child()
    entry_insert = Gtk.Template.Child()
    spin_insert_at = Gtk.Template.Child()
    adjustment_spin_insert_at = Gtk.Template.Child()
    check_insert_at_the_end = Gtk.Template.Child()

    radio_delete = Gtk.Template.Child()
    box_delete = Gtk.Template.Child()
    spin_delete_from = Gtk.Template.Child()
    adjustment_spin_delete_from = Gtk.Template.Child()
    spin_delete_to = Gtk.Template.Child()
    adjustment_spin_delete_to = Gtk.Template.Child()
    check_delete_from_the_end = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._defaults = {
            'radio_insert': self.radio_insert.get_active(),
            'entry_insert': self.entry_insert.get_text(),
            'spin_insert_at': self.spin_insert_at.get_value(),
            'check_insert_at_the_end': self.check_insert_at_the_end.get_active(),
            'radio_delete': self.radio_delete.get_active(),
            'spin_delete_from': self.spin_delete_from.get_value(),
            'spin_delete_to': self.spin_delete_to.get_value(),
            'check_delete_from_the_end': self.check_delete_from_the_end.get_active()
        }

        self.radio_insert.bind_property('active', self.box_insert, 'sensitive', GObject.BindingFlags.SYNC_CREATE)
        self.radio_delete.bind_property('active', self.box_delete, 'sensitive', GObject.BindingFlags.SYNC_CREATE)
        self.check_insert_at_the_end.bind_property(
            'active', self.spin_insert_at, 'sensitive',
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.INVERT_BOOLEAN)
        self.spin_delete_to.bind_property('value', self.adjustment_spin_delete_from, 'upper', GObject.BindingFlags.SYNC_CREATE)
        self.spin_delete_from.bind_property('value', self.adjustment_spin_delete_to, 'lower', GObject.BindingFlags.SYNC_CREATE)

    @Gtk.Template.Callback()
    def on_changed(self, widget):
        self.emit('changed', self.get_renaming_rules())

    def get_renaming_rules(self):
        if self.radio_insert.get_active():
            text = self.entry_insert.get_text()
            at_the_end = self.check_insert_at_the_end.get_active()
            at = self.spin_insert_at.get_value_as_int() - 1 if not at_the_end else None
            return [RenamingRuleInsert(text, at, at_the_end)]

        if self.radio_delete.get_active():
            from_ = self.spin_delete_from.get_value_as_int() - 1
            to = self.spin_delete_to.get_value_as_int() - 1
            from_the_end = self.check_delete_from_the_end.get_active()
            return [RenamingRuleDelete(from_, to, from_the_end)]

    def clear(self):
        self.radio_insert.set_active(self._defaults['radio_insert'])
        self.entry_insert.set_text(self._defaults['entry_insert'])
        self.spin_insert_at.set_value(self._defaults['spin_insert_at'])
        self.check_insert_at_the_end.set_active(self._defaults['check_insert_at_the_end'])
        self.radio_delete.set_active(self._defaults['radio_delete'])
        self.spin_delete_from.set_value(self._defaults['spin_delete_from'])
        self.spin_delete_to.set_value(self._defaults['spin_delete_to'])
        self.check_delete_from_the_end.set_active(self._defaults['check_delete_from_the_end'])
