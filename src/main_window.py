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

from gi.repository import Adw, Gtk, GLib, Gio, GObject
from .cmd_warning import WarningDialog
from .config import TimeSwitchConfig
from .main_window_shortcuts import set_shortcuts
from .manage_presets_view import ManagePresetsView
from .notification_settings_window import NotificationSettingsWindow
from .timer import Timer
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

    def build_ui(self):
        self.set_default_size(*self.config.window_size)
        self.set_title('Time Switch')
        self.content = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.set_content(self.content)

        # Main stack
        # Switches between setup and running
        self.main_stack = Gtk.Stack.new()
        self.main_stack.set_hexpand(True)
        self.main_stack.set_vexpand(True)
        self.main_stack.set_transition_type(Gtk.StackTransitionType.OVER_LEFT_RIGHT)
        self.content.append(self.main_stack)

        self.main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.main_stack.add_named(self.main_box, 'setup')

        # Main Stack Headerbar
        self.header_main = Adw.HeaderBar.new()
        self.setup_stack_switcher = Adw.ViewSwitcher.new()
        self.header_main.set_title_widget(self.setup_stack_switcher)
        self.main_box.append(self.header_main)

        self.presets_menu = Gio.Menu.new()
        self.presets_menu.append(_('Create Preset'), 'win.create-preset')
        self.presets_menu.append(_('Manage Presets'), 'win.manage-presets')
        self.presets_list_section = Gio.Menu.new()
        self.presets_menu.append_section(None, self.presets_list_section)

        self.main_menu_button = Gtk.MenuButton.new()
        self.main_menu_button.set_icon_name('open-menu-symbolic')
        self.main_menu_button.set_tooltip_text(_('Main menu'))
        self.header_main.pack_start(self.main_menu_button)
        self.main_menu = Gio.Menu.new()
        self.main_menu.append(_('Keyboard Shortcuts'), 'app.shortcuts')
        self.main_menu.append(_('About Time Switch'), 'app.about')
        self.main_menu.append(_('Quit'), 'app.quit')
        self.main_menu_button.set_menu_model(self.main_menu)

        # Overlay
        self.overlay = Gtk.Overlay.new()
        self.start_button = Gtk.Button.new()
        self.start_button.set_halign(Gtk.Align.CENTER)
        self.start_button.set_valign(Gtk.Align.END)
        self.start_button.set_margin_bottom(8)
        self.start_button_content = Adw.ButtonContent.new()
        self.start_button_content.set_icon_name('media-playback-start-symbolic')
        self.start_button_content.set_label(_('Start'))
        self.start_button.set_child(self.start_button_content)
        self.start_button.add_css_class('pill')
        self.start_button.add_css_class('suggested-action')
        self.start_button.connect('clicked', self.start_timer)
        self.overlay.add_overlay(self.start_button)

        # Scrolled window
        self.scrolled_window = Gtk.ScrolledWindow.new()
        self.scrolled_window.set_min_content_width(300)
        self.overlay.set_child(self.scrolled_window)

        # Setup stack
        # Switches between timer and presets
        self.setup_stack = Adw.ViewStack.new()
        self.main_box.append(self.setup_stack)
        self.setup_stack_switcher.set_stack(self.setup_stack)
        self.setup_stack.add_titled_with_icon(self.overlay, "main", \
            _("Timer"), "hourglass-symbolic")
        self.presets_view = ManagePresetsView(self)
        self.presets_view.list_presets()
        self.setup_stack.add_titled_with_icon(self.presets_view, "presets", \
            _("Presets"), "view-list-symbolic")

        # Setup page
        self.setup_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 2)
        self.setup_box.set_halign(Gtk.Align.CENTER)
        self.setup_box.set_valign(Gtk.Align.START)
        self.setup_box.set_size_request(280, -1)
        self.setup_box.set_spacing(8)
        self.setup_box.set_margin_top(8)
        self.setup_box.set_margin_bottom(60)
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

        # Timer mode switcher
        self.timer_mode_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.timer_mode_box.add_css_class('linked')
        self.timer_mode_box.set_homogeneous(True)
        self.timer_mode_box.set_halign(Gtk.Align.CENTER)
        self.setup_box.append(self.timer_mode_box)
        self.countdown_mode_toggle = Gtk.ToggleButton.new()
        self.countdown_mode_toggle.set_label(_('Countdown'))
        self.countdown_mode_toggle.set_tooltip_text(_('Set countdown timer'))
        self.timer_mode_box.append(self.countdown_mode_toggle)
        self.clock_mode_toggle = Gtk.ToggleButton.new()
        self.clock_mode_toggle.set_label(_('Clock'))
        self.clock_mode_toggle.set_tooltip_text(_('Set time in 24h format'))
        self.timer_mode_box.append(self.clock_mode_toggle)
        self.countdown_mode_toggle.connect("toggled", self.change_timer_mode)
        self.countdown_mode_toggle.bind_property("active", \
            self.clock_mode_toggle, "active", \
            GObject.BindingFlags.BIDIRECTIONAL | \
            GObject.BindingFlags.SYNC_CREATE | \
            GObject.BindingFlags.INVERT_BOOLEAN)

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

        # Сlamp
        self.actions_clamp = Adw.Clamp.new()
        self.actions_clamp.set_maximum_size(600)
        self.actions_clamp.set_tightening_threshold(600)
        self.actions_clamp.set_margin_start(8)
        self.actions_clamp.set_margin_end(8)
        self.setup_box.append(self.actions_clamp)

        # Actions
        self.actions_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 2)
        self.actions_clamp.set_child(self.actions_box)

        self.actions_top = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.actions_top.set_margin_start(4)
        self.actions_top.set_margin_end(4)
        self.actions_box.append(self.actions_top)
        self.actions_label = Gtk.Label.new(_('Action'))
        self.actions_label.add_css_class('heading')
        self.actions_label.set_halign(Gtk.Align.START)
        self.actions_label.set_margin_top(2)
        self.actions_label.set_hexpand(True)
        self.actions_top.append(self.actions_label)
        self.add_command_button = Gtk.Button.new()
        self.add_command_button.add_css_class('flat')
        self.add_command_button_content = Adw.ButtonContent.new()
        self.add_command_button_content.set_icon_name('list-add-symbolic')
        self.add_command_button_content.set_label(_('Add'))
        self.add_command_button.set_child(self.add_command_button_content)
        self.add_command_button.connect('clicked', self.add_command_start)
        self.actions_top.append(self.add_command_button)

        self.actions_flowbox = Gtk.FlowBox.new()
        self.actions_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.actions_flowbox.set_homogeneous(True)
        self.actions_box.append(self.actions_flowbox)

        # Poweroff
        self.action_grp_poweroff = Adw.PreferencesGroup.new()
        self.actions_flowbox.append(self.action_grp_poweroff)
        self.action_grp_poweroff.get_parent().set_focusable(False)
        self.action_poweroff = Adw.ActionRow.new()
        self.action_poweroff.set_title(_('Power Off'))
        self.action_poweroff_check = Gtk.CheckButton.new()
        self.action_poweroff_check.set_can_focus(False)
        self.action_poweroff.add_prefix(self.action_poweroff_check)
        self.action_poweroff.set_activatable_widget(self.action_poweroff_check)
        self.action_poweroff.activate()
        self.action_grp_poweroff.add(self.action_poweroff)

        # Reboot
        self.action_grp_reboot = Adw.PreferencesGroup.new()
        self.actions_flowbox.append(self.action_grp_reboot)
        self.action_grp_reboot.get_parent().set_focusable(False)
        self.action_reboot = Adw.ActionRow.new()
        self.action_reboot.set_title(_('Reboot'))
        self.action_reboot_check = Gtk.CheckButton.new()
        self.action_reboot_check.set_can_focus(False)
        self.action_reboot_check.set_group(self.action_poweroff_check)
        self.action_reboot.add_prefix(self.action_reboot_check)
        self.action_reboot.set_activatable_widget(self.action_reboot_check)
        self.action_grp_reboot.add(self.action_reboot)

        # Suspend
        self.action_grp_suspend = Adw.PreferencesGroup.new()
        self.actions_flowbox.append(self.action_grp_suspend)
        self.action_grp_suspend.get_parent().set_focusable(False)
        self.action_suspend = Adw.ActionRow.new()
        self.action_suspend.set_title(_('Suspend'))
        self.action_suspend_check = Gtk.CheckButton.new()
        self.action_suspend_check.set_group(self.action_poweroff_check)
        self.action_suspend.add_prefix(self.action_suspend_check)
        self.action_suspend.set_activatable_widget(self.action_suspend_check)
        self.action_grp_suspend.add(self.action_suspend)

        # Notification
        self.action_grp_notify = Adw.PreferencesGroup.new()
        self.actions_flowbox.append(self.action_grp_notify)
        self.action_grp_notify.get_parent().set_focusable(False)
        self.action_notify = Adw.ActionRow.new()
        self.action_notify.set_title(_('Notification'))
        self.action_notify_check = Gtk.CheckButton.new()
        self.action_notify_check.set_can_focus(False)
        self.action_notify_check.set_group(self.action_poweroff_check)
        self.action_notify.add_prefix(self.action_notify_check)
        self.action_notify.set_activatable_widget(self.action_notify_check)
        self.action_grp_notify.add(self.action_notify)

        self.notification_settings_button = Gtk.Button.new()
        self.notification_settings_button.set_icon_name('emblem-system-symbolic')
        self.notification_settings_button.add_css_class('flat')
        self.notification_settings_button.set_valign(Gtk.Align.CENTER)
        self.notification_settings_button.set_tooltip_text(
            _('Notification settings'))
        self.action_notify.add_suffix(self.notification_settings_button)

        self.notification_settings = NotificationSettingsWindow(self)
        self.notification_settings_button.connect('clicked', \
            lambda *args: self.notification_settings.present())

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
        self.header_run.pack_start(self.run_menu_button)
        self.run_menu = Gio.Menu.new()
        self.run_menu.append(_('Keyboard Shortcuts'), 'app.shortcuts')
        self.run_menu.append(_('About Time Switch'), 'app.about')
        self.run_menu.append(_('Quit'), 'app.quit')
        self.run_menu_button.set_menu_model(self.run_menu)

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
        self.clock_mode_toggle.set_active(bool(self.config.mode))
        (h, m, s) = self.config.last_timer_value
        self.hour_spin.set_value(h)
        self.min_spin.set_value(m)
        self.sec_spin.set_value(s)
        if self.config.last_action[0] < 4:
            [self.action_poweroff, self.action_reboot, self.action_suspend, \
                self.action_notify][self.config.last_action[0]].activate()
        self.notification_settings.notification_text.set_text( \
            self.config.notification_text)
        self.commands_widgets = {'groups': [], 'rows': [], 'checks': []}
        for command in self.config.commands:
            self.create_command(command)
        if self.config.last_action[0] == 3:
            self.notification_settings.play_sound_switch.set_active( \
                bool(self.config.last_action[1]))
            if self.config.last_action[1] > 1:
                self.notification_settings.play_until_stopped_switch.set_active(True)
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

    def change_timer_mode(self, w):
        self.reset_timer(None)
        self.hour_spin.get_adjustment().set_upper( \
            99 if self.countdown_mode_toggle.get_active() else 23)

    def reset_timer(self, w):
        self.hour_spin.set_value(0)
        self.min_spin.set_value(0)
        self.sec_spin.set_value(0)
        return True

    def add_command_start(self, w):
        if self.config.show_cmd_warning:
            msg = WarningDialog(self)
            msg.connect('response', self.validate_warning)
            msg.show()
        else:
            self.add_command()

    def validate_warning(self, w, response):
        if response == 'continue':
            self.config.show_cmd_warning = False
            self.add_command()

    def add_command(self):
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
        grp = Adw.PreferencesGroup.new()
        self.commands_widgets['groups'].append(grp)
        row = Adw.ActionRow.new()
        grp.add(row)
        self.commands_widgets['rows'].append(row)
        row.set_title(command['name'])
        row.set_title_lines(1)
        checkbutton = Gtk.CheckButton.new()
        checkbutton.set_can_focus(False)
        checkbutton.set_group(self.action_poweroff_check)
        self.commands_widgets['checks'].append(checkbutton)
        row.add_prefix(checkbutton)
        row.set_activatable_widget(checkbutton)
        edit_button = Gtk.Button.new_from_icon_name('document-edit-symbolic')
        edit_button.set_valign(Gtk.Align.CENTER)
        edit_button.set_tooltip_text(_('Edit command'))
        edit_button.add_css_class('flat')
        edit_button.connect('clicked', self.edit_command, row)
        row.add_suffix(edit_button)
        self.actions_flowbox.append(grp)
        grp.get_parent().set_focusable(False)

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
        cmd_entry.set_buffer(Gtk.EntryBuffer.new( \
            self.config.commands[index]['cmd'], -1))
        cmd_entry.set_hexpand(True)
        grid.attach(cmd_entry, 1, 1, 1, 1)
        msg.set_extra_child(grid)
        msg.add_response('cancel', _('Cancel'))
        msg.add_response('remove', _('Remove'))
        msg.set_response_appearance('remove', Adw.ResponseAppearance.DESTRUCTIVE)
        msg.add_response('apply', _('Apply'))
        msg.set_response_appearance('apply', Adw.ResponseAppearance.SUGGESTED)
        msg.connect('response', self.confirm_edit, index, \
            name_entry.get_buffer().get_text, cmd_entry.get_buffer().get_text)
        msg.show()

    def confirm_edit(self, w, response, index, name_fn, cmd_fn):
        name = name_fn()
        cmd = cmd_fn()
        if response == 'apply':
            self.commands_widgets['rows'][index].set_title(name)
            self.config.commands[index]['name'] = name
            self.config.commands[index]['cmd'] = cmd
            self.config.save()
        elif response == 'remove':
            self.actions_flowbox.remove(self.commands_widgets['groups'][index])
            self.commands_widgets['groups'].pop(index)
            self.commands_widgets['rows'].pop(index)
            self.commands_widgets['checks'].pop(index)
            self.config.commands.pop(index)
            self.action_poweroff.activate()
            self.config.save()

    def start_timer(self, w):
        if self.countdown_mode_toggle.get_active() and \
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
            self.action_suspend_check, self.action_notify_check] + \
            self.commands_widgets['checks']
        for c in range(len(checkbuttons)):
            if checkbuttons[c].get_active():
                self.config.last_action[0] = c if c < 4 else 4
                if c < 3:
                    self.config.last_action[1] = 0
                elif c == 3:
                    if not self.notification_settings.play_sound_switch.get_active():
                        self.notification_settings.play_until_stopped_switch.set_active(False)
                    self.config.last_action[1] = \
                        int(self.notification_settings.play_sound_switch.get_active()) + \
                        int(self.notification_settings.play_until_stopped_switch.get_active())
                else:
                    self.config.last_action[1] = c - 4
                break
        self.config.notification_text = \
            self.notification_settings.notification_text.get_text()
        self.config.mode = int(self.clock_mode_toggle.get_active())
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
                self.notification_settings.notification_text.get_text(),
                self.notification_settings.play_sound_switch.get_active() + \
                self.notification_settings.play_until_stopped_switch.get_active())
        else:
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
        if self.countdown_mode_toggle.get_active():
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

