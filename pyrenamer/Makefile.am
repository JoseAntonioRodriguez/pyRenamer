###################################
### Main data
###################################
all-local: pyrenamer_globals.py

bin_SCRIPTS = pyrenamer

pyrenamerdir = $(pythondir)/pyrenamer

pyrenamer_PYTHON =				\
	__init__.py					\
	pyrenamer.py				\
	pyrenamer_filefuncs.py		\
	pyrenamer_menu_cb.py		\
	pyrenamer_metadata.py		\
	pyrenamer_pattern_editor.py	\
	pyrenamer_prefs.py			\
	pyrenamer_tooltips.py		\
	pyrenamer_undo.py			\
	treefilebrowser.py			\
	TreeViewTooltips.py			\
	EXIF.py
	
nodist_pyrenamer_PYTHON =	\
	pyrenamer_globals.py

EXTRA_DIST = 				\
	$(bin_SCRIPTS)			\
	$(pyrenamer_PYTHON)		\
	pyrenamer_globals.py.in

CLEANFILES = \
	pyrenamer_globals.py

###################################
### Configure pyrenamer_globals.py
###################################
pyrenamer_globals.py: pyrenamer_globals.py.in Makefile
	sed \
		-e s!\@LOCALEDIR\@!$(datadir)/locale! \
		-e s!\@RESOURCEDIR\@!$(datadir)/$(PACKAGE_NAME)! \
		-e s!\@PKGDATADIR\@!$(pkgdatadir)! \
		-e s!\@PACKAGE\@!$(PACKAGE_NAME)! \
		-e s!\@VERSION\@!$(PACKAGE_VERSION)! \
		< $< \
		> $@