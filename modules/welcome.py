# User Greeting
# Odsum

import random
import time


class Welcome:

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

    def welcome(self, uid, greet):

        time.sleep(0.2)
        greetings = ["hi", "sup", "yo", "hey", "eh", ]

        prefix = self.config.B_PREFIX
        _user = self.tinybot.users.search(uid)

        if _user is None:
            return False

        if not self.config.B_ALLOW_GUESTS:
            return False

        if self.config.B_GREET:

            if _user.nick.startswith('guest-'):
                return False

            if self.greet is not None:
                if self.config.B_VERBOSE:
                    time.sleep(1.0)
                    self.tinybot.send_chat_msg('[%s] %s' % (_user.nick, greet))
            else:
                if _user.user_level < 4:
                    self.tinybot.send_private_msg(_user.id, 'You are Mod  - %shelp for cmds' % prefix)
                    time.sleep(1.0)
                    self.tinybot.send_private_msg(_user.id,
                                                  '\n %s %s' % (self.tinybot.boticon, self.tinybot.announcement()))
                    return False
                elif _user.user_level == 5:
                    self.tinybot.send_private_msg(_user.id,
                                                  '%s %s, wb - You have access to the bot here, %shelp for cmds' % (
                                                      random.choice(greetings), _user.nick, prefix))
                    time.sleep(1.0)
                    self.tinybot.send_private_msg(_user.id,
                                                  '\n %s %s' % (self.tinybot.boticon, self.tinybot.announcement()))
                    return False
                elif _user.user_level == 7:
                    if self.config.B_VERBOSE:
                        time.sleep(1.5)
                        self.tinybot.send_chat_msg(
                            '%s %s, welcome to %s' % (random.choice(greetings), _user.nick, self.tinybot.room_name))
                        return False
            return True
        return True
