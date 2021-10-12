###
# Copyright (c) 2021, David Schultz <me@zpld.me>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

from supybot import utils, plugins, ircutils, ircmsgs, callbacks
from supybot.commands import *
from os.path      import expanduser
from ircchallenge import Challenge
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization("ChallengeAuth")
except ImportError:
    _ = lambda x: x

class ChallengeAuth(callbacks.Plugin):
    """Allows opering up via RSA challenge key on ratbox-based ircds"""
    threaded  = True

    def challenge(self, irc, msg, args):
        """takes no arguments

        Initiates an RSA challenge"""
        self.prepChallenge()
        self.requester = irc
        oper = self.registryValue("opername")
        irc.queueMsg(ircmsgs.IrcMsg(f"CHALLENGE {oper}"))
    challenge = wrap(challenge, ["owner"])

    def prepChallenge(self):
        """set up challenge attempt"""
        key = expanduser(self.registryValue("keyfile"))
        password = self.registryValue("password")
        self.challenge = Challenge(keyfile=key, password=password)
        self.requester = None

    def do001(self, irc, msg):
        """start a challenge attempt on connection to server"""
        self.prepChallenge()
        oper = self.registryValue("opername")
        irc.queueMsg(ircmsgs.IrcMsg(f"CHALLENGE {oper}"))

    def do740(self, irc, msg):
        """record ciphertext"""
        self.challenge.push(msg.args[1])

    def do741(self, irc, msg):
        """decrypt and issue retort to server"""
        retort = self.challenge.finalise()
        irc.queueMsg(ircmsgs.IrcMsg(f"CHALLENGE +{retort}"))

    def do491(self, irc, msg):
        """handle unknown oper error"""
        if self.requester:
            self.requester.reply("Error: No O:Lines for my host")
        else:
            self.log.info("Error: No O:Lines for my host")

    def do464(self, irc, msg):
        """handle bad password error"""
        if self.requester:
            self.requester.reply("Error: Password mismatch")
        else:
            self.log.info("Error: Password mismatch")

    def do381(self, irc, msg):
        """when we oper up successfully"""
        if self.requester:
            self.requester.replySuccess()
Class = ChallengeAuth

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
