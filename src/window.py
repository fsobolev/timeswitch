# window.py
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

from gi.repository import Adw, Gtk, GLib
from .timer import Timer


class TimeSwitchWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TimeSwitchWindow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer = None
        self.set_hide_on_close(True)

        # If timer has finished and the window is hidden, the app must quit
        self.quit_on_finish = False # Sets to True when window is hidden

        self.connect('show', self.on_window_show)
        self.connect('close-request', self.on_close_request)
        self.build_ui()

    def build_ui(self):
        self.set_default_size(320, 655)
        self.set_title('Time Switch')
        self.content = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.set_content(self.content)

        # Headerbar
        self.header = Adw.HeaderBar.new()
        self.header.set_title_widget(Gtk.Label.new(''))
        self.content.append(self.header)

        self.about_button = Gtk.Button.new()
        self.about_button.set_icon_name('help-about-symbolic')
        self.about_button.set_action_name('app.about')
        self.header.pack_start(self.about_button)

        # Stack
        self.stack = Gtk.Stack.new()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        self.content.append(self.stack)

        # Scrolled window
        self.scrolled_window = Gtk.ScrolledWindow.new()
        self.scrolled_window.set_min_content_width(300)
        self.stack.add_named(self.scrolled_window, 'setup')

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
        self.spins_box.append(self.hour_spin)

        self.label1 = Gtk.Label.new(':')
        self.label1.add_css_class('large-text')
        self.label1.set_yalign(0.48)
        self.spins_box.append(self.label1)

        self.min_spin = self.create_spinbutton(59)
        self.spins_box.append(self.min_spin)

        self.label2 = Gtk.Label.new(':')
        self.label2.add_css_class('large-text')
        self.label2.set_yalign(0.48)
        self.spins_box.append(self.label2)

        self.sec_spin = self.create_spinbutton(59)
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
        self.reset_button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.reset_button_box.set_halign(Gtk.Align.CENTER)
        self.reset_button_icon = \
            Gtk.Image.new_from_icon_name('view-refresh-symbolic')
        self.reset_button_box.append(self.reset_button_icon)
        self.reset_button_label = Gtk.Label.new(_('Reset'))
        self.reset_button_box.append(self.reset_button_label)
        self.reset_button.set_child(self.reset_button_box)
        self.reset_button.connect('clicked', self.reset_timer)
        self.grid.attach(self.reset_button, 0, 2, 2, 1)

        # Actions
        self.actions_group = Adw.PreferencesGroup.new()
        self.actions_group.set_title(_('Action'))
        self.setup_box.append(self.actions_group)

        # Poweroff
        self.action_poweroff = Adw.ActionRow.new()
        self.action_poweroff.set_title(_('Power Off'))
        self.action_poweroff_check = Gtk.CheckButton.new()
        self.action_poweroff.add_prefix(self.action_poweroff_check)
        self.action_poweroff.set_activatable_widget(self.action_poweroff_check)
        self.action_poweroff.activate()
        self.actions_group.add(self.action_poweroff)

        # Reboot
        self.action_reboot = Adw.ActionRow.new()
        self.action_reboot.set_title(_('Reboot'))
        self.action_reboot_check = Gtk.CheckButton.new()
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
        self.action_notify_check.set_group(self.action_poweroff_check)
        self.action_notify.add_prefix(self.action_notify_check)
        self.action_notify.set_activatable_widget(self.action_notify_check)
        self.actions_group.add(self.action_notify)

        self.notification_settings_button = Gtk.MenuButton.new()
        self.notification_settings_button.set_icon_name('emblem-system-symbolic')
        self.notification_settings_button.add_css_class('flat')
        self.notification_settings_button.set_valign(Gtk.Align.CENTER)
        self.action_notify.add_suffix(self.notification_settings_button)

        self.notification_settings = Gtk.Popover.new()
        self.notification_settings_button.set_popover(
            self.notification_settings)
        self.notification_settings_button.set_direction(Gtk.ArrowType.UP)

        self.notification_settings_grid = Gtk.Grid.new()
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

        # Start timer button
        self.start_button = Gtk.Button.new()
        self.start_button.set_halign(Gtk.Align.CENTER)
        self.start_button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.start_button_box.set_halign(Gtk.Align.CENTER)
        self.start_button_icon = \
            Gtk.Image.new_from_icon_name('media-playback-start-symbolic')
        self.start_button_box.append(self.start_button_icon)
        self.start_button_label = Gtk.Label.new(_('Start'))
        self.start_button_box.append(self.start_button_label)
        self.start_button.set_child(self.start_button_box)
        self.start_button.add_css_class('pill')
        self.start_button.add_css_class('suggested-action')
        self.start_button.connect("clicked", self.start_timer)
        self.setup_box.append(self.start_button)

        # Running page
        self.running_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 2)
        self.running_box.set_halign(Gtk.Align.CENTER)
        self.running_box.set_valign(Gtk.Align.CENTER)
        self.running_box.set_size_request(280, -1)
        self.running_box.set_spacing(10)
        self.stack.add_named(self.running_box, 'running')

        # Description label
        self.desc_label_clamp = Adw.Clamp.new()
        self.desc_label_clamp.set_maximum_size(280)
        self.running_box.append(self.desc_label_clamp)
        self.desc_label = Gtk.Label.new('')
        #self.desc_label.set_halign(Gtk.Align.CENTER)
        self.desc_label.set_margin_top(6)
        self.desc_label.set_wrap(True)
        self.desc_label.set_justify(Gtk.Justification.CENTER)
        self.desc_label_clamp.set_child(self.desc_label)

        # Timer label
        self.timer_label = Gtk.Label.new('0:00:00')
        self.timer_label.set_halign(Gtk.Align.CENTER)
        self.timer_label.add_css_class('large-text')
        self.running_box.append(self.timer_label)

        # Stop button
        self.stop_button = Gtk.Button.new()
        self.stop_button.set_halign(Gtk.Align.CENTER)
        self.stop_button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.stop_button_box.set_halign(Gtk.Align.CENTER)
        self.stop_button_icon = \
            Gtk.Image.new_from_icon_name('media-playback-stop-symbolic')
        self.stop_button_box.append(self.stop_button_icon)
        self.stop_button_label = Gtk.Label.new(_('Stop'))
        self.stop_button_box.append(self.stop_button_label)
        self.stop_button.set_child(self.stop_button_box)
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

    def reset_timer(self, _):
        self.hour_spin.set_value(0)
        self.min_spin.set_value(0)
        self.sec_spin.set_value(0)
        return True

    def start_timer(self, _):
        if self.hour_spin.get_value_as_int() == \
                self.min_spin.get_value_as_int() == \
                self.sec_spin.get_value_as_int() == 0:
            return
        if self.action_poweroff_check.get_active():
            action = ('poweroff',)
        elif self.action_reboot_check.get_active():
            action = ('reboot',)
        elif self.action_suspend_check.get_active():
            action = ('suspend',)
        elif self.action_notify_check.get_active():
            action = ('notification',
                self.notification_text.get_buffer().get_text(),
                self.play_sound_switch.get_active())
        self.timer = Timer(
            self.hour_spin.get_value_as_int(),
            self.min_spin.get_value_as_int(),
            self.sec_spin.get_value_as_int(),
            action,
            self.timer_label,
            self.desc_label,
            self.finish)
        self.timer.run()
        self.stack.set_visible_child_name('running')

    def stop_timer(self, _):
        self.timer.stop = True
        self.finish()

    def finish(self):
        self.timer = None
        if self.quit_on_finish:
            # Wait in case we have notification with sound
            GLib.usleep(2_000_000)
            self.get_application().quit()
        else:
            self.stack.set_visible_child_name('setup')

    def on_window_show(self, _):
        self.quit_on_finish = False
        if self.timer:
            self.stack.set_visible_child_name('running')

    def on_close_request(self, _):
        if self.timer:
            self.quit_on_finish = True
        else:
            self.get_application().quit()
