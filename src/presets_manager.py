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
from .manage_presets_window import ManagePresetsWindow

class PresetsManager:
    def __init__(self, window):
        self.window = window
        self.config = window.config

        action_create = Gio.SimpleAction.new('create-preset', None)
        action_create.connect('activate', lambda *args: self.create_preset())
        self.window.add_action(action_create)

        self.action_manage = Gio.SimpleAction.new('manage-presets', None)
        self.action_manage.connect('activate', lambda *args: self.manage_presets())
        self.window.add_action(self.action_manage)

        self.generate_presets()

    def generate_presets(self):
        self.window.presets_list_section.remove_all()
        self.action_manage.set_enabled( \
            len(self.config.presets) > 0)
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
        self.window.notification_text.get_buffer().set_text( \
            settings['notification-text'], -1)
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
        def entry_callback(row, pspec, dialog):
            if pspec.name == 'text':
                dialog.set_response_enabled('save', len(row.get_text()) > 0)

        dialog = Adw.MessageDialog.new(self.window, _('Create Preset'), \
            _('Currently selected options will be saved in a new preset with the provided name.'))
        preset_name_row = Adw.EntryRow.new()
        preset_name_row.set_title(_('Preset Name'))
        preset_name_row.add_css_class('card')
        preset_name_row.set_activates_default(True)
        dialog.set_extra_child(preset_name_row)
        dialog.add_response('cancel', _('Cancel'))
        dialog.add_response('save', _('Save'))
        dialog.set_response_appearance('save', Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response('save')
        dialog.set_response_enabled('save', False)
        preset_name_row.connect('notify', entry_callback, dialog)
        dialog.connect('response', lambda d, response: \
            self.save_preset(preset_name_row.get_text()))
        dialog.show()

    def save_preset(self, name):
        if len(name) < 1:
            return
        mode = self.window.timer_mode_dropdown.get_selected()
        timer_value = [ \
            self.window.hour_spin.get_value_as_int(), \
            self.window.min_spin.get_value_as_int(), \
            self.window.sec_spin.get_value_as_int() ]
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
        notification_text = \
            self.window.notification_text.get_buffer().get_text() \
            if action[0] == 3 else ""
        self.config.presets.append({ \
            'name': name, \
            'mode': mode, \
            'timer-value': timer_value, \
            'action': action, \
            'notification-text': notification_text})
        self.config.save()
        self.generate_presets()

    def manage_presets(self):
        dialog = ManagePresetsWindow()
        dialog.set_modal(True)
        dialog.set_transient_for(self.window)
        dialog.config = self.config
        dialog.list_presets()
        dialog.show()
        dialog.connect('close-request', lambda *args: self.generate_presets())
