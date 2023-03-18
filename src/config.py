# config.py
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

import os
import json

class TimeSwitchConfig:
    def __init__(self):
        self.last_timer_value = [0, 0, 0]
        self.last_action = [0, 0]
        self.notification_text = ""
        self.commands = []
        self.mode = 0
        self.window_size = (330, 712)
        self.presets = {}
        self.show_cmd_warning = True

        if os.getenv('XDG_CONFIG_HOME'):
            config_dir = os.getenv('XDG_CONFIG_HOME') + '/timeswitch'
        else:
            config_dir = os.getenv('HOME') + '/.config/timeswitch'
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)
        self.config_file_path = config_dir + '/config.json'

    def load(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    data = json.load(f)
                    if 'last-timer-value' in data.keys():
                        self.last_timer_value = data['last-timer-value']
                    if 'last-action' in data.keys():
                        self.last_action = data['last-action']
                    if 'notification-text' in data.keys():
                        self.notification_text = data['notification-text']
                    if 'commands' in data.keys():
                        self.commands = data['commands']
                        if len(self.commands) > 0:
                            self.show_cmd_warning = False
                    if 'mode' in data.keys():
                        self.mode = data['mode']
                    if 'window-size' in data.keys():
                        self.window_size = data['window-size']
                    if 'presets' in data.keys():
                        self.presets = data['presets']
            except Exception as e:
                print("Can't read config file:")
                print(e)

    def save(self):
        try:
            with open(self.config_file_path, 'w') as f:
                data = {'last-timer-value': self.last_timer_value, \
                    'last-action': self.last_action, \
                    'notification-text': self.notification_text, \
                    'commands': self.commands, \
                    'mode': self.mode, \
                    'window-size': self.window_size, \
                    'presets': self.presets}
                json.dump(data, f)
        except Exception as e:
            print("Can't save config file:")
            print(e)
