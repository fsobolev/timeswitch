# timer.py
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

from gi.repository import GObject, GLib, Gio
from .actions import *


class Timer:
    def __init__(self, h, m, s, action, timer_label, desc_label, pause_button, finish_fn):
        self.h, self.m, self.s = h, m, s
        self.duration = self.h * 3600 + self.m * 60 + self.s
        self.action = action[0]
        self.desc_label = desc_label
        self.status_label = ""
        self.pause_button = pause_button
        self.pause = False
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

        # Notification
        self.sound_repeat = False
        self.player_cancellable = Gio.Cancellable.new()

        if self.action == 'poweroff':
            self.desc_label.set_text(_('Your device will be powered off in'))
            self.status_label = _('Power off in {}')
        elif self.action == 'reboot':
            self.desc_label.set_text(_('Your device will be rebooted in'))
            self.status_label = _('Reboot in {}')
        elif self.action == 'suspend':
            self.desc_label.set_text(_('Your device will be suspended in'))
            self.status_label = _('Suspend in {}')
        elif self.action == 'notification':
            self.desc_label.set_text(_('You will receive a notification in'))
            self.status_label = _('Notification in {}')
            self.notification_text = action[1]
            self.play_sound = action[2]
            if action[2] == 2:
                self.sound_repeat = True
        elif self.action == 'command':
            self.desc_label.set_markup(_(
                'The command <b>{}</b> will be executed in').format(action[1]))
            self.status_label = _('Command "{}" in {}').format(action[1], '{}')
            self.cmd = action[2]
        self.timer_label = timer_label
        self.finish_fn = finish_fn
        self.stop = False
        GObject.timeout_add_seconds(1, self.run)

    def run(self):
        if self.pause: return True
        if self.stop:
            self.clear_status()
            return False
        self.s = self.duration
        self.h = self.s // 3600
        self.s %= 3600
        self.m = self.s // 60
        self.s %= 60
        time_label = str(self.h) + \
            ':{0:0>2}'.format(self.m) + \
            ':{0:0>2}'.format(self.s)
        self.timer_label.set_text(time_label)
        self.bus.call('org.freedesktop.portal.Desktop', # Bus name
            '/org/freedesktop/portal/desktop', # Object path
            'org.freedesktop.portal.Background', # Interface name
            'SetStatus', # Method name
            GLib.Variant.new_tuple(GLib.Variant('a{sv}', \
                {'message': GLib.Variant('s', \
                self.status_label.format(time_label))} )), # Parameters
            None, # Reply type
            Gio.DBusCallFlags.NONE, # Flags
            -1, # Timeout
            None, # Cancellable
            None, # Callback
            None) # User data
        if self.duration > 0:
            self.duration -= 1
            return True
        else:
            self.pause_button.set_sensitive(False)
            self.act()
            if self.action == 'notification':
                self.desc_label.set_text( \
                    _('The notification has been sent.'))
            if not self.sound_repeat:
                self.finish_fn()
            self.clear_status()
            return False

    def act(self):
        if self.action == 'poweroff':
            action_poweroff()
            return;
        elif self.action == 'reboot':
            action_reboot()
            return;
        elif self.action == 'suspend':
            action_suspend()
            return;
        elif self.action == 'notification':
            action_notify(self.notification_text, self.play_sound, \
                self.sound_repeat, self.player_cancellable)
            return;
        elif self.action == 'command':
            action_command(self.cmd)

    def stop_timer(self):
        self.stop = True
        self.player_cancellable.cancel()

    def clear_status(self):
        self.bus.call('org.freedesktop.portal.Desktop', # Bus name
            '/org/freedesktop/portal/desktop', # Object path
            'org.freedesktop.portal.Background', # Interface name
            'SetStatus', # Method name
            GLib.Variant.new_tuple(GLib.Variant('a{sv}', \
                {'message': GLib.Variant('s', \
                _('Timer has finished!'))} )), # Parameters
            None, # Reply type
            Gio.DBusCallFlags.NONE, # Flags
            -1, # Timeout
            None, # Cancellable
            None, # Callback
            None) # User data'
