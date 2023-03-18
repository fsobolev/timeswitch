# manage_presets_window.py
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

class ManagePresetsWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'ManagePresetsWindow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_('Presets'))
        self.set_default_size(360, -1)
        self.set_search_enabled(False)
        self.page = Adw.PreferencesPage.new()
        self.add(self.page)

        self.group = None
        self.config = None

    def list_presets(self):
        if self.config == None:
            return
        if self.group != None:
            self.page.remove(self.group)
        self.group = Adw.PreferencesGroup.new()
        self.page.add(self.group)
        for p in self.config.presets:
            row = Adw.ActionRow.new()
            row.set_title(p['name'])
            subtitle = [_('Countdown'), _('Clock')][p['mode']]
            subtitle += f' {int(p["timer-value"][0])}'
            subtitle += ':{0:0>2}'.format(int(p['timer-value'][1]))
            subtitle += ':{0:0>2} | '.format(int(p['timer-value'][2]))
            if p['action'][0] == 0:
                subtitle += _('Power Off')
            elif p['action'][0] == 1:
                subtitle += _('Reboot')
            elif p['action'][0] == 3:
                if p['action'][1] == 0:
                    subtitle += _('Notification')
                elif p['action'][1] == 1:
                    subtitle += _('Notification with sound')
                elif p['action'][1] == 2:
                    subtitle += _('Notification with sound playing until stopped')
            elif p['action'][0] == 4:
                if (len(self.config.commands) - 1) < p['action'][1]:
                    subtitle += _('Unknown command')
                    row.add_css_class('error')
                else:
                    subtitle += _('Command "{}"').format( \
                        self.config.commands[p['action'][1]]['name'])
            row.set_subtitle(subtitle)
            delete_button = Gtk.Button.new_from_icon_name('user-trash-symbolic')
            delete_button.set_valign(Gtk.Align.CENTER)
            delete_button.connect('clicked', self.delete_preset, \
                self.config.presets.index(p))
            row.add_suffix(delete_button)
            self.group.add(row)

    def delete_preset(self, button, index):
        self.config.presets.pop(index)
        self.config.save()
        if len(self.config.presets) == 0:
            self.close()
        else:
            self.list_presets()
