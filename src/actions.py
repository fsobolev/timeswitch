# actions.py
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
import subprocess
import gi
gi.require_version('GSound', '1.0')
from gi.repository import Gio, GLib
from .player import Player


def action_poweroff():
    if os.getenv('XDG_CURRENT_DESKTOP') == 'GNOME':
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.call('org.gnome.SessionManager', # Bus name
            '/org/gnome/SessionManager', # Object path
            'org.gnome.SessionManager', # Interface name
            'Shutdown', # Method name
            None, # Parameters
            None, # Reply type
            Gio.DBusCallFlags.NONE, # Flags
            -1, # Timeout
            None, # Cancellable
            None, # Callback
            None) # User data
    else:
        # I didn't manage to get it work using Gio :(
        # Fortunately, this seems to work fine
        os.system('dbus-send --system --print-reply \
            --dest=org.freedesktop.login1 /org/freedesktop/login1 \
            "org.freedesktop.login1.Manager.PowerOff" boolean:true')

def action_reboot():
    if os.getenv('XDG_CURRENT_DESKTOP') == 'GNOME':
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.call('org.gnome.SessionManager', # Bus name
            '/org/gnome/SessionManager', # Object path
            'org.gnome.SessionManager', # Interface name
            'Reboot', # Method name
            None, # Parameters
            None, # Reply type
            Gio.DBusCallFlags.NONE, # Flags
            -1, # Timeout
            None, # Cancellable
            None, # Callback
            None) # User data
    else:
        os.system('dbus-send --system --print-reply \
            --dest=org.freedesktop.login1 /org/freedesktop/login1 \
            "org.freedesktop.login1.Manager.Reboot" boolean:true')

def action_suspend():
    os.system('dbus-send --system --print-reply \
        --dest=org.freedesktop.login1 /org/freedesktop/login1 \
        "org.freedesktop.login1.Manager.Suspend" boolean:true')

def action_notify(text, play_sound, sound_repeat, cancellable):
    if text == '': text = _('Timer has finished!')
    notification = Gio.Notification.new('Time Switch')
    notification.set_body(text)
    notification.set_priority(Gio.NotificationPriority.URGENT)
    Gio.Application.get_default().send_notification(None, notification)
    if play_sound:
        player = Player(sound_repeat, cancellable)
        player.play()

def action_command(cmd):
    if os.getenv('FLATPAK_ID'):
        cmd = 'flatpak-spawn --host ' + cmd
    subprocess.Popen(cmd, shell=True)
