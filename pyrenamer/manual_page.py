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


from gi.repository import Gtk, GObject, Gdk

from pyrenamer.conf import RESOURCE_BASE_PATH
from pyrenamer.renaming_rules import RenamingRuleManual


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/ManualPage.ui')
class ManualPage(Gtk.Bin):
    __gtype_name__ = 'ManualPage'

    __gsignals__ = {
        'next': (GObject.SignalFlags.RUN_LAST, None, ()),
        'previous': (GObject.SignalFlags.RUN_LAST, None, ()),
        'changed': (GObject.SignalFlags.RUN_LAST, None, (object,))
    }

    entry_new_name = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_filename(self, filename):
        self.entry_new_name.set_text(filename)

    @Gtk.Template.Callback()
    def on_changed(self, widget):
        self.emit('changed', self.get_renaming_rules())

    @Gtk.Template.Callback()
    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Page_Up:
            self.emit('previous')
        elif event.keyval in (Gdk.KEY_Page_Down, Gdk.KEY_Return):
            self.emit('next')

    def get_renaming_rules(self):
        return [RenamingRuleManual(self.entry_new_name.get_text())]
