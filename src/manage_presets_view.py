# manage_presets_view.py
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

class ManagePresetsView(Gtk.Stack):
    __gtype_name__ = 'ManagePresetsView'

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.config = window.config
        self.rows = []
        
        self.status = Adw.StatusPage.new()
        self.status.set_vexpand(True)
        self.status.set_icon_name('document-save-symbolic')
        self.status.set_title(_('No Presets Found'))
        self.status.set_description(_('Select desired options on "Timer" page and press the button below to create a preset'))
        self.status_create_button = Gtk.Button.new()
        self.status_create_button.set_label(_('Create Preset'))
        self.status_create_button.set_halign(Gtk.Align.CENTER)
        self.status_create_button.add_css_class('pill')
        self.status_create_button.add_css_class('suggested-action')
        self.status_create_button.connect('clicked', self.create_preset)
        self.status.set_child(self.status_create_button)
        self.add_named(self.status, 'empty')

        self.page = Adw.PreferencesPage.new()
        self.add_named(self.page, 'list')

        self.group = Adw.PreferencesGroup.new()
        self.page.add(self.group)
        self.create_button = Gtk.Button.new()
        self.create_button.set_label(_('Create Preset'))
        self.create_button.connect('clicked', self.create_preset)
        self.create_button.set_halign(Gtk.Align.CENTER)
        self.create_button.set_margin_top(24)
        self.create_button.add_css_class('pill')
        self.group.add(self.create_button)
        
    def list_presets(self):
        for row in self.rows:
            self.group.remove(row)
        if len(self.config.presets) == 0:
            self.set_visible_child_name('empty')
            return
        self.set_visible_child_name('list')
        self.rows = []
        for p in self.config.presets:
            row = Adw.ActionRow.new()
            self.rows.append(row)
            row.set_size_request(-1, 84)
            row.set_focusable(False)
            row.set_title(p['name'])
            row.set_title_lines(1)
            row.set_subtitle_lines(1)
            subtitle = [_('Countdown'), _('Clock')][p['mode']]
            subtitle += f' {p["timer-value"][0]}'
            subtitle += ':{0:0>2}'.format(p['timer-value'][1])
            subtitle += ':{0:0>2}\n'.format(p['timer-value'][2])
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
            move_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
            move_box.add_css_class('linked')
            move_box.set_margin_start(4)
            move_box.set_margin_end(4)
            move_box.set_valign(Gtk.Align.CENTER)
            move_up = Gtk.Button.new_from_icon_name('pan-up-symbolic')
            move_up.set_tooltip_text(_('Move Up'))
            move_up.add_css_class('move-button')
            move_up.connect('clicked', self.move_preset, \
                (self.config.presets.index(p), -1))
            move_up.set_sensitive(self.config.presets.index(p) != 0)
            move_box.append(move_up)
            move_down = Gtk.Button.new_from_icon_name('pan-down-symbolic')
            move_down.set_tooltip_text(_('Move Down'))
            move_down.add_css_class('move-button')
            move_down.connect('clicked', self.move_preset, \
                (self.config.presets.index(p), 1))
            move_down.set_sensitive( \
                self.config.presets.index(p) < len(self.config.presets) - 1)
            move_box.append(move_down)
            row.add_prefix(move_box)
            delete_button = Gtk.Button.new_from_icon_name('user-trash-symbolic')
            delete_button.set_tooltip_text(_('Delete Preset'))
            delete_button.set_valign(Gtk.Align.CENTER)
            delete_button.set_margin_start(6)
            delete_button.set_margin_end(8)
            delete_button.connect('clicked', self.delete_preset, \
                self.config.presets.index(p))
            row.add_suffix(delete_button)
            apply_button = Gtk.Button.new_from_icon_name('emblem-ok-symbolic')
            apply_button.set_tooltip_text(_('Apply Preset'))
            apply_button.set_valign(Gtk.Align.CENTER)
            apply_button.set_margin_start(0)
            apply_button.set_margin_end(6)
            apply_button.connect('clicked', self.activate_preset, \
                self.config.presets.index(p))
            row.add_suffix(apply_button)
            self.group.add(row)

    def move_preset(self, button, args):
        index, offset = args
        if (index + offset) < 0 or \
                (index + offset) > len(self.config.presets) - 1:
            return
        self.config.presets[index], self.config.presets[index+offset] = \
            self.config.presets[index+offset], self.config.presets[index]
        self.config.save()
        self.list_presets()

    def delete_preset(self, button, index):
        self.config.presets.pop(index)
        self.config.save()
        self.list_presets()

    def create_preset(self, button):
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
        dialog.connect('response', self.save_preset, preset_name_row)
        dialog.show()

    def save_preset(self, d, response, name_row):
        name = name_row.get_text()
        if len(name) < 1 or response != 'save':
            return
        mode = int(self.window.clock_mode_toggle.get_active())
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
                        int(self.window.notification_settings.play_sound_switch.get_active()) + \
                        int(self.window.notification_settings.play_until_stopped_switch.get_active()))
                elif c == 4:
                    for cc in range(len(self.window.commands_widgets['checks'])):
                        if self.window.commands_widgets['checks'][cc].get_active():
                            action.append(cc)
                            break
                else:
                    action.append(0)
                break
        notification_text = \
            self.window.notification_settings.notification_text.get_text() \
            if action[0] == 3 else ""
        self.config.presets.append({ \
            'name': name, \
            'mode': mode, \
            'timer-value': timer_value, \
            'action': action, \
            'notification-text': notification_text})
        self.config.save()
        self.list_presets()
    
    def activate_preset(self, button, index):
        settings = self.config.presets[index]
        self.window.clock_mode_toggle.set_active(settings['mode'])
        self.window.hour_spin.set_value(settings['timer-value'][0])
        self.window.min_spin.set_value(settings['timer-value'][1])
        self.window.sec_spin.set_value(settings['timer-value'][2])
        if settings['action'][0] != 4:
            self.window.actions_stack.set_visible_child_name('actions')
        [self.window.action_poweroff, self.window.action_reboot, \
            self.window.action_suspend, self.window.action_notify, \
            self.window.action_command][settings['action'][0]].activate()
        self.window.notification_settings.notification_text.set_text( \
            settings['notification-text'])
        if settings['action'][0] == 3:
            self.window.notification_settings.play_sound_switch.set_active( \
                bool(settings['action'][1]))
            if settings['action'][1] > 1:
                self.window.notification_settings.play_until_stopped_switch.set_active(True)
        elif settings['action'][0] == 4:
            if len(self.window.commands_widgets['rows']) > \
                    settings['action'][1]:
                self.window.commands_widgets['rows'][ \
                settings['action'][1]].activate()
        self.window.setup_stack.set_visible_child_name('main')
