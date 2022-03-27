# -*- coding: utf-8 -*-

"""
Copyright (C) 2006-2008 Adolfo González Blázquez <code@infinicode.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

If you find any bugs or have any suggestions email: code@infinicode.org
"""

try:
    import pygtk
    pygtk.require('2.0')
except:
      print "PyGtk 2.0 or later required for this app to run"
      raise SystemExit

try:
    import gtk
    import gtk.glade
    import gobject
except:
    raise SystemExit

try:
    import gconf
    HAS_GCONF = True
except:
    HAS_GCONF = False


import treefilebrowser
import pyrenamer_filefuncs as renamerfilefuncs
import pyrenamer_globals as pyrenamerglob
import pyrenamer_tooltips as tooltips
import pyrenamer_prefs
import pyrenamer_pattern_editor
import pyrenamer_menu_cb
import pyrenamer_undo

import threading
from os import path as ospath

import locale
import gettext

from gettext import gettext as _
gettext.bindtextdomain(pyrenamerglob.name, pyrenamerglob.locale_dir)
gettext.textdomain(pyrenamerglob.name)
gtk.glade.bindtextdomain(pyrenamerglob.name, pyrenamerglob.locale_dir)
gtk.glade.textdomain(pyrenamerglob.name)

class pyRenamer:

    def __init__(self, rootdir=None, startdir=None):

    	global HAS_GCONF

        self.menu_cb = pyrenamer_menu_cb.PyrenamerMenuCB(self)

        # Load default icons from current theme
        icon_theme = self.get_default_icons()

        # If icon theme changes, reload icons
        icon_theme.connect("changed", self.icon_theme_changed)


        # Main variables
        self.count = 0
        self.populate_id = []
        self.listing = []
        self.listing_thread = None
        self.ignore_errors = False

        # Patterns saving variables
        self.patterns = {}
        self.patterns_default = {
            "main_ori": "",
            "main_dest": "",
            "images_ori": "",
            "images_dest": "",
            "music_ori": "",
            "music_dest": "" }


        # Window geometry vars
        self.window_maximized = False
        self.window_width = 500
        self.window_height = 500
        self.window_posx = 0
        self.window_posy = 0
        self.pane_position = 250

        # Directories variables
        self.home = pyrenamerglob.home_dir
        self.root_dir = '/'
        self.active_dir = self.home

        # Options
        self.options_shown = False
        self.filedir = 0        # 0: Files; 1: Dirs; 2: Both
        self.keepext = False
        self.autopreview = False

        # Read preferences using Gconf
        if HAS_GCONF:
            self.prefs = pyrenamer_prefs.PyrenamerPrefs(self)
            self.prefs.preferences_read()

        # Process commanline
        if rootdir != None: self.root_dir = rootdir
        if startdir != None: self.active_dir = startdir

        # Init Glade stuff
        self.glade_tree = gtk.glade.XML(pyrenamerglob.gladefile, "main_window")

        # Get some widgets
        self.main_window = self.glade_tree.get_widget("main_window")
        self.main_hpaned = self.glade_tree.get_widget("main_hpaned")
        self.selected_files, selected_files_scrolled = self.create_selected_files_treeview()


        self.statusbar = self.glade_tree.get_widget("statusbar")
        self.notebook = self.glade_tree.get_widget("notebook")
        self.clear_button = self.glade_tree.get_widget("clear_button")
        self.preview_button = self.glade_tree.get_widget("preview_button")
        self.rename_button = self.glade_tree.get_widget("rename_button")

        self.original_pattern = self.glade_tree.get_widget("original_pattern")
        self.renamed_pattern = self.glade_tree.get_widget("renamed_pattern")
        self.original_pattern_combo = self.glade_tree.get_widget("original_pattern_combo")
        self.renamed_pattern_combo = self.glade_tree.get_widget("renamed_pattern_combo")

        self.subs_spaces = self.glade_tree.get_widget("subs_spaces")
        self.subs_capitalization = self.glade_tree.get_widget("subs_capitalization")
        self.subs_spaces_combo = self.glade_tree.get_widget("subs_spaces_combo")
        self.subs_capitalization_combo = self.glade_tree.get_widget("subs_capitalization_combo")
        self.subs_replace = self.glade_tree.get_widget("subs_replace")
        self.subs_replace_orig = self.glade_tree.get_widget("subs_replace_orig")
        self.subs_replace_new = self.glade_tree.get_widget("subs_replace_new")
        self.subs_replace_label = self.glade_tree.get_widget("subs_replace_label")
        self.subs_accents = self.glade_tree.get_widget("subs_accents")
        self.subs_duplicated = self.glade_tree.get_widget("subs_duplicated")

        self.insert_radio = self.glade_tree.get_widget("insert_radio")
        self.insert_entry = self.glade_tree.get_widget("insert_entry")
        self.insert_pos = self.glade_tree.get_widget("insert_pos")
        self.insert_end = self.glade_tree.get_widget("insert_end")

        self.delete_radio = self.glade_tree.get_widget("delete_radio")
        self.delete_from = self.glade_tree.get_widget("delete_from")
        self.delete_to = self.glade_tree.get_widget("delete_to")
        self.delete_end = self.glade_tree.get_widget("delete_end")

        self.manual = self.glade_tree.get_widget("manual")
        self.menu_clear_preview = self.glade_tree.get_widget("menu_clear_preview")
        self.menu_rename = self.glade_tree.get_widget("menu_rename")
        self.menu_show_options = self.glade_tree.get_widget("menu_show_options")

        self.menu_undo = self.glade_tree.get_widget("menu_undo")
        self.menu_redo = self.glade_tree.get_widget("menu_redo")

        self.menu_music = self.glade_tree.get_widget("menu_music")

        self.images_original_pattern = self.glade_tree.get_widget("images_original_pattern")
        self.images_renamed_pattern = self.glade_tree.get_widget("images_renamed_pattern")
        self.images_original_pattern_combo = self.glade_tree.get_widget("images_original_pattern_combo")
        self.images_renamed_pattern_combo = self.glade_tree.get_widget("images_renamed_pattern_combo")

        self.music_original_pattern = self.glade_tree.get_widget("music_original_pattern")
        self.music_renamed_pattern = self.glade_tree.get_widget("music_renamed_pattern")
        self.music_original_pattern_combo = self.glade_tree.get_widget("music_original_pattern_combo")
        self.music_renamed_pattern_combo = self.glade_tree.get_widget("music_renamed_pattern_combo")

        # Options panel
        self.file_pattern = self.glade_tree.get_widget("file_pattern")
        self.add_recursive = self.glade_tree.get_widget("add_recursive")
        self.options_button = self.glade_tree.get_widget("options_button")
        self.options_vbox = self.glade_tree.get_widget("options_vbox")
        self.options_label = self.glade_tree.get_widget("options_label")
        self.options_close_button = self.glade_tree.get_widget("options_close_button")
        self.filedir_combo = self.glade_tree.get_widget("filedir_combo")
        self.pattern_hbox = self.glade_tree.get_widget("pattern_hbox")
        self.add_recursive = self.glade_tree.get_widget("add_recursive")
        self.extensions_check = self.glade_tree.get_widget("extensions_check")
        self.autopreview_check = self.glade_tree.get_widget("autopreview_check")

        self.options_panel_state(self.options_shown)
        self.menu_show_options.set_active(self.options_shown)
        self.filedir_combo.set_active(self.filedir)
        self.extensions_check.set_active(self.keepext)
        self.autopreview_check.set_active(self.autopreview)


        self.statusbar_context = self.statusbar.get_context_id("file_renamer")

        # Get Glade defined signals
        signals = { "on_main_window_destroy": self.on_main_quit,
                    "on_main_window_window_state_event": self.on_main_window_window_state_event,
                    "on_main_window_configure_event": self.on_main_window_configure_event,
                    "on_main_hpaned_notify": self.on_main_hpaned_notify,

                    "on_file_pattern_changed": self.on_file_pattern_changed,
                    "on_original_pattern_changed": self.on_original_pattern_changed,
                    "on_renamed_pattern_changed": self.on_renamed_pattern_changed,
                    "on_pattern_ori_save_clicked": self.on_pattern_ori_save_clicked,
                    "on_pattern_ori_edit_clicked": self.on_pattern_ori_edit_clicked,
                    "on_pattern_dest_save_clicked": self.on_pattern_dest_save_clicked,
                    "on_pattern_dest_edit_clicked": self.on_pattern_dest_edit_clicked,
                    "on_original_pattern_combo_changed": self.on_original_pattern_combo_changed,
                    "on_renamed_pattern_combo_changed": self.on_renamed_pattern_combo_changed,

                    "on_preview_button_clicked": self.on_preview_button_clicked,
                    "on_clean_button_clicked": self.on_clean_button_clicked,
                    "on_rename_button_clicked": self.on_rename_button_clicked,
                    "on_exit_button_clicked": self.on_main_quit,

                    "on_options_button_clicked": self.on_options_button_clicked,
                    "on_add_recursive_toggled": self.prefs.on_add_recursive_toggled,
                    "on_filedir_combo_changed": self.prefs.on_filedir_combo_changed,
                    "on_extensions_check_toggled": self.prefs.on_extensions_check_toggled,
                    "on_autopreview_check_toggled": self.prefs.on_autopreview_check_toggled,

                    "on_menu_preview_activate": self.on_preview_button_clicked,
                    "on_menu_rename_activate": self.on_rename_button_clicked,
                    "on_menu_load_names_from_file_activate": self.on_menu_load_names_from_file_activate,
                    "on_menu_clear_preview_activate": self.on_clean_button_clicked,

                    "on_menu_undo_activate": self.menu_cb.on_menu_undo_activate,
                    "on_menu_redo_activate": self.menu_cb.on_menu_redo_activate,
                    "on_cut_activate": self.on_cut_activate,
                    "on_copy_activate": self.on_copy_activate,
                    "on_paste_activate": self.on_paste_activate,
                    "on_clear_activate": self.on_clear_activate,
                    "on_select_all_activate": self.on_select_all_activate,
                    "on_select_nothing_activate": self.on_select_nothing_activate,
                    "on_preferences_activate": self.on_preferences_activate,

                    "on_menu_refresh_activate": self.menu_cb.on_menu_refresh_activate,
                    "on_menu_patterns_activate": self.menu_cb.on_menu_patterns_activate,
                    "on_menu_substitutions_activate": self.menu_cb.on_menu_substitutions_activate,
                    "on_menu_insert_activate": self.menu_cb.on_menu_insert_activate,
                    "on_menu_manual_activate": self.menu_cb.on_menu_manual_activate,
                    "on_menu_images_activate": self.menu_cb.on_menu_images_activate,
                    "on_menu_music_activate": self.menu_cb.on_menu_music_activate,
                    "on_menu_show_options_activate": self.menu_cb.on_menu_show_options_activate,

                    "on_subs_spaces_toggled": self.on_subs_spaces_toggled,
                    "on_subs_capitalization_toggled": self.on_subs_capitalization_toggled,
                    "on_subs_spaces_combo_changed": self.on_subs_spaces_combo_changed,
                    "on_subs_capitalization_combo_changed": self.on_subs_capitalization_combo_changed,
                    "on_subs_replace_toggled": self.on_subs_replace_toggled,
                    "on_subs_replace_orig_changed": self.on_subs_replace_orig_changed,
                    "on_subs_replace_new_changed": self.on_subs_replace_new_changed,
                    "on_subs_accents_toggled": self.on_subs_accents_toggled,
                    "on_subs_duplicated_toggled": self.on_subs_duplicated_toggled,

                    "on_insert_radio_toggled": self.on_insert_radio_toggled,
                    "on_insert_entry_changed": self.on_insert_entry_changed,
                    "on_insert_pos_changed": self.on_insert_pos_changed,
                    "on_insert_end_toggled": self.on_insert_end_toggled,

                    "on_delete_radio_toggled": self.on_delete_radio_toggled,
                    "on_delete_from_changed": self.on_delete_from_changed,
                    "on_delete_to_changed": self.on_delete_to_changed,
                    "on_delete_end_toggled": self.on_delete_end_toggled,

                    "on_images_original_pattern_changed": self.on_images_original_pattern_changed,
                    "on_images_renamed_pattern_changed": self.on_images_renamed_pattern_changed,
                    "on_images_ori_save_clicked": self.on_images_ori_save_clicked,
                    "on_images_ori_edit_clicked": self.on_images_ori_edit_clicked,
                    "on_images_dest_save_clicked": self.on_images_dest_save_clicked,
                    "on_images_dest_edit_clicked": self.on_images_dest_edit_clicked,
                    "on_images_original_pattern_combo_changed": self.on_images_original_pattern_combo_changed,
                    "on_images_renamed_pattern_combo_changed": self.on_images_renamed_pattern_combo_changed,

                    "on_music_original_pattern_changed": self.on_music_original_pattern_changed,
                    "on_music_renamed_pattern_changed": self.on_music_renamed_pattern_changed,
                    "on_music_ori_save_clicked": self.on_music_ori_save_clicked,
                    "on_music_ori_edit_clicked": self.on_music_ori_edit_clicked,
                    "on_music_dest_save_clicked": self.on_music_dest_save_clicked,
                    "on_music_dest_edit_clicked": self.on_music_dest_edit_clicked,
                    "on_music_original_pattern_combo_changed": self.on_music_original_pattern_combo_changed,
                    "on_music_renamed_pattern_combo_changed": self.on_music_renamed_pattern_combo_changed,

                    "on_menu_quit_activate": self.on_main_quit,
                    "on_menu_about_activate": self.about_info,

                    "on_notebook_switch_page": self.on_notebook_switch_page,

                    "on_manual_key_press_event": self.on_manual_key_press_event,
                    "on_quit_button_clicked": self.on_main_quit }

        self.glade_tree.signal_autoconnect(signals)

        # Create ProgressBar and add it to the StatusBar. Add also a Stop icon
        self.progressbar = gtk.ProgressBar()
        self.progressbar.set_pulse_step(0.01)
        self.progressbar.set_size_request(-1,14)

        self.progressbar_vbox = gtk.VBox()
        self.progressbar_vbox.pack_start(self.progressbar, 0, 0)
        self.progressbar_vbox.set_homogeneous(True)

        self.stop_button = gtk.Button()
        self.stop_button.set_relief(gtk.RELIEF_NONE)

        stop_image = gtk.Image()
        stop_image.set_from_file(pyrenamerglob.pixmaps_dir+'/stop.png')

        self.stop_button.connect("clicked", self.on_stop_button_clicked)
        self.stop_button.set_image(stop_image)

        self.statusbar.pack_start(self.stop_button,0,0)
        self.statusbar.pack_start(self.progressbar_vbox,0,0)
        self.statusbar.set_size_request(-1,20)
        self.statusbar.show_all()
        self.stop_button.hide()

        # Init main window
        self.main_window.set_title(pyrenamerglob.name_long)
        self.main_window.set_icon_from_file(pyrenamerglob.icon)
        self.main_window.move(self.window_posx, self.window_posy)
        self.main_hpaned.set_position(self.pane_position)
        self.main_window.resize(self.window_width, self.window_height)
        if self.window_maximized: self.main_window.maximize()

        # Init TreeFileBrowser
        self.file_browser = treefilebrowser.TreeFileBrowser(self.root_dir)
        self.file_browser_view = self.file_browser.get_view()
        file_browser_scrolled = self.file_browser.get_scrolled()
        signal = self.file_browser.connect("cursor-changed", self.dir_selected)

        # Add dirs and files tomain window
        self.main_hpaned.pack1(file_browser_scrolled, resize=True, shrink=False)
        self.main_hpaned.pack2(selected_files_scrolled, resize=True, shrink=False)

        # Add signal for manual entry changed
        self.manual_signal = self.manual.connect("changed", self.on_manual_changed)

        # Create model and add dirs
        self.create_model()

        #  Set cursor on selected dir
        try:
            # Check if the dir is hidden
            if "/." in (self.active_dir or self.root_dir):
                self.file_browser.set_show_hidden(True)

            # Check if paths are correct
            if not self.file_browser.check_active_dir(self.active_dir):
                self.active_dir = self.home
                if not self.file_browser.check_active_dir(self.active_dir):
                    self.active_dir = self.root_dir
        except:
            self.active_dir = self.home
        self.file_browser.set_active_dir(self.active_dir)

        # Init comboboxes
        self.subs_spaces_combo.set_active(0)
        self.subs_capitalization_combo.set_active(0)

        # Init some menu items
        self.menu_rename.set_sensitive(False)
        self.menu_clear_preview.set_sensitive(False)

        # Init delete radio buttons
        self.delete_from.set_sensitive(False)
        self.delete_to.set_sensitive(False)
        self.delete_end.set_sensitive(False)

        # Init pattern comboboxes
        self.populate_pattern_combos()

        # Init tooltips
        tips = tooltips.ToolTips(self.column_preview)
        tips.add_view(self.selected_files)

        # Hide music tab if necessary
        if not pyrenamerglob.have_hachoir and not pyrenamerglob.have_eyed3:
            self.notebook.get_nth_page(5).hide()
            self.menu_music.hide()
        if pyrenamerglob.have_hachoir: print "Using hachoir for music renaming."
        elif pyrenamerglob.have_eyed3: print "Using eyed3 for music renaming."

        # Init the undo/redo manager
        self.undo_manager = pyrenamer_undo.PyrenamerUndo()
        self.menu_undo.set_sensitive(False)
        self.menu_redo.set_sensitive(False)



