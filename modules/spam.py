# Spam 2.3.5 Protection ting
# odsum(lucy) //shit hasn't been the same as it was before...
# 03.14.18

import time

import pinylib
from util import words


class Spam:

    def __init__(self, tinybot, conf):
        """
        Initialize the Spam class.

        :param tinybot: An instance of TinychatBot.
        :type tinybot: TinychatBot
        :param user: The User object to check.
        :type user: User
        :param conf: The config file.
        :type conf: config
        """
        self.tinybot = tinybot
        self.config = conf
        self.general = ["hey", "hi", "yes", "no", "yo", "sup", "ya", "hello", "cheers", "tokes"]
        self.msgs = {}
        self.spamlevel = 0

        self.joind_time = 0
        self.joind_count = 0

        self.autoban_time = 0
        self.autoban_count = 0
        self.silent = False
        self.ban_time = 0
        self.lockdown = False

    def lockdown_onjoin(self, _user, t):

        maxtime = 10  # Reset check in X seconds
        maxjoins = 5  # maxjoins in maxtime

        if self.joind_time == 0:
            self.joind_time = t

        if t - self.joind_time > maxtime:
            self.joind_count = 0
            self.joind_time = 0

        if t - self.joind_time < maxtime and self.joind_count > maxjoins:
            self.autoban_time = t
            self.do_lockdown(0)
            self.tinybot.console_write(
                self.tinybot.pinylib.COLOR['red'], '[Security] Lockdown started')
            return False

        self.joind_count += 1

        self.tinybot.console_write(pinylib.COLOR['cyan'], '[User] %s:%d joined the room. (%s)' % (
            _user.nick, _user.id, self.joind_count))

        return True

    def check_lockdown(self):
        if self.lockdown:
            while True:
                time.sleep(0.2)

                if self.autoban_time > 240:  # 4 minute lockdown
                    self.autoban_time = 0
                    self.lockdown = False

                    self.do_lockdown(1)

                    self.tinybot.console_write(pinylib.COLOR['red'], '[Security] Lockdown Mode Reset')

                    if self.config.B_VERBOSE:
                        self.tinybot.handle_msg('Lockdown Mode Rest')

    def do_lockdown(self, soft):
        if self.tinybot.is_client_owner:

            if self.lockdown:
                if not soft:
                    password = self.tinybot.pinylib.string_util.create_random_string(5, 8)
                    self.tinybot.privacy_.set_room_password(password)

                if not self.tinybot.privacy_.set_guest_mode():
                    self.account_mode = False
                    self.tinybot.privacy_.set_guest_mode()
                else:
                    self.account_mode = True

                self.lockdown = True

                if soft:
                    self.tinybot.handle_msg('\n %s Lockdown - no guests allowed.' % self.tinybot.boticon)
                else:
                    self.tinybot.handle_msg('\n %s Lockdown - tmp password is: %s' % (self.tinybot.boticon, password))

            else:

                password = None
                self.tinybot.privacy_.set_room_password(password)

                if not self.account_mode:
                    self.tinybot.privacy_.set_guest_mode()
                    self.account_mode = True

                self.lockdown = False

                self.tinybot.kick_pool[:] = []
                self.tinybot.ban_pool[:] = []

                time.sleep(2.0)
                self.tinybot.handle_msg(
                    '\n %s %s is open to the public again.' % (self.tinybot.boticon, self.tinybot.room_name))

        else:

            if self.lockdown:

                if not self.config.B_ALLOW_GUESTS:
                    self.tinybot.do_guests(1)

                if not self.config.B_USE_KICK_AS_AUTOBAN:
                    self.tinybot.do_kick_as_ban(1)

                if self.silent and not self.config.B_VERBOSE:
                    self.tinybot.do_verbose(1)
                    self.silent = False

                self.tinybot.kick_pool[:] = []
                self.tinybot.ban_pool[:] = []

                self.lockdown = False

                time.sleep(2.0)
                self.tinybot.handle_msg(
                    '\n %s %s is open to the public again.' % (self.tinybot.boticon, self.tinybot.room_name))
            else:

                if self.config.B_VERBOSE:
                    self.silent = True
                    self.tinybot.do_verbose(1)

                if self.config.B_ALLOW_GUESTS:
                    self.tinybot.do_guests(1)

                if self.config.B_USE_KICK_AS_AUTOBAN:
                    self.tinybot.do_kick_as_ban(1)

                self.lockdown = True
                time.sleep(2.0)
                self.tinybot.handle_msg('\n %s Lockdown - no guests allowed.' % self.tinybot.boticon)

    def check_msg(self, msg):

        spamlevel = self.spamlevel
        spammer = False
        ban = False
        kick = False
        msg = words.removenonascii(msg)
        chat_words = msg.split(' ')
        total = sum(char.isspace() or char == "0" for char in msg)
        chatr_user = self.tinybot.active_user.nick
        chatr_account = self.tinybot.active_user.account
        msg_time = int(time.time())
        totalcopies = 0
        # reason = ''

        # each word reviewed and scored

        for word in chat_words:
            if word in self.general:
                return
            else:
                if self.config.B_SPAMP:
                    if not words.isword(word):
                        spamlevel += 0.25  # for everyword that isn't english word

                    if not words.isword(chatr_user):
                        spamlevel += 0.25  # wack nick

                    if word.isupper():
                        spamlevel += 0.125  # Uppercase word

                lword = word.lower()
                if self.tinybot.buddy_db.find_db_word_bans(lword):
                    ban = True
                    spammer = True
                    reason = 'Word ban: ' + lword
                    # self.tinybot.console_write(pinylib.COLOR['bright_magenta'], '[Spam] Banned word.')

        if self.config.B_SPAMP:
            if total > 140:  # if message is larger than 100 characters
                spamlevel += 0.25

            # knownnick = self.buddy_db.find_db_ticket(chatr_user)
            #
            # # known spammer from our database.
            #
            # if knownnick:
            #     spamlevel += 0.25
            #     spammer = True
            #
            #     if knownnick['account']:
            #         spamlevel += 0.25

            for m in self.msgs:

                if msg == m and m not in self.general:
                    totalcopies += 1
                    oldmsg = self.msgs[msg]
                    msgdiff = msg_time - oldmsg['ts']

                    if msgdiff < 4:
                        spamlevel += 0.25

                    if totalcopies > 0:

                        spamlevel += 0.25

                        if oldmsg['nick'] == chatr_user:
                            spamlevel += 0.5
                            spammer = True
                            kick = True
                        #   reason = 'Spam repeat.'

            mpkg = {'score': spamlevel, 'account': chatr_account, 'nick': chatr_user, 'ts': msg_time}

            # if spamlevel >= 2:
            #     self.buddy_db.add_ticket(chatr_account, spamlevel, chatr_user, reason)
            #     self.console_write(pinylib.COLOR['bright_magenta'], '[Spam] Ticket submitted: Nick: %s Score: %s' %
            #                        (chatr_user, spamlevel))

            self.msgs.update({'%s' % msg: mpkg})

            if len(self.msgs) > 4:  # store last 4 messages
                self.msgs.clear()

            if self.tinybot.active_user.user_level > 5:
                if spamlevel > 3:
                    ban = True
        if ban:
            time.sleep(0.7)
            if self.tinybot.active_user.user_level > 5:
                if self.tinybot.active_user.user_level == 6:
                    if spammer:
                        self.tinybot.buddy_db.add_bad_account(self.tinybot.active_user.account)
                        if self.tinybot.lockdown:
                            self.tinybot.process_ban(self.tinybot.active_user.id)
                        else:
                            self.tinybot.send_ban_msg(self.tinybot.active_user.id)
                elif len(self.tinybot.active_user.account) is 0:
                    if spammer:
                        if self.tinybot.lockdown:
                            self.tinybot.process_ban(self.tinybot.active_user.id)
                        else:
                            self.tinybot.end_ban_msg(self.tinybot.active_user.id)
                if self.config.B_VERBOSE:
                    self.tinybot.handle_msg(
                        '\n %s %s was banned for spamming.' % (self.tinybot.boticon, self.tinybot.active_user.nick))

        if kick:
            if self.tinybot.active_user.user_level > 3:
                if self.tinybot.lockdown:
                    self.tinybot.process_kick(self.tinybot.active_user.id)
                else:
                    self.tinybot.send_kick_msg(self.tinybot.active_user.id)

                if self.config.B_VERBOSE:
                    self.tinybot.handle_msg(
                        '\n %s %s was kicked for spamming.' % (self.tinybot.boticon, self.tinybot.active_user.nick))

        return spamlevel
