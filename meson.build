project('pyrenamer', version: '1.0.0', meson_version: '>=0.60.0', default_options: ['prefix=/usr'])

python = import('python')
i18n = import('i18n')
gnome = import('gnome')

python3 = python.find_installation('python3', modules: ['taglib'])
if not python3.found()
    error('Python 3 is required to build and run pyRenamer.')
endif

dependency('python3', version: '>= 3.7')
dependency('pygobject-3.0', version: '>= 3.36')
dependency('gtk+-3.0', version: '>= 3.24')
dependency('glib-2.0', version: '>= 2.64')
dependency('gexiv2', version: '>= 0.12')

if get_option('profile') == 'devel'
    name_suffix = ' (Development Snapshot)'
    profile = 'Devel'
else
    name_suffix = ''
    profile = ''
endif

application_id_no_profile = 'digital.jose.pyRenamer'
application_id = f'@application_id_no_profile@@profile@'
resource_base_path = '/digital/jose/pyRenamer'

prefix = get_option('prefix')

bin_dir = prefix / get_option('bindir')
man_dir = prefix / get_option('mandir')
locale_dir = prefix / get_option('localedir')
po_dir = meson.current_source_dir() / 'po'

data_dir = prefix / get_option('datadir')
pkgdata_dir = data_dir / meson.project_name()
schema_dir = data_dir / 'glib-2.0' / 'schemas'
desktop_dir = data_dir / 'applications'
appdata_dir = data_dir / 'metainfo'
icon_dir = data_dir / 'icons'

# message('prefix:', prefix)
# message('bin_dir:', bin_dir)
# message('man_dir:', man_dir)
# message('locale_dir:', locale_dir)
# message('po_dir:', po_dir)
# message('data_dir:', data_dir)
# message('pkgdata_dir:', pkgdata_dir)
# message('schema_dir:', schema_dir)
# message('desktop_dir:', desktop_dir)
# message('appdata_dir:', appdata_dir)
# message('icon_dir:', icon_dir)

subdir('pyrenamer')
subdir('data')
subdir('po')

install_data('bin/pyrenamer', install_dir: bin_dir)

meson.add_install_script('meson_post_install.py')
