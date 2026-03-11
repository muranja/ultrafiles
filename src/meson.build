pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'ultrafiles'

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'ultrafiles.in',
  output: 'ultrafiles',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

ultrafiles_sources = [
  '__init__.py',
  'main.py',
  'application.py',
  'window.py',
]

install_data(ultrafiles_sources, install_dir: moduledir)

# Install submodules
install_subdir('views', install_dir: moduledir)
install_subdir('widgets', install_dir: moduledir)
install_subdir('viewers', install_dir: moduledir)
install_subdir('dialogs', install_dir: moduledir)
install_subdir('services', install_dir: moduledir)
install_subdir('utils', install_dir: moduledir)
