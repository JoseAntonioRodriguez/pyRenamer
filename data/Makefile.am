###################################
### Initialization
###################################
EXTRA_DIST =
DISTCLEANFILES =


###################################
### Desktop file
###################################
@INTLTOOL_DESKTOP_RULE@
desktop_in_files = pyrenamer.desktop.in.in
desktopdir = $(datadir)/applications
desktop_DATA = $(desktop_in_files:.desktop.in.in=.desktop)

pyrenamer.desktop.in: pyrenamer.desktop.in.in
	sed \
		-e s!\@RESOURCEDIR\@!$(datadir)/$(PACKAGE_NAME)! \
		-e s!\@BINDIR\@!$(bindir)! \
		< $< > $@

EXTRA_DIST += pyrenamer.desktop.in.in.in
DISTCLEANFILES += $(desktop_DATA) pyrenamer.desktop.in


###################################
### Glade
###################################
gladedir   = $(pkgdatadir)
glade_DATA = pyrenamer.glade
EXTRA_DIST += $(glade_DATA)


###################################
### Gconf schemas
###################################
@INTLTOOL_SCHEMAS_RULE@
schemadir = $(GCONF_SCHEMA_FILE_DIR)
schema_in_files = pyrenamer.schemas.in
schema_DATA = $(schema_in_files:.schemas.in=.schemas)
EXTRA_DIST += $(schema_in_files)
DISTCLEANFILES += $(schema_DATA)

install-data-local: install-schemas
uninstall-local: uninstall-schemas

install-schemas: $(schema_DATA)
	if test -z "$(DESTDIR)" ; then \
	for p in $^ ; do \
		GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) \
			$(GCONFTOOL) \
			--makefile-install-rule \
			$(top_builddir)/data/$$p; \
	done \
	fi

uninstall-schemas: $(schema_DATA)
	if test -z "$(DESTDIR)" ; then \
	for p in $^ ; do \
		GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) \
			$(GCONFTOOL) \
			--makefile-uninstall-rule \
			$(top_builddir)/data/$$p; \
	done \
	fi