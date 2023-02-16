pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'timeswitch')
gnome = import('gnome')

gnome.compile_resources('timeswitch',
  'timeswitch.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'timeswitch.in',
  output: 'timeswitch',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

timeswitch_sources = [
  '__init__.py',
  'main.py',
  'main_window.py',
  'main_window_shortcuts.py',
  'timer.py',
  'actions.py',
  'player.py',
  'config.py'
]

install_data(timeswitch_sources, install_dir: moduledir)

configure_file(
  input: 'translator_credits.py.in',
  output: 'translator_credits.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)
