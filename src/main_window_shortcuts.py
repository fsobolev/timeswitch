# window_shortcuts.py
#
# Copyright 2022 Fyodor Sobolev
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization.
#
# SPDX-License-Identifier: MIT

from gi.repository import Gio

def set_shortcuts(window):
    # Setup
    create_action(window, 'focus-hour', \
        lambda *args: \
            window.hour_spin.grab_focus() if not window.timer else None, \
        ['<alt>H'])
    create_action(window, 'focus-min', \
        lambda *args: \
            window.min_spin.grab_focus() if not window.timer else None, \
        ['<alt>M'])
    create_action(window, 'focus-sec', \
        lambda *args: \
            window.sec_spin.grab_focus() if not window.timer else None, \
        ['<alt>S'])
    create_action(window, 'reset', \
        lambda *args: \
            window.reset_timer(None) if not window.timer else None, \
        ['<alt>R'])
    create_action(window, 'change_mode', \
        lambda *args: \
            (window.timer_mode_dropdown.set_selected( \
            1 if window.timer_mode_dropdown.get_selected() == 0 else 0)) \
            if not window.timer else None, \
        ['<primary>M'])
    create_action(window, 'start', \
        lambda *args: window.start_timer(None) if not window.timer else None, \
        ['<primary>Return'])

    # Actions
    create_action(window, 'power-off', \
        lambda *args: select_action(window, window.action_poweroff), \
        ['<primary>O'])
    create_action(window, 'reboot', \
        lambda *args: select_action(window, window.action_reboot), \
        ['<primary>R'])
    create_action(window, 'suspend', \
        lambda *args: select_action(window, window.action_suspend), \
        ['<primary>S'])
    create_action(window, 'notification', \
        lambda *args: select_action(window, window.action_notify), \
        ['<primary>N'])
    for i in range(10):
        cb = lambda act, param: select_command(window, int(act.get_name()[-1]))
        create_action(window, 'select-command-' + str(i), cb, \
            ['<primary>' + str(i)])
    create_action(window, 'add-command', \
        lambda *args: add_command(window), ['<primary>a'])
    create_action(window, 'edit-command', \
        lambda *args: edit_command(window), ['<primary>e'])

    # Running
    create_action(window, 'toggle-pause', \
        lambda *args: window.toggle_pause(None) if window.timer else None, \
        ['<primary>p'])
    create_action(window, 'stop-timer', \
        lambda *args: window.stop_timer(None) if window.timer else None, \
        ['<primary><alt>s'])

    create_action(window, 'show-menu', lambda *args: \
        window.run_menu_button.popup() if window.timer \
        else window.main_menu_button.popup(), ['F10'])

def select_action(window, row):
    if not window.timer:
        row.activate()

def select_command(window, index):
    if not window.timer:
        try:
            if index == 0:
                index = 10
            window.commands_widgets['rows'][index-1].activate()
        except:
            pass

def add_command(window):
    if not window.timer and not window.show_cmd_warning:
            window.add_command(None)

def edit_command(window):
    if not window.timer:
        for row in window.commands_widgets['rows']:
            if row.get_activatable_widget().get_active():
                window.edit_command(None, row)
                break

def create_action(window, name, callback, shortcuts):
    """Add an application action.

    Args:
        name: the name of the action
        callback: the function to be called when the action is
          activated
        shortcuts: a list of accelerators
    """
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    window.add_action(action)
    window.get_application().set_accels_for_action(f"win.{name}", shortcuts)