#---------------------------------------------------------------------------------------
# Model and View stuff

    def create_selected_files_treeview(self):
    	""" Create the TreeView and the ScrolledWindow for the selected files """
        view = gtk.TreeView()
        view.set_headers_visible(True)
        view.set_enable_search(True)
        view.set_reorderable(False)
        view.set_rules_hint(True)
        view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        view.connect("cursor-changed", self.on_selected_files_cursor_changed)

        # Create scrollbars around the view
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrolled.add(view)
        scrolled.show()

        return view, scrolled


    def create_model(self):
    	""" Create the model to hold the needed data
        Model = [file, /path/to/file, newfilename, /path/to/newfilename] """
        self.file_selected_model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gtk.gdk.Pixbuf)
        self.selected_files.set_model(self.file_selected_model)

        renderer0 = gtk.CellRendererPixbuf()
        column0 = gtk.TreeViewColumn('', renderer0, pixbuf=4)
        #column0.set_resizable(True)
        self.selected_files.append_column(column0)

        renderer1 = gtk.CellRendererText()
        column1 = gtk.TreeViewColumn(_("Original file name"), renderer1, text=0)
        #column1.set_resizable(True)
        self.selected_files.append_column(column1)

        renderer2 = gtk.CellRendererText()
        column2 = gtk.TreeViewColumn(_("Renamed file name"), renderer2, text=2)
        self.column_preview = column2
        #column2.set_resizable(True)
        self.selected_files.append_column(column2)

        self.selected_files.show()


    def rename_rows(self, model, path, iter, user_data):
    	""" This function is called by foreach to rename files on every row """
    	ori = model.get_value(iter, 1)
    	new = model.get_value(iter, 3)

        if new != None and new != '':
            result, error = renamerfilefuncs.rename_file(ori, new)
            if not result:
                if not self.ignore_errors:
                    self.display_error_dialog(_("Could not rename file %s to %s\n%s") % (ori, new, error))
            else:
                self.undo_manager.add(ori, new)


    def preview_rename_rows(self, model, path, iter, paths):
    	""" Called when Preview button is clicked.
    	Get new names and paths and add it to the model """

        if (paths != None) and (path not in paths) and (paths != []):
            # Preview only selected rows (if we're not on manual rename)
            return

        # Get current values
        name = model.get_value(iter, 0)
        path = model.get_value(iter, 1)
        newname = name
        newpath = path

        # Keep extension (not valid on manual rename!)
        if self.keepext and self.notebook.get_current_page() != 3:
            ename, epath, ext = renamerfilefuncs.cut_extension(newname, newpath)
            if ext != '':
                newname = ename
                newpath = epath

        if self.notebook.get_current_page() == 0:
            # Replace using patterns
            pattern_ini = self.original_pattern.get_text()
            pattern_end = self.renamed_pattern.get_text()
            newname, newpath = renamerfilefuncs.rename_using_patterns(newname, newpath, pattern_ini, pattern_end, self.count)

        elif self.notebook.get_current_page() == 1:
            # Replace spaces
            if self.subs_spaces.get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_spaces(newname, newpath, self.subs_spaces_combo.get_active())

            # Replace orig with new
            if self.subs_replace.get_active() and newname != None:
                orig = self.subs_replace_orig.get_text()
                new = self.subs_replace_new.get_text()
                newname, newpath = renamerfilefuncs.replace_with(newname, newpath, orig, new)

            # Replace capitalization
            if self.subs_capitalization.get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_capitalization(newname, newpath, self.subs_capitalization_combo.get_active())

            # Replace accents
            if self.subs_accents.get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_accents(newname, newpath)

            # Fix duplicated symbols
            if self.subs_duplicated.get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_duplicated(newname, newpath)

        elif self.notebook.get_current_page() == 2:
            # Insert / delete
            if self.insert_radio.get_active():
                text = self.insert_entry.get_text()
                if text != "":
                    if self.insert_end.get_active():
                        pos = None
                    else:
                        pos = int(self.insert_pos.get_value())-1
                    newname, newpath = renamerfilefuncs.insert_at(newname, newpath, text, pos)
            elif self.delete_radio.get_active():
                ini = int(self.delete_from.get_value())-1
                to = int(self.delete_to.get_value())-1
                end = self.delete_end.get_active()
                newname, newpath = renamerfilefuncs.delete_from(newname, newpath, ini, to, end)

        elif self.notebook.get_current_page() == 3:
            # Manual rename
            self.selected_files.get_selection().set_mode(gtk.SELECTION_SINGLE)
            nmodel, niter = self.selected_files.get_selection().get_selected()
            if niter != None:
                if nmodel.get_value(niter,0) == name:
                    newname = self.manual.get_text()
                    newpath = renamerfilefuncs.get_new_path(newname, path)
                else:
                    newname = model.get_value(iter, 2)
                    newpath = model.get_value(iter, 3)
            self.selected_files.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        elif self.notebook.get_current_page() == 4:
            # Replace images using patterns
            pattern_ini = self.images_original_pattern.get_text()
            pattern_end = self.images_renamed_pattern.get_text()
            newname, newpath = renamerfilefuncs.rename_using_patterns(newname, newpath, pattern_ini, pattern_end, self.count)
            newname, newpath = renamerfilefuncs.replace_images(name, path, newname, newpath)

        elif self.notebook.get_current_page() == 5 and (pyrenamerglob.have_hachoir or pyrenamerglob.have_eyed3):
            # Replace music using patterns
            pattern_ini = self.music_original_pattern.get_text()
            pattern_end = self.music_renamed_pattern.get_text()
            newname, newpath = renamerfilefuncs.rename_using_patterns(newname, newpath, pattern_ini, pattern_end, self.count)
            if pyrenamerglob.have_hachoir:
                newname, newpath = renamerfilefuncs.replace_music_hachoir(name, path, newname, newpath)
            elif pyrenamerglob.have_eyed3:
                newname, newpath = renamerfilefuncs.replace_music_eyed3(name, path, newname, newpath)


        # Add the kept extension
        if self.keepext and self.notebook.get_current_page() != 3 and (newname and newpath) != '':
            if ext != '': newname, newpath = renamerfilefuncs.add_extension(newname, newpath, ext)

        # Set new values on model
        if newname != '' and newname != None:
            model.set_value(iter, 2, newname)
            model.set_value(iter, 3, newpath)
        else:
            model.set_value(iter, 2, None)
            model.set_value(iter, 3, None)
        self.count += 1


    def preview_selected_row(self):
        """ Preview just selected row """

        # Get values of current row
        model, iter = self.selected_files.get_selection().get_selected()
        name = model.get_value(iter, 0)
        path = model.get_value(iter, 1)
        if iter != None:
            newname = self.manual.get_text()
            if newname != name:
                newpath = renamerfilefuncs.get_new_path(newname, path)
            else:
                newname = None
                newpath = None

         # Set new values on model
        if newname != '' and newname != None:
            model.set_value(iter, 2, newname)
            model.set_value(iter, 3, newpath)
        else:
            model.set_value(iter, 2, None)
            model.set_value(iter, 3, None)
        self.count += 1


    def preview_clear(self, model, path, iter, paths):
        """ Clean a row """

        if (paths != None) and (path not in paths) and (paths != []):
            return

        model.set_value(iter, 2, None)
        model.set_value(iter, 3, None)


    def enable_rename_and_clean(self, model, path, iter):
        """ Check if the rename button and menu should be enabled """
        val = model.get_value(iter, 2) != None
        if path[0] > 0:
            prev = self.rename_button.get_property("sensitive")
        else:
            prev = False

        self.rename_button.set_sensitive(val or prev)
        self.menu_rename.set_sensitive(val or prev)
        self.clear_button.set_sensitive(val or prev)
        self.menu_clear_preview.set_sensitive(val or prev)

        return False


