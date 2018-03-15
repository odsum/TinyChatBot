# Spam 2.3.5 Protection ting
# odsum(lucy) //shit hasn't been the same as it was before...
# 03.14.18

import time

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
