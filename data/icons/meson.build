application_id = 'io.github.fsobolev.TimeSwitch'

scalable_apps_dir = join_paths('hicolor', 'scalable', 'apps')
install_data(
  join_paths(scalable_apps_dir, ('@0@.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', scalable_apps_dir)
)

symbolic_apps_dir = join_paths('hicolor', 'symbolic', 'apps')
install_data(
  join_paths(symbolic_apps_dir, ('@0@-symbolic.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', symbolic_apps_dir)
)

symbolic_status_dir = join_paths('hicolor', 'symbolic', 'status')
install_data(
  files(join_paths(symbolic_status_dir, 'clock-alt-symbolic.svg'), join_paths(symbolic_status_dir, 'hourglass-symbolic.svg')),
  install_dir: join_paths(get_option('datadir'), 'icons', symbolic_apps_dir)
)