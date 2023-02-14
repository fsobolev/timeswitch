# main.py
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

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import TimeSwitchWindow
from .translator_credits import get_translator_credits


class TimeSwitchApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version):
        super().__init__(application_id='io.github.fsobolev.TimeSwitch',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.version = version
        self.create_action('about', self.on_about_action)
        self.create_action('shortcuts', self.on_shortcuts_action, \
            ['<primary>question'])
        self.create_action('quit', self.on_quit_action, ['<primary>Q'])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = TimeSwitchWindow(application=self)
            self.create_action('stop-timer', \
                lambda *args : win.stop_timer(self))
        win.present()

    def on_shortcuts_action(self, widget, args):
        self.shortcuts_win = None
        for w in self.get_windows():
            if type(w) == Gtk.ShortcutsWindow:
                self.shortcuts_win = w
                break
        if not self.shortcuts_win:
            builder = Gtk.Builder.new_from_resource( \
                '/io/github/fsobolev/TimeSwitch/shortcuts_dialog.ui')
            self.shortcuts_win = builder.get_object('dialog')
            self.shortcuts_win.set_modal(True)
            self.shortcuts_win.set_transient_for(self.props.active_window)
        self.shortcuts_win.present()

    def on_about_action(self, widget, args):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Time Switch',
                                application_icon='io.github.fsobolev.TimeSwitch',
                                developer_name=_('Fyodor Sobolev'),
                                version=self.version,
                                copyright='© 2022 ' + _('Fyodor Sobolev'),
                                website='https://github.com/fsobolev/timeswitch',
                                issue_url='https://github.com/fsobolev/timeswitch/issues',
                                license_type=Gtk.License.MIT_X11,
                                artists=('Igor Dyatlov https://github.com/igor-dyatlov',),
                                translator_credits=_('Translators on Weblate ❤️') + 'https://hosted.weblate.org/projects/timeswitch/timeswitch/\n' + get_translator_credits())
        about.present()

    def on_quit_action(self, widget, args):
        def on_response(w, response):
            if response == 'quit':
                win.close()
                self.quit()

        win = self.props.active_window
        if win.timer:
            dialog = Adw.MessageDialog.new(win, '', \
                _('Are you sure you want to stop the timer and quit?'))
            dialog.add_response('cancel', _('Cancel'))
            dialog.set_close_response('cancel')
            dialog.add_response('quit', _('Quit'))
            dialog.set_default_response('quit')
            dialog.set_response_appearance('quit', \
                Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect('response', on_response)
            dialog.show()
        else:
            win.close()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = TimeSwitchApplication(version)
    return app.run(sys.argv)
