# Install Gsettings schema
install_data(
    f'@application_id_no_profile@.gschema.xml',
    install_dir: schema_dir
)

# Check GSettings schema
compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
    test(
        'Validate schema file',
        compile_schemas,
        args: ['--strict', '--dry-run', meson.current_source_dir()]
    )
endif

# Merging the translations with the desktop file
desktop_conf = configuration_data({
    'icon': application_id_no_profile
})
desktop_file = i18n.merge_file(
    type: 'desktop',
    input: configure_file(
        input: f'@application_id_no_profile@.desktop.in.in',
        output: f'@application_id@.desktop.in',
        configuration: desktop_conf),
    output: f'@application_id@.desktop',
    po_dir: po_dir,
    install: true,
    install_dir: desktop_dir
)

# Validating the desktop file
desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
    test (
        'Validate desktop file',
        desktop_file_validate,
        args: desktop_file.full_path()
    )
endif

# Merging the translations with the appdata file
appdata_conf = configuration_data({
    'appid': application_id
})
appdata_file = i18n.merge_file(
    input: configure_file(
        input: f'@application_id_no_profile@.appdata.xml.in.in',
        output: f'@application_id@.appdata.xml.in',
        configuration: appdata_conf
    ),
    output: f'@application_id@.appdata.xml',
    po_dir: po_dir,
    install: true,
    install_dir: appdata_dir
)

# Validating the appdata file
appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
    test (
        'Validate appdata file',
        appstream_util,
        args: ['validate-relax', '--nonet', appdata_file.full_path()]
    )
endif

# Installing the default icon
install_data(
    'icons' /  'hicolor' / 'scalable' / 'apps' / f'@application_id_no_profile@.svg',
    install_dir: icon_dir / 'hicolor' / 'scalable' /'apps'
)
