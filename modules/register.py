# User Level Registration
# Banned Account Check
# VIP Mode Check
# Guest Mode
# Lurker Mode

# Odsum

import pinylib
from apis import tinychat


class Registration:

    def __init__(self, tinybot, spamcheck, conf):
        """
        Initialize the Spam class.

        :param tinybot: An instance of TinychatBot.
        :type tinybot: TinychatBot
        :param spamcheck: check if room is in lockdown
        :type spamcheck: True/False
        :param conf: The config file.
        :type conf: config
        """
        self.tinybot = tinybot
        self.spamcheck = spamcheck
        self.config = conf
        self.lockdown = False
        self.greet = None

    def user_register(self, _user):

        if not _user.account:
            _user.user_level = 7  # guest
            self.tinybot.console_write(pinylib.COLOR['cyan'],
                                       '[User] Guest %s:%d' % (_user.nick, _user.id))

            if not self.config.B_ALLOW_GUESTS:
                if _user.user_level == 7:
                    if self.spamcheck.lockdown:
                        self.tinybot.process_ban(_user.id)
                    else:
                        self.tinybot.send_ban_msg(_user.id)
                    if self.config.B_VERBOSE:
                        self.tinybot.handle_msg('%s was banned (No Guests allowed).' % _user.nick)
                        self.tinybot.console_write(pinylib.COLOR['red'],
                                                   '[Security] %s was banned on no guest mode' % _user.nick)
                    return False

            if _user.is_lurker and not self.config.B_ALLOW_LURKERS:
                if _user.user_level > 5:
                    if self.spamcheck.lockdown:
                        self.tinybot.process_ban(_user.id)
                    else:
                        self.tinybot.send_ban_msg(_user.id)
                    if self.config.B_VERBOSE:
                        self.tinybot.handle_msg('%s is a lurker, no captcha. No Lurker Mode' % _user.nick)
                    self.tinybot.console_write(pinylib.COLOR['red'],
                                               '[Security] %s was banned on no lurkers mode' % _user.nick)
                    return False

        else:

            buddyusr = self.tinybot.buddy_db.find_db_user(_user.account)
            tc_info = tinychat.user_info(_user.account)

            if tc_info is not None:
                _user.tinychat_id = tc_info['tinychat_id']
                _user.last_login = tc_info['last_active']
                self.greet = tc_info['biography']

            if _user.is_owner:
                _user.user_level = 2  # account owner
                self.tinybot.console_write(pinylib.COLOR['cyan'], '[User] Room Owner %s:%d:%s' %
                                           (_user.nick, _user.id, _user.account))
            elif _user.is_mod:
                _user.user_level = 3  # mod
                self.tinybot.console_write(pinylib.COLOR['cyan'], '[User] Moderator %s:%d:%s' %
                                           (_user.nick, _user.id, _user.account))

            if buddyusr:
                _level = buddyusr['level']

                if not _user.is_mod:
                    _user.user_level = _level

                if _level < 6:
                    if buddyusr['greet'] != '':
                        self.greet = buddyusr['greet']

                if _level == 4 and not _user.is_mod:
                    _user.user_level = _level  # chatmod

                if _level == 5 and not _user.is_mod:
                    _user.user_level = _level  # whitelist

                if _level == 2:  # overwrite mod to chatadmin
                    _user.user_level = _level

                self.tinybot.console_write(pinylib.COLOR['cyan'], '[User] Found, level(%s)  %s:%d:%s' % (
                    _user.user_level, _user.nick, _user.id, _user.account))

            if self.tinybot.buddy_db.find_db_account_bans(_user.account) and self.tinybot.is_client_mod:
                if self.spamcheck.lockdown:
                    self.tinybot.process_ban(_user.id)
                else:
                    self.tinybot.process_ban(_user.id)
                if self.config.B_VERBOSE:
                    self.tinybot.handle_msg('%s is an banned account.' % _user.account)
                    self.tinybot.console_write(pinylib.COLOR['red'],
                                               '[Security] Banned: Account %s' % _user.account)
                return False

            if _user.user_level is None:
                _user.user_level = 6  # account not whitelisted
                self.tinybot.console_write(pinylib.COLOR['cyan'],
                                           '[User] Not Whitelisted %s:%d:%s' % (_user.nick, _user.id, _user.account))

            if self.config.B_VIP and not buddyusr:
                if self.spamcheck.lockdown:
                    self.tinybot.process_ban(_user.id)
                else:
                    self.tinybot.send_ban_msg(_user.id)

                if self.config.B_VERBOSE:
                    self.tinybot.handle_msg(
                        '%s is banned account, only known accounts allowed in VIP Mode.' % _user.account)
                self.tinybot.console_write(pinylib.COLOR['red'],
                                           '[Security] %s was banned, VIP mode' % _user.nick)
                return False
        return True
