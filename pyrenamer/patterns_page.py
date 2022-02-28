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

from gi.repository import Gtk, GObject, Gio

from pyrenamer.conf import RESOURCE_BASE_PATH
from pyrenamer.renaming_rules import RenamingRulePattern, RenamingRulePatternImages, RenamingRulePatternMusic


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/PatternsPage.ui')
class PatternsPage(Gtk.Bin):
    __gtype_name__ = 'PatternsPage'

    original_patterns = GObject.Property(type=GObject.TYPE_STRV)
    renamed_patterns = GObject.Property(type=GObject.TYPE_STRV)

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, (object,)),
    }

    grid = Gtk.Template.Child()

    @unique
    class Mode(IntEnum):
        GENERIC = 0
        IMAGES = 1
        MUSIC = 2

    _ORIGINAL_PATTERNS_SETTINGS_KEYS = {
        Mode.GENERIC: 'patterns-original',
        Mode.IMAGES: 'patterns-original-images',
        Mode.MUSIC: 'patterns-original-music'
    }

    _RENAMED_PATTERNS_SETTINGS_KEYS = {
        Mode.GENERIC: 'patterns-renamed',
        Mode.IMAGES: 'patterns-renamed-images',
        Mode.MUSIC: 'patterns-renamed-music'
    }

    _ORIGINAL_PATTERN_TOOLTIP = _("""\
{#}		Numbers
{L}		Letters
{C}		Characters (numbers and letters, not spaces)
{X}		Numbers, letters, and spaces
{@}	Trash""")

    _RENAMED_PATTERN_TOOLTIP = {
        Mode.GENERIC: _("""\
Common replacements:
Use {1} for first matched item, {2} for second, etc...
Use {num} for adding 1, 2, 3... to file names
Use {num2} for adding 01, 02, 03...
Use {num3} for adding 001, 002, 003...
Use {num+10} for adding 10, 11, 12...
Use {num2+10} for adding 010, 011, 012...
Use {dir} for getting the current directory

Some today date replacements:
{date}			22Feb2022
{year}			2022
{month}		02
{monthname}	February
{monthsimp}	Feb
{day}			22
{dayname}		Tuesday
{daysimp}		Tue

Random number replacements:
{rand} is a random number between 0 and 100.
{rand,3} is a random number between 0 and 100 of 3 digits (012)
{rand500} is a random number between 0 and 500
{rand10-20} is a random number between 10 and 20
{rand20,5} is a random number between 0 and 20 of 5 digits (00012)""")
    }

    _RENAMED_PATTERN_TOOLTIP[Mode.IMAGES] = _("""\
Image metadata replacements:
{imagewidth}			4272
{imageheight}			2848
{cameramaker}			Canon
{cameramodel}			Canon EOS 1100D
{imagedate}			22Feb2022
{imageyear}			2022
{imagemonth}			02
{imagemonthname}		February
{imagemonthsimp}		Feb
{imageday}				22
{imagedayname}		Tuesday
{imagedaysimp}		Tue
{imagetime}			20_15_38
{imagehour}			20
{imageminute}			15
{imagesecond}			38

""") + _RENAMED_PATTERN_TOOLTIP[Mode.GENERIC]

    _RENAMED_PATTERN_TOOLTIP[Mode.MUSIC] = _("""\
Music metadata replacements:
{artist}			Queen
{title}			Bohemian Rhapsody
{album}		A Night at the Opera
{track}			11
{tracktotal}	12
{myear}		1975
{genre}			Rock

""") + _RENAMED_PATTERN_TOOLTIP[Mode.GENERIC]

    def __init__(self, settings, mode, **kwargs):
        super().__init__(**kwargs)
        self._mode = mode

        self.pattern_selector_original = PatternSelector(
            settings, self._ORIGINAL_PATTERNS_SETTINGS_KEYS[mode], self._ORIGINAL_PATTERN_TOOLTIP)
        self.pattern_selector_original.connect('changed', self.on_changed)
        self.grid.attach(self.pattern_selector_original, 1, 1, 1, 1)

        self.pattern_selector_renamed = PatternSelector(
            settings, self._RENAMED_PATTERNS_SETTINGS_KEYS[mode], self._RENAMED_PATTERN_TOOLTIP[mode])
        self.pattern_selector_renamed.connect('changed', self.on_changed)
        self.grid.attach(self.pattern_selector_renamed, 1, 2, 1, 1)

    def on_changed(self, combo):
        self.emit('changed', self.get_renaming_rules())

    def get_renaming_rules(self):
        if self._mode == self.Mode.GENERIC:
            renaming_rule_cls = RenamingRulePattern
        elif self._mode == self.Mode.IMAGES:
            renaming_rule_cls = RenamingRulePatternImages
        elif self._mode == self.Mode.MUSIC:
            renaming_rule_cls = RenamingRulePatternMusic
        return [
            renaming_rule_cls(self.pattern_selector_original.active_pattern,
                              self.pattern_selector_renamed.active_pattern)]

    def clear(self):
        self.pattern_selector_original.combo_pattern.set_active(0)
        self.pattern_selector_renamed.combo_pattern.set_active(0)


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/PatternSelector.ui')
class PatternSelector(Gtk.Box):
    __gtype_name__ = 'PatternSelector'

    patterns = GObject.Property(type=GObject.TYPE_STRV)

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    combo_pattern = Gtk.Template.Child()
    button_save_pattern = Gtk.Template.Child()
    button_edit_patterns = Gtk.Template.Child()

    def __init__(self, settings, patterns_settings_key, tooltip, **kwargs):
        super().__init__(**kwargs)
        self._settings = settings
        self._patterns_settings_key = patterns_settings_key

        settings.bind(patterns_settings_key, self, 'patterns', Gio.SettingsBindFlags.DEFAULT)
        self.connect('notify::patterns', self.on_patterns_changed)

        self.combo_pattern.set_tooltip_text(tooltip)
        self._combo_handler_id = self.combo_pattern.connect('changed', self.on_changed)
        self._update_patterns_combo()
        self._active_pattern = self.combo_pattern.get_active_text()

    @GObject.Property(type=str, default='', flags=GObject.ParamFlags.READABLE)
    def active_pattern(self):
        return self._active_pattern

    def on_patterns_changed(self, obj, prop):
        self._update_patterns_combo()

    def _update_patterns_combo(self):
        self._active_pattern = self.combo_pattern.get_active_text()
        active_index = -1

        with self.combo_pattern.handler_block(self._combo_handler_id):
            self.combo_pattern.remove_all()
            for index, pattern in enumerate(self.patterns):
                self.combo_pattern.append_text(pattern)
                if pattern == self._active_pattern:
                    active_index = index

        self.combo_pattern.set_active(active_index if active_index >= 0 else 0)

    def on_changed(self, combo):
        self._active_pattern = self.combo_pattern.get_active_text()
        self.button_save_pattern.set_sensitive(self._active_pattern not in self.patterns)

        self.emit('changed')

    @Gtk.Template.Callback()
    def on_button_save_pattern_clicked(self, button):
        if self.active_pattern and self.active_pattern not in self.patterns:
            self.patterns = [*self.patterns, self.active_pattern]

    @Gtk.Template.Callback()
    def on_button_edit_patterns_clicked(self, button):
        dialog = PatternsEditorDialog(self._settings, self._patterns_settings_key, transient_for=self.get_toplevel())
        dialog.present()


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/PatternsEditorDialog.ui')
class PatternsEditorDialog(Gtk.Dialog):
    __gtype_name__ = 'PatternsEditorDialog'

    patterns = GObject.Property(type=GObject.TYPE_STRV)

    tree_view_patterns = Gtk.Template.Child()
    tree_selection_patterns = Gtk.Template.Child()
    list_store_patterns = Gtk.Template.Child()
    button_add = Gtk.Template.Child()
    button_remove = Gtk.Template.Child()
    button_edit = Gtk.Template.Child()
    button_up = Gtk.Template.Child()
    button_down = Gtk.Template.Child()

    def __init__(self, settings, patterns_settings_key, **kwargs):
        super().__init__(**kwargs)

        settings.bind(patterns_settings_key, self, 'patterns', GObject.BindingFlags.DEFAULT)
        self.connect('notify::patterns', self.on_patterns_changed)

        self._update_patterns_tree_view()

        self.show_all()

    def on_patterns_changed(self, obj, prop):
        self._update_patterns_tree_view()

    def _update_patterns_tree_view(self):
        model, selected_iter = self.tree_selection_patterns.get_selected()
        selected_pattern = model[selected_iter][0] if selected_iter else ''

        self.list_store_patterns.clear()
        for pattern in self.patterns:
            iter = self.list_store_patterns.append((pattern,))
            if pattern == selected_pattern:
                selected_iter = iter

        if selected_iter:
            self.tree_selection_patterns.select_iter(selected_iter)

    def _get_patterns_from_model(self):
        patterns = []
        self.list_store_patterns.foreach(lambda model, path, iter: patterns.append(model[iter][0]))
        return patterns

    def _select_pattern(self, pattern):
        iter = self.list_store_patterns.get_iter_first()
        while iter:
            if self.list_store_patterns[iter][0] == pattern:
                self.tree_selection_patterns.select_iter(iter)
                return
            iter = self.list_store_patterns.iter_next(iter)

    @Gtk.Template.Callback()
    def on_tree_selection_patterns_changed(self, tree_selection):
        model, iter = tree_selection.get_selected()
        self.button_remove.set_sensitive(bool(iter))
        self.button_edit.set_sensitive(bool(iter))
        self.button_up.set_sensitive(bool(iter) and int(model.get_string_from_iter(iter)) > 0)
        self.button_down.set_sensitive(bool(iter) and int(model.get_string_from_iter(iter)) < len(model) - 1)

    @Gtk.Template.Callback()
    def on_tree_view_patterns_button_press_event(self, tree_view, event):
        if self.tree_view_patterns.get_path_at_pos(int(event.x), int(event.y)) is None:
            self.tree_selection_patterns.unselect_all()

    @Gtk.Template.Callback()
    def on_button_add_clicked(self, button):
        dialog = AddPatternDialog(transient_for=self)
        response = dialog.run()
        new_pattern = dialog.pattern if response == Gtk.ResponseType.OK else None
        dialog.destroy()

        if not new_pattern:
            return

        if new_pattern in self.patterns:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=_("Repeated pattern"),
            )
            dialog.format_secondary_text(_("The pattern '{}' already exists.".format(new_pattern)))
            dialog.run()
            dialog.destroy()
            self._select_pattern(new_pattern)
            return

        model, selected_iter = self.tree_selection_patterns.get_selected()
        if selected_iter:
            iter = model.insert_after(selected_iter, (new_pattern,))
        else:
            iter = model.append((new_pattern,))
        self.tree_selection_patterns.select_iter(iter)

        self.patterns = self._get_patterns_from_model()

    @Gtk.Template.Callback()
    def on_button_remove_clicked(self, button):
        model, iter = self.tree_selection_patterns.get_selected()
        if iter:
            model.remove(iter)
            self.patterns = self._get_patterns_from_model()

    @Gtk.Template.Callback()
    def on_button_edit_clicked(self, button):
        model, iter = self.tree_selection_patterns.get_selected()
        if iter:
            path = model.get_path(iter)
            self.tree_view_patterns.set_cursor(path, self.tree_view_patterns.get_column(0), True)

    @Gtk.Template.Callback()
    def on_cell_renderer_text_pattern_edited(self, cell_renderer_text, path, new_text):
        iter = self.list_store_patterns.get_iter(path)
        self.list_store_patterns[iter][0] = new_text
        self.patterns = self._get_patterns_from_model()

    @Gtk.Template.Callback()
    def on_button_up_clicked(self, button):
        model, iter = self.tree_selection_patterns.get_selected()
        if iter:
            pos = int(model.get_string_from_iter(iter))
            if pos > 0:
                iter_previous = model.get_iter_from_string(str(pos - 1))
                if iter_previous:
                    model.swap(iter, iter_previous)
                    self.patterns = self._get_patterns_from_model()

    @Gtk.Template.Callback()
    def on_button_down_clicked(self, button):
        model, iter = self.tree_selection_patterns.get_selected()
        if iter:
            iter_next = model.iter_next(iter)
            if iter_next:
                model.swap(iter, iter_next)
                self.patterns = self._get_patterns_from_model()

    @Gtk.Template.Callback()
    def on_response(self, dialog, response_id):
        self.destroy()


@Gtk.Template(resource_path=f'{RESOURCE_BASE_PATH}/ui/AddPatternDialog.ui')
class AddPatternDialog(Gtk.Dialog):
    __gtype_name__ = 'AddPatternDialog'

    pattern = GObject.Property(type=str, default='')

    entry_pattern = Gtk.Template.Child()
    button_ok = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bind_property('pattern', self.entry_pattern, 'text', GObject.BindingFlags.BIDIRECTIONAL)
        self.entry_pattern.bind_property('text-length', self.button_ok, 'sensitive', GObject.BindingFlags.SYNC_CREATE)

        self.show_all()