#---------------------------------------------------------------------------------------
# Callbacks


    def on_selected_files_cursor_changed(self, treeview):
        """ Clicked a file """

        if self.notebook.get_current_page() == 3:
            # Manual rename
            try:
                self.selected_files.get_selection().set_mode(gtk.SELECTION_SINGLE)
                model, iter = treeview.get_selection().get_selected()
                name = model.get_value(iter,0)
                newname = model.get_value(iter,2)
                if newname != None:
                    self.manual.set_text(newname)
                else:
                    self.manual.set_text(name)
            except: pass


    def on_stop_button_clicked(self, widget):
    	""" The stop button on Statusbar.
    	Stop adding items to the selected files list and show information on statusbar """
    	self.populate_stop()


    def on_main_window_window_state_event(self, window, event):
    	""" Thrown when window is maximized or demaximized """
        if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
                self.window_maximized = True
                self.statusbar.set_has_resize_grip(False)
            else:
                self.window_maximized = False
                self.statusbar.set_has_resize_grip(True)


    def on_main_window_configure_event(self, window, event):
        """ Saving window size to avoid losing data when it gets destroyed """
        self.window_width, self.window_height = self.main_window.get_size()
        self.window_posx, self.window_posy = self.main_window.get_position()


    def on_rename_button_clicked(self, widget):
    	""" For everyrow rename the files as requested """

        self.undo_manager.clean()
        self.menu_undo.set_sensitive(True)
        self.menu_redo.set_sensitive(False)
        self.file_selected_model.foreach(self.rename_rows, None)
        self.dir_reload_current()
        self.clear_button.set_sensitive(False)
        self.menu_clear_preview.set_sensitive(False)
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        self.ignore_errors = False


    def on_preview_button_clicked(self, widget):
    	""" Set the item count to zero and get new names and paths for files on model """
        self.count = 0

        # Get selected rows and execute rename function
        model, paths = self.selected_files.get_selection().get_selected_rows()
        self.file_selected_model.foreach(self.preview_rename_rows, paths)

        self.selected_files.columns_autosize()
        self.clear_button.set_sensitive(True)
        self.menu_clear_preview.set_sensitive(True)
        self.rename_button.set_sensitive(True)
        self.menu_rename.set_sensitive(True)
        self.file_selected_model.foreach(self.enable_rename_and_clean)


    def on_clean_button_clicked(self, widget):
        """ Clean the previewed filenames """
        self.count = 0

        # Clean selected rows
        model, paths = self.selected_files.get_selection().get_selected_rows()
        self.file_selected_model.foreach(self.preview_clear, paths)

        self.file_selected_model.foreach(self.enable_rename_and_clean)

        self.selected_files.columns_autosize()

        if self.notebook.get_current_page() == 3:
            # Manual rename
            try:
                self.selected_files.get_selection().set_mode(gtk.SELECTION_SINGLE)
                model, iter = self.selected_files.get_selection().get_selected()
                name = model.get_value(iter,0)
                newname = model.get_value(iter,2)
                if newname != None:
                    self.manual.set_text(newname)
                else:
                    self.manual.set_text(name)
            except:
                pass


    def on_main_hpaned_notify(self, pane, gparamspec):
        if gparamspec.name == 'position':
            self.pane_position = pane.get_property('position')

    def on_options_button_clicked(self, widget):
        self.options_panel_state(not self.options_shown)

    def options_panel_state(self, state):

        if state:
            self.options_vbox.show()
            self.options_label.show()
            icon = self.options_button.get_child()
            icon.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        else:
            self.options_vbox.hide()
            self.options_label.hide()
            icon = self.options_button.get_child()
            icon.set_from_stock(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_MENU)

        self.options_shown = state
        self.menu_show_options.set_active(state)


    def on_file_pattern_changed(self, widget):
    	""" Reload the current dir 'cause we need it """
        self.dir_reload_current()


    def on_original_pattern_changed(self, widget):
    	""" Reload current dir and disable Rename button """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_renamed_pattern_changed(self, widget):
    	""" Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_spaces_toggled(self, widget):
    	""" Enable/Disable spaces combo """
    	self.subs_spaces_combo.set_sensitive(widget.get_active())
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_capitalization_toggled(self, widget):
    	""" Enable/Disable caps combo """
    	self.subs_capitalization_combo.set_sensitive(widget.get_active())
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_replace_toggled(self, widget):
        """ Enable/Disable replace with text entries """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        self.subs_replace_new.set_sensitive(widget.get_active())
        self.subs_replace_orig.set_sensitive(widget.get_active())
        self.subs_replace_label.set_sensitive(widget.get_active())
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_spaces_combo_changed(self, widget):
    	""" Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_capitalization_combo_changed(self, widget):
    	""" Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_replace_orig_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_replace_new_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_accents_toggled(self, widget):
        """ Enable/Disable accents """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)

    def on_subs_duplicated_toggled(self, widget):
        """ Fixes duplicated symbols """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_radio_toggled(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        self.insert_entry.set_sensitive(True)
        self.insert_pos.set_sensitive(True)
        self.insert_end.set_sensitive(True)
        self.delete_from.set_sensitive(False)
        self.delete_to.set_sensitive(False)
        self.delete_end.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_entry_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_pos_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_end_toggled(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        self.insert_pos.set_sensitive(not self.insert_end.get_active())
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_delete_radio_toggled(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        self.delete_from.set_sensitive(True)
        self.delete_to.set_sensitive(True)
        self.delete_end.set_sensitive(True)
        self.insert_entry.set_sensitive(False)
        self.insert_pos.set_sensitive(False)
        self.insert_end.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_delete_from_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.delete_from.get_value() > self.delete_to.get_value():
            self.delete_from.set_value(self.delete_to.get_value())
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_delete_to_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.delete_to.get_value() < self.delete_from.get_value():
            self.delete_to.set_value(self.delete_from.get_value())
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_delete_end_toggled(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_manual_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)

    def on_images_original_pattern_changed(self, widget):
        """ Reload current dir and disable Rename button """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_images_renamed_pattern_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_music_original_pattern_changed(self, widget):
        """ Reload current dir and disable Rename button """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_music_renamed_pattern_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.rename_button.set_sensitive(False)
        self.menu_rename.set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def populate_pattern_combos(self):
        """ Populate pattern combo boxes """

        # Clear 'em all first
        self.patterns = {}
        self.original_pattern_combo.get_model().clear()
        self.renamed_pattern_combo.get_model().clear()
        self.images_original_pattern_combo.get_model().clear()
        self.images_renamed_pattern_combo.get_model().clear()
        self.music_original_pattern_combo.get_model().clear()
        self.music_renamed_pattern_combo.get_model().clear()

        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        main_ori = pe.get_patterns('main_ori')
        main_dest = pe.get_patterns('main_dest')
        images_ori = pe.get_patterns('images_ori')
        images_dest = pe.get_patterns('images_dest')
        music_ori = pe.get_patterns('music_ori')
        music_dest = pe.get_patterns('music_dest')

        def set_combo_element(combo, newtext):
            pos = 0
            try:
                model = combo.get_model()
                iter = model.get_iter_first()
                elem = model.get_value(iter, 0)

                while elem != newtext:
                    iter = model.iter_next(iter)
                    elem = model.get_value(iter, 0)
                    pos += 1
            except:
                pos = -1

            text = combo.get_active_text()
            if pos >= 0:
                combo.set_active(pos)
            elif text == '':
                combo.set_active(0)
            else:
                combo.child.set_text(text)


        # Main original
        for p in main_ori:
            self.original_pattern_combo.append_text(p)
        set_combo_element(self.original_pattern_combo, self.patterns_default["main_ori"])
        self.patterns["main_ori"] = main_ori

        # Main renamed
        for p in main_dest:
            self.renamed_pattern_combo.append_text(p)
        set_combo_element(self.renamed_pattern_combo, self.patterns_default["main_dest"])
        self.patterns["main_dest"] = main_dest

        # Images original
        for p in images_ori:
            self.images_original_pattern_combo.append_text(p)
        set_combo_element(self.images_original_pattern_combo, self.patterns_default["images_ori"])
        self.patterns["images_ori"] = images_ori

        # Images renamed
        for p in images_dest:
            self.images_renamed_pattern_combo.append_text(p)
        set_combo_element(self.images_renamed_pattern_combo, self.patterns_default["images_dest"])
        self.patterns["images_dest"] = images_dest

        # Music original
        for p in music_ori:
            self.music_original_pattern_combo.append_text(p)
        set_combo_element(self.music_original_pattern_combo, self.patterns_default["music_ori"])
        self.patterns["music_ori"] = music_ori

        # Music renamed
        for p in music_dest:
            self.music_renamed_pattern_combo.append_text(p)
        set_combo_element(self.music_renamed_pattern_combo, self.patterns_default["music_dest"])
        self.patterns["music_dest"] = music_dest


    def on_pattern_ori_save_clicked(self, widget):

        # Get the pattern value
        text = self.original_pattern.get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('main_ori', text)

        # Add it to the variable
        patterns = self.patterns["main_ori"]
        patterns.append(text)
        self.patterns["main_ori"] = patterns

        # And show it on combobox
        self.original_pattern_combo.append_text(text)


    def on_pattern_ori_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('main_ori')


    def on_pattern_dest_save_clicked(self, widget):

        # Get the pattern value
        text = self.renamed_pattern.get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('main_dest', text)

        # Add it to the variable
        patterns = self.patterns["main_dest"]
        patterns.append(text)
        self.patterns["main_dest"] = patterns

        # And show it on combobox
        self.renamed_pattern_combo.append_text(text)


    def on_pattern_dest_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('main_dest')


    def on_images_ori_save_clicked(self, widget):

        # Get the pattern value
        text = self.images_original_pattern.get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('images_ori', text)

        # Add it to the variable
        patterns = self.patterns["images_ori"]
        patterns.append(text)
        self.patterns["images_ori"] = patterns

        # And show it on combobox
        self.images_original_pattern_combo.append_text(text)


    def on_images_ori_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('images_ori')


    def on_images_dest_save_clicked(self, widget):

        # Get the pattern value
        text = self.images_renamed_pattern.get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('images_dest', text)

        # Add it to the variable
        patterns = self.patterns["images_dest"]
        patterns.append(text)
        self.patterns["images_dest"] = patterns

        # And show it on combobox
        self.images_renamed_pattern_combo.append_text(text)


    def on_images_dest_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('images_dest')


    def on_music_ori_save_clicked(self, widget):

        # Get the pattern value
        text = self.music_original_pattern.get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('music_ori', text)

        # Add it to the variable
        patterns = self.patterns["music_ori"]
        patterns.append(text)
        self.patterns["music_ori"] = patterns

        # And show it on combobox
        self.music_original_pattern_combo.append_text(text)


    def on_music_ori_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('music_ori')


    def on_music_dest_save_clicked(self, widget):

        # Get the pattern value
        text = self.music_renamed_pattern.get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('music_dest', text)

        # Add it to the variable
        patterns = self.patterns["music_dest"]
        patterns.append(text)
        self.patterns["music_dest"] = patterns

        # And show it on combobox
        self.music_renamed_pattern_combo.append_text(text)


    def on_music_dest_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('music_dest')


    def on_original_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["main_ori"] = text


    def on_renamed_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["main_dest"] = text


    def on_images_original_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["images_ori"] = text


    def on_images_renamed_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["images_dest"] = text


    def on_music_original_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["music_ori"] = text


    def on_music_renamed_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["music_dest"] = text


    def on_notebook_switch_page(self, notebook, page, page_num):
        """ Tab changed """
        if page_num != 3:
            self.selected_files.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        else:
            # Manual rename
            try:
                self.selected_files.get_selection().set_mode(gtk.SELECTION_SINGLE)
                model, iter = self.selected_files.get_selection().get_selected()
                name = model.get_value(iter,0)
                newname = model.get_value(iter,2)
                if newname != None:
                    self.manual.set_text(newname)
                else:
                    self.manual.set_text(name)
            except: pass


    def on_copy_activate(self, widget):
        """ Copy to clipboard """
        w = self.main_window.get_focus()
        if isinstance(w, gtk.Entry):
            w.emit('copy-clipboard')


    def on_paste_activate(self, widget):
        """ Paste from clipboard """
        w = self.main_window.get_focus()
        if isinstance(w, gtk.Entry):
            w.emit('paste-clipboard')


    def on_cut_activate(self, widget):
        """ Cut to clipboard """
        w = self.main_window.get_focus()
        if isinstance(w, gtk.Entry):
            w.emit('cut-clipboard')


    def on_clear_activate(self, widget):
        """ Clear text widget """
        w = self.main_window.get_focus()
        if isinstance(w, gtk.Entry):
            w.set_text('')


    def on_select_all_activate(self, widget):
        """ Select every row on selected-files treeview """
        if self.notebook.get_current_page() == 3:
            self.selected_files.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.selected_files.get_selection().select_all()


    def on_select_nothing_activate(self, widget):
        """ Select nothing on selected-files treeview """
        if self.notebook.get_current_page() == 3:
            self.selected_files.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.selected_files.get_selection().unselect_all()


    def on_preferences_activate(self, widget):
        """ Preferences menu item clicked """
        self.prefs.create_preferences_dialog()


    def on_manual_key_press_event(self, widget, event):
        """ Key pressed on manual rename entry """

        if self.notebook.get_current_page() == 3:
            self.selected_files.get_selection().set_mode(gtk.SELECTION_SINGLE)
            if event.keyval == gtk.keysyms.Page_Up:
                try:
                    self.preview_selected_row()
                    self.file_selected_model.foreach(self.enable_rename_and_clean)
                    model, iter = self.selected_files.get_selection().get_selected()
                    path = model.get_path(iter)
                    path = path[0]-1
                    if path < 0: return
                    iter = model.get_iter(path)
                    name = model.get_value(iter,0)
                    self.selected_files.get_selection().select_iter(iter)
                    self.manual.handler_block(self.manual_signal)
                    self.selected_files.scroll_to_cell(path)
                    self.on_selected_files_cursor_changed(self.selected_files)
                    self.manual.handler_unblock(self.manual_signal)
                except:
                    pass
            elif event.keyval == gtk.keysyms.Page_Down:
                try:
                    self.preview_selected_row()
                    self.file_selected_model.foreach(self.enable_rename_and_clean)
                    model, iter = self.selected_files.get_selection().get_selected()
                    iter = model.iter_next(iter)
                    if iter == None: return
                    path = model.get_path(iter)
                    name = model.get_value(iter,0)
                    self.selected_files.get_selection().select_iter(iter)
                    self.manual.handler_block(self.manual_signal)
                    self.selected_files.scroll_to_cell(path)
                    self.on_selected_files_cursor_changed(self.selected_files)
                    self.manual.handler_unblock(self.manual_signal)
                except:
                    pass
            elif event.keyval == gtk.keysyms.Return:
                try:
                    self.preview_selected_row()
                    self.file_selected_model.foreach(self.enable_rename_and_clean)
                    model, iter = self.selected_files.get_selection().get_selected()
                    iter = model.iter_next(iter)
                    if iter == None: return
                    path = model.get_path(iter)
                    name = model.get_value(iter,0)
                    self.selected_files.get_selection().select_iter(iter)
                    self.manual.handler_block(self.manual_signal)
                    self.selected_files.scroll_to_cell(path)
                    self.on_selected_files_cursor_changed(self.selected_files)
                    self.manual.handler_unblock(self.manual_signal)
                except:
                    pass
            self.selected_files.get_selection().set_mode(gtk.SELECTION_MULTIPLE)


    def on_menu_load_names_from_file_activate(self, widget):
        """ Get file names from a file """

        filename = ""
        f = gtk.FileChooserDialog(_('Select file'),
                                  self.main_window,
                                  gtk.FILE_CHOOSER_ACTION_OPEN,
                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                                   )
        response = f.run()
        if response == gtk.RESPONSE_ACCEPT:
            filename = f.get_filename()
        elif response == gtk.RESPONSE_REJECT:
            pass
        f.destroy()

        if filename != "":
            self.populate_from_file(filename)


    def on_main_quit(self, *args):
    	""" Bye bye! But first, save preferences """
        self.populate_stop()
        if HAS_GCONF: self.prefs.preferences_save()
        gtk.main_quit()


#---------------------------------------------------------------------------------------
# Directory functions

    def dir_reload_current(self):
        """ An easy way to call dir_selected """
        self.dir_selected(None, self.active_dir)


    def dir_selected(self, obj, dir):
    	""" The user has clicked on a directory on the left pane, so we need to load
    	the files inside that dir on the right pane. """

        self.active_dir = dir
        self.populate_stop()

        self.stop_button.show()
        self.clear_button.set_sensitive(False)
        self.rename_button.set_sensitive(False)
        self.file_selected_model.clear()

        while gtk.events_pending():
            gtk.main_iteration()

        self.file_selected_model.clear()

        self.populate_selected_files(dir)
        self.selected_files.columns_autosize()
        self.statusbar.push(self.statusbar_context, _("Reading contents of dir %s") % dir)


    def populate_stop(self):
        """ Stop populating the TreeView """

        renamerfilefuncs.set_stop(True)

        if self.listing_thread != None:
            while self.listing_thread.isAlive():
                self.listing_thread.join()

        self.stop_button.hide()
        for i in self.populate_id:
            removed = gobject.source_remove(i)
            self.populate_id.remove(i)

        self.selected_files.set_model(self.file_selected_model)
        self.progressbar.set_fraction(0)
        self.statusbar.push(self.statusbar_context, _("Directory: %s - Files: %s") % (self.active_dir, self.count))


    def populate_get_listing(self, dir, pattern, recursive):
        """ Get the file listing using the utilities on renamerfilefuncs """

        # Add files from the current directory (and subdirs if needed)
        if recursive:
            self.listing = renamerfilefuncs.get_file_listing_recursive(dir, self.filedir, pattern)
        else:
            self.listing = renamerfilefuncs.get_file_listing(dir, self.filedir, pattern)

        gobject.idle_add(self.populate_get_listing_end)


    def populate_get_listing_end(self):
        """ The listing thread stuff is over, so now add things to the view """

        if renamerfilefuncs.get_stop():
            self.populate_stop()
        else:
            populate = self.populate_add_to_view(self.listing)
            self.populate_id.append(gobject.idle_add(populate.next))


    def populate_selected_files(self, dir):
    	""" Get the file listing using the utilities on renamerfilefuncs.
    	Then add it to the model while updating the gui """

        pattern = self.file_pattern.get_text()
        recursive = self.add_recursive.get_active()

        renamerfilefuncs.set_stop(False)

        self.listing_thread = threading.Thread(target=lambda:self.populate_get_listing(dir, pattern, recursive))
        self.listing_thread.start()

        return


    def populate_add_to_view(self, listing):
        """ Add files to the treeview """

        # Don't display things while we're populating
        self.selected_files.set_model(None)

        # Add items to treeview
        for elem in listing:

            row = [elem[0], elem[1], None, None, self.get_icon(elem[1])]
            self.file_selected_model.append(row)

            self.progressbar.pulse()
            self.statusbar.push(self.statusbar_context, _("Adding file %s") % elem[1])
            self.count += 1
            yield True

        # Show on treeview, reset progressbar and statusbar
        self.selected_files.set_model(self.file_selected_model)
        self.progressbar.set_fraction(0)
        self.statusbar.push(self.statusbar_context, _("Directory: %s - Files: %s") % (self.active_dir, self.count))
        self.stop_button.hide()
        self.count = 0
        yield False


    def populate_from_file(self, filename):
        """ Populate file preview loading the names from a file """

        f = open(filename, 'r')
        iter = self.file_selected_model.get_iter_root()
        for line in f:
            line = line.rstrip()
            if len(line) > 255 or not isinstance(line, str) or line == "":
                line = None
                path = None

            if line != "" and line != None:
                oripath = self.file_selected_model.get_value(iter, 1)
                path = ospath.join(ospath.dirname(oripath), line)

            self.selected_files.set_model(None)
            self.file_selected_model.set_value(iter, 2, line)
            self.file_selected_model.set_value(iter, 3, path)

            self.count += 1
            iter = self.file_selected_model.iter_next(iter)
            if iter == None: break

        self.selected_files.set_model(self.file_selected_model)

        self.selected_files.columns_autosize()
        self.clear_button.set_sensitive(True)
        self.menu_clear_preview.set_sensitive(True)
        self.rename_button.set_sensitive(True)
        self.menu_rename.set_sensitive(True)

        f.close()


    def get_default_icons(self):

        # Load default icon theme
        icon_theme = gtk.icon_theme_get_default()

        # Load directory icon
        try:
            self.icon_dir = icon_theme.load_icon("gnome-fs-directory", gtk.ICON_SIZE_MENU, 0)
        except gobject.GError, exc:
            try:
                self.icon_dir =  icon_theme.load_icon("gtk-directory", gtk.ICON_SIZE_MENU, 0)
            except:
                self.icon_dir = None

        # Load text icon
        try:
            self.icon_text = icon_theme.load_icon("text-x-generic", gtk.ICON_SIZE_MENU, 0)
        except gobject.GError, exc:
            self.icon_text = None

        # Load image icon
        try:
            self.icon_image = icon_theme.load_icon("image-x-generic", gtk.ICON_SIZE_MENU, 0)
        except gobject.GError, exc:
            self.icon_image = None

        # Load audio icon
        try:
            self.icon_audio = icon_theme.load_icon("audio-x-generic", gtk.ICON_SIZE_MENU, 0)
        except gobject.GError, exc:
            self.icon_audio = None

        # Load video icon
        try:
            self.icon_video = icon_theme.load_icon("video-x-generic", gtk.ICON_SIZE_MENU, 0)
        except gobject.GError, exc:
            self.icon_video = None

        # Load package icon
        try:
            self.icon_package = icon_theme.load_icon("package-x-generic", gtk.ICON_SIZE_MENU, 0)
        except gobject.GError, exc:
            self.icon_package = None


        return icon_theme


    def icon_theme_changed(self, icon_theme):
        self.get_default_icons()


    def get_icon(self, path):

        if ospath.isdir(path):
            return self.icon_dir
        else:

            audio = ["mp3", "ogg", "wav", "aiff", "mp4", "aac"]
            image = ["jpg", "gif", "png", "tiff", "tif", "jpeg", "xcf", "psd", "svg"]
            video = ["avi", "ogm", "mpg", "mpeg", "mov"]
            package = ["rar", "zip", "gz", "tar", "bz2", "tgz", "deb", "rpm"]

            file = path.split('/')[-1]
            ext = (file.split('.')[-1]).lower()

            if ext in audio:
                return self.icon_audio
            elif ext in image:
                return self.icon_image
            elif ext in video:
                return self.icon_video
            elif ext in package:
                return self.icon_package
            else:
                return self.icon_text


#---------------------------------------------------------------------------------------
# Dialog methods

    def display_error_dialog(self, text):
    	""" Yeps, it shows a error dialog """

        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_NONE, text)
        dialog.add_button(_("Ignore errors"), 1)
        dialog.add_button("gtk-ok", 0)
        self.ignore_errors = dialog.run()
        dialog.destroy()


    def about_info(self,event,data=None):
        """ Display the About dialog """

        about = gtk.AboutDialog()
        about.set_name(pyrenamerglob.name_long)
        about.set_version(pyrenamerglob.version)
        about.set_authors(pyrenamerglob.authors)
        #about.set_artists(pyrenamerglob.artists)
        about.set_translator_credits(_('translator-credits'))
        about.set_logo(gtk.gdk.pixbuf_new_from_file(pyrenamerglob.icon))
        about.set_license(pyrenamerglob.license)
        about.set_wrap_license(True)
        about.set_comments(_(pyrenamerglob.description))
        about.set_copyright(pyrenamerglob.copyright)

        def openHomePage(widget,url,url2):
            import webbrowser
            webbrowser.open_new(url)

        gtk.about_dialog_set_url_hook(openHomePage,pyrenamerglob.website)
        about.set_website(pyrenamerglob.website)
        about.set_icon_from_file(pyrenamerglob.icon)
        about.run()
        about.destroy()
