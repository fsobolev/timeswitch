# player.py
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

from gi.repository import GSound

class Player:
    def __init__(self, repeat, cancellable):
        self.gsound = GSound.Context.new()
        self.gsound.init()
        self.repeat = repeat
        self.cancellable = cancellable

        if self.repeat:
            self.sound_id = 'alarm-clock-elapsed'
        else:
            self.sound_id = 'complete'

    def play(self):
        self.gsound.play_full({GSound.ATTR_EVENT_ID: self.sound_id, \
            GSound.ATTR_MEDIA_ROLE: 'alarm'}, self.cancellable, \
            self.sound_finished)

    def sound_finished(self, *args):
        if self.repeat and not self.cancellable.is_cancelled():
            self.play()
