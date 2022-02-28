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

from gi.repository import GObject, Gio, Gdk


class WindowState(GObject.GObject):
    __gtype_name__ = 'WindowState'

    is_maximized = GObject.Property(type=bool, nick='Current window maximized state', default=False)
    x = GObject.Property(type=int, nick='Current window x position', default=-1)
    y = GObject.Property(type=int, nick='Current window y position', default=-1)
    width = GObject.Property(type=int, nick='Current window width', default=-1)
    height = GObject.Property(type=int, nick='Current window height', default=-1)

    def bind(self, window):
        window.connect('configure-event', self.on_configure_event)
        window.connect('window-state-event', self.on_window_state_event)

        application = window.props.application
        settings = application.props.settings
        bind_flags = Gio.SettingsBindFlags.DEFAULT | Gio.SettingsBindFlags.GET_NO_CHANGES
        settings.bind('window-maximized', self, 'is_maximized', bind_flags)
        settings.bind('window-position-x', self, 'x', bind_flags)
        settings.bind('window-position-y', self, 'y', bind_flags)
        settings.bind('window-width', self, 'width', bind_flags)
        settings.bind('window-height', self, 'height', bind_flags)

        if self.props.is_maximized:
            window.maximize()
        else:
            if self.props.x >= 0 and self.props.y >= 0:
                window.move(self.props.x, self.props.y)
            if self.props.width >= 0 and self.props.height >= 0:
                window.resize(self.props.width, self.props.height)

    def on_configure_event(self, window, event):
        if not self.props.is_maximized:
            x, y = window.get_position()
            width, height = window.get_size()
            if x != self.props.x:
                self.props.x = max(x, 0)
            if y != self.props.y:
                self.props.y = max(y, 0)
            if width != self.props.width:
                self.props.width = width
            if height != self.props.height:
                self.props.height = height

    def on_window_state_event(self, window, event):
        is_maximized = bool(event.new_window_state & Gdk.WindowState.MAXIMIZED)
        if is_maximized != self.props.is_maximized:
            self.props.is_maximized = is_maximized
