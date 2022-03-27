folders = {
    '.': [
        '__init__.py',
        'application.py',
        'application_window.py',
        'file_browser.py',
        'insert_delete_page.py',
        'manual_page.py',
        'options_pane.py',
        'paths.py',
        'patterns_page.py',
        'preferences.py',
        'renamer.py',
        'renaming_notebook.py',
        'renaming_rules.py',
        'substitutions_page.py',
        'tree_file_browser.py',
        'window_state.py'
    ]
}

foreach folder_name, sources : folders
  pkg_dir = meson.project_name() / folder_name
  python3.install_sources(sources, pure: false, subdir: pkg_dir)
endforeach

# Install the executable file
app_config = configuration_data({
    'version': meson.project_version(),
    'application_id': application_id,
    'resource_base_path': resource_base_path,
    'locale_dir': locale_dir,
    'pkgdata_dir': pkgdata_dir
})
configure_file(
    input: 'conf.py.in',
    output: 'conf.py',
    configuration: app_config,
    install_dir: python3.get_install_dir(subdir: meson.project_name())
)

subdir('resources')
