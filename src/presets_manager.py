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

from gi.repository import Adw, Gio

class PresetsManager:
    def __init__(self, window):
        self.window = window
        self.config = window.config
        self.generate_presets()

        action_create = Gio.SimpleAction.new('create-preset', None)
        action_create.connect('activate', lambda *args: self.create_preset())
        self.window.add_action(action_create)

    def generate_presets(self):
        self.window.presets_list_section.remove_all()
        for i in range(len(self.config.presets)):
            self.window.remove_action(f'preset-{i}')
            action = Gio.SimpleAction.new(f'preset-{i}', None)
            action.connect('activate', self.activate_preset)
            self.window.add_action(action)
            self.window.presets_list_section.append( \
                self.config.presets[i]['name'], f'win.preset-{i}')

    def activate_preset(self, action, param):
        settings = self.config.presets[ \
            int(action.get_name().replace('preset-', ''))]
        self.window.timer_mode_dropdown.set_selected(settings['mode'])
        self.window.hour_spin.set_value(settings['timer-value'][0])
        self.window.min_spin.set_value(settings['timer-value'][1])
        self.window.sec_spin.set_value(settings['timer-value'][2])
        if settings['action'][0] != 4:
            self.window.actions_stack.set_visible_child_name('actions')
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

    def create_preset(self):
        dialog = Adw.MessageDialog.new(self.window, _('Create Preset'), \
            _('Currently selected options will be saved in a new preset with the provided name.'))
        preset_name_row = Adw.EntryRow.new()
        preset_name_row.set_title(_('Preset Name'))
        preset_name_row.add_css_class('card')
        dialog.set_extra_child(preset_name_row)
        dialog.add_response('cancel', _('Cancel'))
        dialog.add_response('save', _('Save'))
        dialog.set_response_appearance('save', Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response('save')
        dialog.connect('response', lambda d, response: \
            self.save_preset(preset_name_row.get_text()))
        dialog.show()

    def save_preset(self, name):
        if len(name) < 1:
            return
        mode = self.window.timer_mode_dropdown.get_selected()
        timer_value = [ \
            self.window.hour_spin.get_value(), \
            self.window.min_spin.get_value(), \
            self.window.sec_spin.get_value() ]
        action = []
        checkbuttons = [self.window.action_poweroff_check, \
            self.window.action_reboot_check, \
            self.window.action_suspend_check, \
            self.window.action_notify_check, \
            self.window.action_command_check]
        for c in range(len(checkbuttons)):
            if checkbuttons[c].get_active():
                action.append(c)
                if c == 3:
                    action.append( \
                        int(self.window.play_sound_switch.get_active()) + \
                        int(self.window.play_until_stopped_switch.get_active()))
                elif c == 4:
                    for cc in range(len(self.window.commands_widgets['checks'])):
                        if self.window.commands_widgets['checks'][cc].get_active():
                            action.append(cc)
                            break
                else:
                    action.append(0)
                break
        self.config.presets.append({ \
            'name': name, \
            'mode': mode, \
            'timer-value': timer_value, \
            'action': action })
        self.config.save()
        self.generate_presets()
