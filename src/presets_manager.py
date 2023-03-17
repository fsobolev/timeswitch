# presets_manager.py
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
# SPDX-License-Identifier: MIT)

from gi.repository import Gio

class PresetsManager:
    def __init__(self, window, presets):
        self.window = window
        self.generate_presets(presets)

    def generate_presets(self, presets):
        self.window.presets_list_section.remove_all()
        i = 0
        for p in presets:
            self.window.remove_action(f'preset-{i}')
            action = Gio.SimpleAction.new(f'preset-{i}', None)
            action.connect('activate', lambda *args: self.activate_preset(p))
            self.window.add_action(action)
            self.window.presets_list_section.append(p['name'], f'win.preset-{i}')
            i += 1

    def activate_preset(self, settings):
        self.window.timer_mode_dropdown.set_selected(settings['mode'])
        self.window.hour_spin.set_value(settings['timer-value'][0])
        self.window.min_spin.set_value(settings['timer-value'][1])
        self.window.sec_spin.set_value(settings['timer-value'][2])
        [self.window.action_poweroff, self.window.action_reboot, \
            self.window.action_suspend, self.window.action_notify, \
            self.window.action_command][settings['action'][0]].activate()
        if settings['action'][0] == 3:
            self.window.play_sound_switch.set_active( \
                bool(settings['action'][1]))
            self.window.play_until_stopped_switch.set_sensitive( \
                bool(settings['action'][1]))
            if settings['action'][1] > 1:
                self.window.play_until_stopped_switch.set_active(True)
        elif settings['action'][0] == 4:
            if len(self.window.commands_widgets['rows']) > \
                    settings['action'][1]:
                self.window.commands_widgets['rows'][ \
                settings['action'][1]].activate()
