# cmd_warning.py
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

from gi.repository import Adw, Gtk
import os

class WarningDialog(Adw.MessageDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_modal(True)
        self.set_transient_for(self.parent)

        self.set_heading(_('Warning'))

        if os.path.exists('/.flatpak-info'):
            flatpak_warning = \
                _('They will be executed outside of flatpak sandbox. ')
        else:
            flatpak_warning = ''
        self.set_body(_("Your commands will be executed as if they were executed on a command prompt. {}The app doesn't perform any checks whether a command was executed successfully or not. Be careful, do not enter commands whose result is unknown to you.").format(flatpak_warning))

        self.add_response('cancel', _('Cancel'))
        self.set_default_response('cancel')
        self.set_close_response('cancel')
        self.add_response('continue', _('Continue'))
        self.set_response_appearance('continue', \
            Adw.ResponseAppearance.SUGGESTED)
        self.set_response_enabled('continue', False)
        ar = Adw.ActionRow.new()
        ar.set_title(_('I understand'))
        ar_switch = Gtk.Switch.new()
        ar_switch.set_valign(Gtk.Align.CENTER)
        ar.add_prefix(ar_switch)
        ar.set_activatable_widget(ar_switch)
        ar_switch.connect('state-set', self.pass_warning)
        ar.remove_css_class('activatable')
        self.set_extra_child(ar)

        self.connect('response', self.on_response)

    def pass_warning(self, w, state):
        self.set_response_enabled('continue', state)

    def on_response(self, w, response):
        if response == 'continue':
            self.parent.config.show_cmd_warning = False
        else:
            self.parent.show_actions(None)
