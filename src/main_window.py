# main_window.py
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

from gi.repository import Adw, Gtk, GLib, Gio
from .config import TimeSwitchConfig
from .timer import Timer
from .presets_manager import PresetsManager
from .main_window_shortcuts import set_shortcuts
from .cmd_warning import WarningDialog
import datetime


class TimeSwitchWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TimeSwitchWindow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer = None
        self.set_hide_on_close(True)
        self.config = TimeSwitchConfig()
        set_shortcuts(self)

        # If timer has finished and the window is hidden, the app must quit
        self.quit_on_finish = False # Sets to True when window is hidden

        self.connect('show', self.on_window_show)
        self.connect('close-request', self.on_close_request)
        self.get_application().set_accels_for_action('window.close',
            ['<primary>w'])

        self.config.load()
        self.build_ui()
        self.presets_manager = PresetsManager(self)

    def build_ui(self):
        self.set_default_size(*self.config.window_size)
        self.set_title('Time Switch')
        self.content = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.set_content(self.content)

        # Main stack
        self.main_stack = Gtk.Stack.new()
        self.main_stack.set_hexpand(True)
        self.main_stack.set_vexpand(True)
        self.main_stack.set_transition_type(Gtk.StackTransitionType.OVER_LEFT_RIGHT)
        self.content.append(self.main_stack)

        # Main Stack Box
        self.main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.main_stack.add_named(self.main_box, 'setup')

        # Main Stack Headerbar
        self.header_main = Adw.HeaderBar.new()
        self.header_main.set_title_widget(Gtk.Label.new(''))
        self.main_box.append(self.header_main)

        self.timer_mode_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
        self.timer_mode_box.set_margin_start(6)
        self.timer_mode_box.set_margin_end(6)
        self.timer_mode_box.set_valign(Gtk.Align.CENTER)
        self.header_main.pack_start(self.timer_mode_box)

        self.timer_mode_image = Gtk.Image.new_from_icon_name('hourglass-symbolic')
        self.timer_mode_box.append(self.timer_mode_image)

        self.timer_mode_dropdown = Gtk.DropDown.new_from_strings( \
            [_('Countdown'), _('Clock')] )
        self.timer_mode_dropdown.get_first_child().add_css_class('flat')
        self.timer_mode_dropdown.set_tooltip_text(_('Select timer mode'))
        self.timer_mode_dropdown.connect('notify::selected-item', \
            self.change_timer_mode)
        self.timer_mode_box.append(self.timer_mode_dropdown)

        self.presets_menu = Gio.Menu.new()
        self.presets_menu.append(_('Create Preset'), 'win.create-preset')
        self.presets_menu.append(_('Manage Presets'), 'win.manage-presets')
        self.presets_list_section = Gio.Menu.new()
        self.presets_menu.append_section(None, self.presets_list_section)

        self.main_menu_button = Gtk.MenuButton.new()
        self.main_menu_button.set_icon_name('open-menu-symbolic')
        self.main_menu_button.set_tooltip_text(_('Main menu'))
        self.header_main.pack_end(self.main_menu_button)
        self.main_menu = Gio.Menu.new()
        self.main_menu.append_submenu(_('Presets'), self.presets_menu)
        self.main_menu.append(_('Keyboard Shortcuts'), 'app.shortcuts')
        self.main_menu.append(_('About'), 'app.about')
        self.main_menu.append(_('Quit'), 'app.quit')
        self.main_menu_button.set_menu_model(self.main_menu)

        # Scrolled window
        self.scrolled_window = Gtk.ScrolledWindow.new()
        self.scrolled_window.set_min_content_width(300)
        self.main_box.append(self.scrolled_window)

        # Setup page
        self.setup_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 2)
        self.setup_box.set_halign(Gtk.Align.CENTER)
        self.setup_box.set_valign(Gtk.Align.CENTER)
        self.setup_box.set_size_request(280, -1)
        self.setup_box.set_spacing(10)
        self.setup_box.set_margin_top(6)
        self.setup_box.set_margin_bottom(6)
        self.scrolled_window.set_child(self.setup_box)

        # Main timer widget
        self.spins_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.spins_box.set_halign(Gtk.Align.CENTER)
        self.setup_box.append(self.spins_box)

        self.hour_spin = self.create_spinbutton(99)
        for ctrl in self.hour_spin.observe_controllers():
            if isinstance(ctrl, Gtk.EventControllerKey):
                ctrl.connect('key-released', self.on_key_released)
                break
        self.spins_box.append(self.hour_spin)

        self.label1 = Gtk.Label.new(':')
        self.label1.add_css_class('large-text')
        self.label1.set_yalign(0.48)
        self.spins_box.append(self.label1)

        self.min_spin = self.create_spinbutton(59)
        for ctrl in self.min_spin.observe_controllers():
            if isinstance(ctrl, Gtk.EventControllerKey):
                ctrl.connect('key-released', self.on_key_released)
                break
        self.spins_box.append(self.min_spin)

        self.label2 = Gtk.Label.new(':')
        self.label2.add_css_class('large-text')
        self.label2.set_yalign(0.48)
        self.spins_box.append(self.label2)

        self.sec_spin = self.create_spinbutton(59)
        for ctrl in self.sec_spin.observe_controllers():
            if isinstance(ctrl, Gtk.EventControllerKey):
                ctrl.connect('key-released', self.on_key_released)
                break
        self.spins_box.append(self.sec_spin)

        # Buttons for faster timer increase
        self.grid = Gtk.Grid.new()
        self.grid.set_halign(Gtk.Align.CENTER)
        self.grid.set_column_spacing(6)
        self.grid.set_row_spacing(6)
        self.setup_box.append(self.grid)

        buttons = []
        for value in [5, 10, 300, 600]:
            buttons.append(Gtk.Button.new_with_label('+{} {}'.format(
                int(value / 60) if value > 60 else value,
                _('min') if value > 60 else _('sec')
            )))
            buttons[-1].connect('clicked', self.on_add_button_click, value)
            buttons[-1].set_size_request(90, -1)
        self.grid.attach(buttons[0], 0, 0, 1, 1)
        self.grid.attach(buttons[1], 1, 0, 1, 1)
        self.grid.attach(buttons[2], 0, 1, 1, 1)
        self.grid.attach(buttons[3], 1, 1, 1, 1)

        # Reset timer
        self.reset_button = Gtk.Button.new()
        self.reset_button_content = Adw.ButtonContent.new()
        self.reset_button_content.set_halign(Gtk.Align.CENTER)
        self.reset_button_content.set_icon_name('view-refresh-symbolic')
        self.reset_button_content.set_label(_('Reset'))
        self.reset_button.set_child(self.reset_button_content)
        self.reset_button.connect('clicked', self.reset_timer)
        self.grid.attach(self.reset_button, 0, 2, 2, 1)

        # Stack clamp
        self.stack_clamp = Adw.Clamp.new()
        self.stack_clamp.set_maximum_size(500)
        self.stack_clamp.set_margin_start(15)
        self.stack_clamp.set_margin_end(15)
        self.setup_box.append(self.stack_clamp)

        # Actions stack
        self.actions_stack = Gtk.Stack.new()
        self.actions_stack.set_hexpand(True)
        self.actions_stack.set_vexpand(True)
        self.actions_stack.set_transition_type( \
            Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack_clamp.set_child(self.actions_stack)

        # Actions
        self.actions_group = Adw.PreferencesGroup.new()
        self.actions_group.set_title(_('Action'))
        self.actions_stack.add_named(self.actions_group, 'actions')

        # Poweroff
        self.action_poweroff = Adw.ActionRow.new()
        self.action_poweroff.set_title(_('Power Off'))
        self.action_poweroff_check = Gtk.CheckButton.new()
        self.action_poweroff_check.set_can_focus(False)
        self.action_poweroff.add_prefix(self.action_poweroff_check)
        self.action_poweroff.set_activatable_widget(self.action_poweroff_check)
        self.action_poweroff.activate()
        self.actions_group.add(self.action_poweroff)

        # Reboot
        self.action_reboot = Adw.ActionRow.new()
        self.action_reboot.set_title(_('Reboot'))
        self.action_reboot_check = Gtk.CheckButton.new()
        self.action_reboot_check.set_can_focus(False)
        self.action_reboot_check.set_group(self.action_poweroff_check)
        self.action_reboot.add_prefix(self.action_reboot_check)
        self.action_reboot.set_activatable_widget(self.action_reboot_check)
        self.actions_group.add(self.action_reboot)

        # Suspend
        self.action_suspend = Adw.ActionRow.new()
        self.action_suspend.set_title(_('Suspend'))
        self.action_suspend_check = Gtk.CheckButton.new()
        self.action_suspend_check.set_group(self.action_poweroff_check)
        self.action_suspend.add_prefix(self.action_suspend_check)
        self.action_suspend.set_activatable_widget(self.action_suspend_check)
        self.actions_group.add(self.action_suspend)

        # Notification
        self.action_notify = Adw.ActionRow.new()
        self.action_notify.set_title(_('Notification'))
        self.action_notify_check = Gtk.CheckButton.new()
        self.action_notify_check.set_can_focus(False)
        self.action_notify_check.set_group(self.action_poweroff_check)
        self.action_notify.add_prefix(self.action_notify_check)
        self.action_notify.set_activatable_widget(self.action_notify_check)
        self.actions_group.add(self.action_notify)

        self.notification_settings_button = Gtk.MenuButton.new()
        self.notification_settings_button.set_icon_name('emblem-system-symbolic')
        self.notification_settings_button.add_css_class('flat')
        self.notification_settings_button.set_valign(Gtk.Align.CENTER)
        self.notification_settings_button.set_tooltip_text(
            _('Notification settings'))
        self.action_notify.add_suffix(self.notification_settings_button)

        self.notification_settings = Gtk.Popover.new()
        self.notification_settings_button.set_popover(
            self.notification_settings)
        self.notification_settings_button.set_direction(Gtk.ArrowType.UP)

        self.notification_settings_grid = Gtk.Grid.new()
        self.notification_settings_grid.set_column_spacing(6)
        self.notification_settings_grid.set_row_spacing(6)
        self.notification_settings.set_child(self.notification_settings_grid)

        self.notification_text = Gtk.Entry.new()
        self.notification_text.set_placeholder_text(_('Notification text'))
        self.notification_settings_grid.attach(self.notification_text,
            0, 0, 2, 1)

        self.play_sound_label = Gtk.Label.new(_('Play sound'))
        self.play_sound_label.set_halign(Gtk.Align.START)
        self.notification_settings_grid.attach(self.play_sound_label,
            0, 1, 1, 1)
        self.play_sound_switch = Gtk.Switch.new()
        self.play_sound_switch.set_halign(Gtk.Align.END)
        self.notification_settings_grid.attach(self.play_sound_switch,
            1, 1, 1, 1)

        self.play_until_stopped_label = Gtk.Label.new(_('Until stopped'))
        self.play_until_stopped_label.set_halign(Gtk.Align.START)
        self.notification_settings_grid.attach(self.play_until_stopped_label,
            0, 2, 1, 1)
        self.play_until_stopped_switch = Gtk.Switch.new()
        self.play_until_stopped_switch.set_halign(Gtk.Align.END)
        self.play_sound_switch.connect('notify::active', \
            lambda *args : self.play_until_stopped_switch.set_sensitive( \
                self.play_sound_switch.get_active()))
        self.notification_settings_grid.attach(self.play_until_stopped_switch,
            1, 2, 1, 1)

        # Command execution
        self.action_command = Adw.ActionRow.new()
        self.action_command.set_title(_('Command'))
        self.action_command_check = Gtk.CheckButton.new()
        self.action_command_check.set_can_focus(False)
        self.action_command_check.set_group(self.action_poweroff_check)
        self.action_command.add_prefix(self.action_command_check)
        self.action_command.set_activatable_widget(self.action_command_check)
        self.action_command.connect('activated', self.show_commands)
        self.actions_group.add(self.action_command)

        self.action_command_suffix = \
            Gtk.Image.new_from_icon_name('go-next-symbolic')
        self.action_command_suffix.set_size_request(32, -1)
        self.action_command.add_suffix(self.action_command_suffix)

        # Commands
        self.commands_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        self.actions_stack.add_named(self.commands_box, 'commands')

        self.commands_sw = Gtk.ScrolledWindow.new()
        self.commands_sw.set_min_content_height(270)
        self.commands_box.append(self.commands_sw)

        self.commands_group = Adw.PreferencesGroup.new()
        self.commands_group.set_title(_('Command'))
        self.commands_sw.set_child(self.commands_group)

        self.back_button = Gtk.Button.new()
        self.back_button_content = Adw.ButtonContent.new()
        self.back_button_content.set_icon_name('go-previous-symbolic')
        self.back_button_content.set_label(_('Back'))
        self.back_button.set_child(self.back_button_content)
        self.back_button.connect('clicked', self.show_actions)
        self.commands_group.set_header_suffix(self.back_button)

        self.commands_widgets = {'rows': [], 'checks': []}
        self.invisible_checkbutton = Gtk.CheckButton.new()

        self.add_command_button = Gtk.Button.new()
        self.add_command_button.set_halign(Gtk.Align.CENTER)
        self.add_command_button.add_css_class('pill')
        self.add_command_button_content = Adw.ButtonContent.new()
        self.add_command_button_content.set_icon_name('list-add-symbolic')
        self.add_command_button_content.set_label(_('Add'))
        self.add_command_button.set_child(self.add_command_button_content)
        self.add_command_button.connect('clicked', self.add_command)
        self.commands_box.append(self.add_command_button)

        # Start timer button
        self.start_button = Gtk.Button.new()
        self.start_button.set_halign(Gtk.Align.CENTER)
        self.start_button_content = Adw.ButtonContent.new()
        self.start_button_content.set_icon_name('media-playback-start-symbolic')
        self.start_button_content.set_label(_('Start'))
        self.start_button.set_child(self.start_button_content)
        self.start_button.add_css_class('pill')
        self.start_button.add_css_class('suggested-action')
        self.start_button.connect('clicked', self.start_timer)
        self.setup_box.append(self.start_button)

        # Running page
        self.run_page_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.run_page_box.set_valign(Gtk.Align.FILL)
        self.run_page_box.add_css_class('background')
        self.main_stack.add_named(self.run_page_box, 'running')

        # Running page headerbar
        self.header_run = Adw.HeaderBar.new()
        self.header_run.set_title_widget(Gtk.Label.new(''))
        self.run_page_box.append(self.header_run)

        self.run_menu_button = Gtk.MenuButton.new()
        self.run_menu_button.set_icon_name('open-menu-symbolic')
        self.run_menu_button.set_tooltip_text(_('Main menu'))
        self.header_run.pack_end(self.run_menu_button)
        self.run_menu_button.set_menu_model(self.main_menu)

        # Running timer box
        self.running_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 10)
        self.running_box.set_halign(Gtk.Align.CENTER)
        self.running_box.set_valign(Gtk.Align.CENTER)
        self.running_box.set_vexpand(True)
        self.running_box.set_size_request(280, -1)
        self.run_page_box.append(self.running_box)

        # Description label
        self.desc_label_clamp = Adw.Clamp.new()
        self.desc_label_clamp.set_maximum_size(280)
        self.running_box.append(self.desc_label_clamp)
        self.desc_label = Gtk.Label.new('')
        self.desc_label.set_margin_top(6)
        self.desc_label.set_wrap(True)
        self.desc_label.set_justify(Gtk.Justification.CENTER)
        self.desc_label_clamp.set_child(self.desc_label)

        # Timer label
        self.timer_label = Gtk.Label.new('0:00:00')
        self.timer_label.set_halign(Gtk.Align.CENTER)
        self.timer_label.add_css_class('large-text')
        self.running_box.append(self.timer_label)

        # Pause button
        self.pause_button = Gtk.Button.new()
        self.pause_button.set_halign(Gtk.Align.CENTER)
        self.pause_button_content = Adw.ButtonContent.new()
        self.pause_button_content.set_icon_name('media-playback-pause-symbolic')
        self.pause_button_content.set_label(_('Pause'))
        self.pause_button.set_child(self.pause_button_content)
        self.pause_button.add_css_class('pill')
        self.pause_button.connect('clicked', self.toggle_pause)
        self.running_box.append(self.pause_button)

        # Stop button
        self.stop_button = Gtk.Button.new()
        self.stop_button.set_halign(Gtk.Align.CENTER)
        self.stop_button_content = Adw.ButtonContent.new()
        self.stop_button_content.set_icon_name('media-playback-stop-symbolic')
        self.stop_button_content.set_label(_('Stop'))
        self.stop_button.set_child(self.stop_button_content)
        self.stop_button.add_css_class('pill')
        self.stop_button.add_css_class('destructive-action')
        self.stop_button.connect('clicked', self.stop_timer)
        self.running_box.append(self.stop_button)

        # Warning about window closing
        self.warning_label_clamp = Adw.Clamp.new()
        self.warning_label_clamp.set_maximum_size(280)
        self.running_box.append(self.warning_label_clamp)
        self.warning_label = Gtk.Label.new(
            _('You can close the window, the timer will work in the background.'))
        self.warning_label.add_css_class('dim-label')
        self.warning_label.set_wrap(True)
        self.warning_label.set_margin_top(20)
        self.warning_label.set_margin_bottom(6)
        self.warning_label.set_justify(Gtk.Justification.CENTER)
        self.warning_label_clamp.set_child(self.warning_label)

        # Load config
        self.timer_mode_dropdown.set_selected(self.config.mode)
        (h, m, s) = self.config.last_timer_value
        self.hour_spin.set_value(h)
        self.min_spin.set_value(m)
        self.sec_spin.set_value(s)
        [self.action_poweroff, self.action_reboot, \
            self.action_suspend, self.action_notify, \
            self.action_command][self.config.last_action[0]].activate()
        self.notification_text.get_buffer().set_text( \
            self.config.notification_text, -1)
        for command in self.config.commands:
            self.create_command(command)
        if len(self.commands_widgets['rows']) > 0:
            self.commands_widgets['rows'][0].activate()
        if self.config.last_action[0] == 3:
            self.play_sound_switch.set_active(bool(self.config.last_action[1]))
            self.play_until_stopped_switch.set_sensitive( \
                bool(self.config.last_action[1]))
            if self.config.last_action[1] > 1:
                self.play_until_stopped_switch.set_active(True)
        elif self.config.last_action[0] == 4:
            if len(self.commands_widgets['rows']) > self.config.last_action[1]:
                self.commands_widgets['rows'][ \
                self.config.last_action[1]].activate()

    def create_spinbutton(self, max_value):
        adj = Gtk.Adjustment.new(0.0, 0.0, max_value, 1.0, 10.0, 0.0)
        spin = Gtk.SpinButton.new(adj, 1.0, 0)
        spin.set_orientation(Gtk.Orientation.VERTICAL)
        spin.numeric = True
        spin.set_width_chars(2)
        spin.connect('output', self.show_leading_zeros)
        spin.add_css_class('large-text')
        return spin

    def show_leading_zeros(self, spin):
        spin.set_text('{0:0>2}'.format(spin.get_value_as_int()))
        return True

    def on_add_button_click(self, button, value):
        if value >= 60:
            self.min_spin.set_value(
                self.min_spin.get_value() + value // 60)
        else:
            self.sec_spin.set_value(self.sec_spin.get_value() + value)
        return True

    def change_timer_mode(self, w, pspec):
        self.timer_mode_image.set_from_icon_name( ['hourglass', 'clock-alt'][ \
            self.timer_mode_dropdown.get_selected() ] + '-symbolic')
        self.reset_timer(None)
        if self.timer_mode_dropdown.get_selected() == 0:
            self.hour_spin.get_adjustment().set_upper(99)
        else:
            self.hour_spin.get_adjustment().set_upper(23)

    def reset_timer(self, w):
        self.hour_spin.set_value(0)
        self.min_spin.set_value(0)
        self.sec_spin.set_value(0)
        return True

    def show_actions(self, w):
        self.actions_stack.set_visible_child_name('actions')
        self.action_poweroff.activate()

    def show_commands(self, w):
        self.actions_stack.set_visible_child_name('commands')
        if self.config.show_cmd_warning:
            msg = WarningDialog(self)
            msg.show()

    def set_action_row_titles(self, row, title, subtitle, lines):
        row.set_title(title)
        row.set_title_lines(lines)
        row.set_subtitle(subtitle)
        row.set_subtitle_lines(lines)

    def add_command(self, w):
        msg = Adw.MessageDialog.new(self, _('Add command'), None)
        grid = Gtk.Grid.new()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        name_label = Gtk.Label.new(_('Name'))
        name_label.set_halign(Gtk.Align.START)
        grid.attach(name_label, 0, 0, 1, 1)
        name_entry = Gtk.Entry.new()
        name_entry.set_hexpand(True)
        grid.attach(name_entry, 1, 0, 1, 1)
        cmd_label = Gtk.Label.new(_('Command'))
        cmd_label.set_halign(Gtk.Align.START)
        grid.attach(cmd_label, 0, 1, 1, 1)
        cmd_entry = Gtk.Entry.new()
        cmd_entry.set_hexpand(True)
        grid.attach(cmd_entry, 1, 1, 1, 1)
        msg.set_extra_child(grid)
        msg.add_response('cancel', _('Cancel'))
        msg.add_response('add', _('Add'))
        msg.set_response_appearance('add', Adw.ResponseAppearance.SUGGESTED)
        msg.connect('response', self.confirm_add, \
            name_entry.get_buffer().get_text, cmd_entry.get_buffer().get_text)
        msg.show()

    def confirm_add(self, w, response, name_fn, cmd_fn):
        if response == 'add':
            name = name_fn()
            cmd = cmd_fn()
            if len(name) < 1 or len(cmd) < 1:
                return
            dict = {'name': name, 'cmd': cmd}
            self.config.commands.append(dict)
            self.create_command(dict)
            self.config.save()

    def create_command(self, command):
        self.commands_widgets['rows'].append(Adw.ActionRow.new())
        self.set_action_row_titles(self.commands_widgets['rows'][-1],
            command['name'], command['cmd'], 1)
        checkbutton = Gtk.CheckButton.new()
        checkbutton.set_can_focus(False)
        self.commands_widgets['checks'].append(checkbutton)
        self.commands_widgets['checks'][-1].set_group(
            self.invisible_checkbutton)
        self.commands_widgets['rows'][-1].add_prefix(
            self.commands_widgets['checks'][-1])
        self.commands_widgets['rows'][-1].set_activatable_widget(
            self.commands_widgets['checks'][-1])
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
        edit_button = Gtk.Button.new_from_icon_name('document-edit-symbolic')
        edit_button.set_valign(Gtk.Align.CENTER)
        edit_button.set_tooltip_text(_('Edit command'))
        edit_button.connect('clicked', self.edit_command, \
            self.commands_widgets['rows'][-1])
        box.append(edit_button)
        remove_button = Gtk.Button.new_from_icon_name('user-trash-symbolic')
        remove_button.set_valign(Gtk.Align.CENTER)
        remove_button.add_css_class('destructive-action')
        remove_button.set_tooltip_text(_('Remove command'))
        remove_button.connect('clicked', \
            self.remove_command, self.commands_widgets['rows'][-1])
        box.append(remove_button)
        self.commands_widgets['rows'][-1].add_suffix(box)
        self.commands_group.add(self.commands_widgets['rows'][-1])
        self.commands_widgets['rows'][-1].activate()

    def edit_command(self, w, action_row):
        index = self.commands_widgets['rows'].index(action_row)
        msg = Adw.MessageDialog.new(self, _('Edit command'), None)
        grid = Gtk.Grid.new()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        name_label = Gtk.Label.new(_('Name'))
        name_label.set_halign(Gtk.Align.START)
        grid.attach(name_label, 0, 0, 1, 1)
        name_entry = Gtk.Entry.new()
        name_entry.set_buffer(Gtk.EntryBuffer.new(action_row.get_title(), -1))
        name_entry.set_hexpand(True)
        grid.attach(name_entry, 1, 0, 1, 1)
        cmd_label = Gtk.Label.new(_('Command'))
        cmd_label.set_halign(Gtk.Align.START)
        grid.attach(cmd_label, 0, 1, 1, 1)
        cmd_entry = Gtk.Entry.new()
        cmd_entry.set_buffer(Gtk.EntryBuffer.new(action_row.get_subtitle(), -1))
        cmd_entry.set_hexpand(True)
        grid.attach(cmd_entry, 1, 1, 1, 1)
        msg.set_extra_child(grid)
        msg.add_response('cancel', _('Cancel'))
        msg.add_response('apply', _('Apply'))
        msg.set_response_appearance('apply', Adw.ResponseAppearance.SUGGESTED)
        msg.connect('response', self.confirm_edit, index, \
            name_entry.get_buffer().get_text, cmd_entry.get_buffer().get_text)
        msg.show()

    def confirm_edit(self, w, response, index, name_fn, cmd_fn):
        name = name_fn()
        cmd = cmd_fn()
        if response == 'apply':
            self.set_action_row_titles(self.commands_widgets['rows'][index], \
                name, cmd, 1)
            self.config.commands[index]['name'] = name
            self.config.commands[index]['cmd'] = cmd
            self.config.save()

    def remove_command(self, w, action_row):
        index = self.commands_widgets['rows'].index(action_row)
        msg = Adw.MessageDialog.new(self, _('Remove command?'), \
            _('Are you sure you want to remove command "{}"?').format( \
            self.config.commands[index]['name']))
        msg.add_response('cancel', _('Cancel'))
        msg.add_response('remove', _('Remove'))
        msg.set_response_appearance('remove', Adw.ResponseAppearance.DESTRUCTIVE)
        msg.connect('response', self.confirm_remove, index)
        msg.show()

    def confirm_remove(self, w, response, index):
        if response == 'remove':
            self.commands_group.remove(self.commands_widgets['rows'][index])
            self.commands_widgets['rows'].pop(index)
            self.commands_widgets['checks'].pop(index)
            self.config.commands.pop(index)
            if len(self.commands_widgets['rows']) > 0:
                self.commands_widgets['rows'][0].activate()
            self.config.save()

    def start_timer(self, w):
        if self.timer_mode_dropdown.get_selected() == \
                self.hour_spin.get_value_as_int() == \
                self.min_spin.get_value_as_int() == \
                self.sec_spin.get_value_as_int() == 0:
            return
        self.config.last_timer_value = [ \
            self.hour_spin.get_value_as_int(), \
            self.min_spin.get_value_as_int(), \
            self.sec_spin.get_value_as_int() \
        ]
        checkbuttons = [self.action_poweroff_check, self.action_reboot_check, \
            self.action_suspend_check, self.action_notify_check, \
            self.action_command_check]
        for c in range(len(checkbuttons)):
            if checkbuttons[c].get_active():
                self.config.last_action[0] = c
                if c == 3:
                    if not self.play_sound_switch.get_active():
                        self.play_until_stopped_switch.set_active(False)
                    self.config.last_action[1] = \
                        int(self.play_sound_switch.get_active()) + \
                        int(self.play_until_stopped_switch.get_active())
                elif c == 4:
                    for cc in range(len(self.commands_widgets['checks'])):
                        if self.commands_widgets['checks'][cc].get_active():
                            self.config.last_action[1] = cc
                            break
                else:
                    self.config.last_action[1] = 0
                break
        self.config.notification_text = \
            self.notification_text.get_buffer().get_text()
        self.config.mode = self.timer_mode_dropdown.get_selected()
        self.config.window_size = self.get_default_size()
        self.config.save()
        if self.action_poweroff_check.get_active():
            action = ('poweroff',)
        elif self.action_reboot_check.get_active():
            action = ('reboot',)
        elif self.action_suspend_check.get_active():
            action = ('suspend',)
        elif self.action_notify_check.get_active():
            action = ('notification',
                self.notification_text.get_buffer().get_text(),
                self.play_sound_switch.get_active() + \
                self.play_until_stopped_switch.get_active())
        elif self.action_command_check.get_active():
            name = ''
            cmd = ''
            for c in self.commands_widgets['checks']:
                if c.get_active():
                    index = self.commands_widgets['checks'].index(c)
                    name = self.config.commands[index]['name']
                    cmd = self.config.commands[index]['cmd']
                    break
            if not name:
                return
            action = ('command', name, cmd)
        self.pause_button.set_sensitive(True)
        if self.timer_mode_dropdown.get_selected() == 0:
            time = (self.hour_spin.get_value_as_int(),
                self.min_spin.get_value_as_int(),
                self.sec_spin.get_value_as_int())
        else:
            now = datetime.datetime.now()
            target = now.replace(hour = self.hour_spin.get_value_as_int(),
                minute = self.min_spin.get_value_as_int(),
                second = self.sec_spin.get_value_as_int())
            if target < now:
                target += datetime.timedelta(days = 1)
            minutes, seconds = divmod((target - now).seconds, 60)
            hours, minutes = divmod(minutes, 60)
            time = (hours, minutes, seconds)
        self.timer = Timer(
            *time,
            action,
            self.timer_label,
            self.desc_label,
            self.pause_button,
            self.finish)
        self.timer.run()
        self.main_stack.set_visible_child_name('running')

    def toggle_pause(self, w):
        if self.timer.pause:
            self.pause_button_content.set_icon_name('media-playback-pause-symbolic')
            self.pause_button_content.set_label(_('Pause'))
            self.pause_button.remove_css_class('suggested-action')
        else:
            self.pause_button_content.set_icon_name('media-playback-start-symbolic')
            self.pause_button_content.set_label(_('Continue'))
            self.pause_button.add_css_class('suggested-action')
        self.timer.pause = not self.timer.pause

    def stop_timer(self, w):
        self.timer.stop_timer()
        self.finish()

    def finish(self):
        self.timer = None
        if self.quit_on_finish:
            # Wait in case we have notification with sound
            GLib.usleep(2_000_000)
            self.get_application().quit()
        else:
            self.main_stack.set_visible_child_name('setup')

    def on_window_show(self, w):
        self.quit_on_finish = False
        if self.timer:
            self.main_stack.set_visible_child_name('running')

    def on_close_request(self, w):
        self.config.window_size = self.get_default_size()
        self.config.save()
        if self.timer:
            self.quit_on_finish = True
        else:
            self.get_application().quit()

    def on_key_released(self, w, val, code, *args):
        if code == 36 or code == 104:
            self.start_timer(w)

