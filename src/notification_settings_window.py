# notification_settings_window.py
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

from gi.repository import Adw, Gtk

class NotificationSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'NotificationSettingsWindow'

    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)
        self.set_hide_on_close(True)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_search_enabled(False)
        self.set_title('Notification Settings')
        self.set_default_size(360, 260)

        self.page = Adw.PreferencesPage.new()
        self.add(self.page)
        self.group = Adw.PreferencesGroup.new()
        self.page.add(self.group)

        self.notification_text = Adw.EntryRow.new()
        self.notification_text.set_title(_('Notification Text'))
        self.group.add(self.notification_text)

        self.play_sound_row = Adw.ActionRow.new()
        self.play_sound_row.set_title(_('Play sound'))
        self.group.add(self.play_sound_row)
        self.play_sound_switch = Gtk.Switch.new()
        self.play_sound_switch.set_valign(Gtk.Align.CENTER)
        self.play_sound_row.add_suffix(self.play_sound_switch)

        self.play_until_stopped_row = Adw.ActionRow.new()
        self.play_until_stopped_row.set_title(_('Until stopped'))
        self.group.add(self.play_until_stopped_row)
        self.play_until_stopped_switch = Gtk.Switch.new()
        self.play_until_stopped_switch.set_valign(Gtk.Align.CENTER)
        self.play_until_stopped_row.add_suffix(self.play_until_stopped_switch)
        self.play_until_stopped_row.set_sensitive(False)
        self.play_sound_switch.connect('notify::active', \
            self.set_until_stopped_state)

    def set_until_stopped_state(self, *args):
        self.play_until_stopped_row.set_sensitive( \
            self.play_sound_switch.get_active())
        if not self.play_sound_switch.get_active():
            self.play_until_stopped_switch.set_active(False)
