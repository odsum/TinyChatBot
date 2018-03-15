# Tokecountdown from Tunebot
# Cheers/Tokes 1.1
# 03.01.18
# odsum

import threading
import time


class Tokes:

    def __init__(self, tinybot, conf):

        self.tinybot = tinybot
        self.config = conf

        self.announce = 0
        self.announceCheck = 0

        self.tokers = []
        self.toke_start = 0
        self.toke_end = 0
        self.toke_mode = False
        self.toker = None

    def tokesession(self, cmd_args):

        prefix = self.config.B_PREFIX

        if cmd_args == "!!":
            if self.tinybot.active_user.user_level < 5:
                self.resettokes()
                self.tinybot.send_chat_msg('Cheers has been reset.')
            return

        if self.toke_mode:
            mins = self.until(self.toke_start, self.toke_end)

            if self.tinybot.active_user.nick in self.tokers:
                self.tinybot.send_chat_msg(
                    'You have already joined, %s %s to cheers...' % (str(mins), self.pluralize('minute', mins)))
            else:
                self.newtoker()
            return
        else:
            if self.tinybot.active_user.user_level < 6:
                try:
                    end = int(cmd_args)
                    if not 1 <= end <= 10:
                        raise Exception()
                except:
                    self.tinybot.send_chat_msg('Give me a time in minutes, between 1 and 10, until cheers...')
                    return

                announce = 1
                self.tokers.append(self.tinybot.active_user.nick)
                self.startTokes(end, announce)
                mins = self.until(self.toke_start, self.toke_end)
                self.tinybot.send_chat_msg(
                    '\n %s %s %s until the cheers.. . type %scheers in the box to still join in!' % (
                        self.tinybot.cheersicon, str(mins), self.pluralize('minute', mins), prefix))

    def newtoker(self):
        self.tokers.append(self.tinybot.active_user.nick)
        mins = self.until(self.toke_start, self.toke_end)
        time.sleep(0.9)
        self.tinybot.send_chat_msg('\n %s %s is down... %s %s left for cheers' % (
            self.tinybot.cheersicon, self.tinybot.active_user.nick, str(mins), self.pluralize('minute', mins)))
        return

    def startTokes(self, end, announce=0):
        self.toke_mode = True
        t = int(time.time())
        self.announce = int(announce) * 60
        self.announceCheck = t + self.announce
        self.toke_start = t
        self.toke_end = int(end) * 60
        thread = threading.Thread(target=self.toke_count, args=())
        thread.daemon = True
        thread.start()

    def resettokes(self):
        self.toke_mode = False
        self.announce = 0
        self.announceCheck = 0
        self.tokers[:] = []
        self.toke_start = 0
        self.toker = None
        return

    def toke_count(self):
        prefix = self.config.B_PREFIX
        while True:
            time.sleep(0.3)
            t = time.time()

            if not self.toke_mode:
                time.sleep(5)
                break

            if self.toker is None:
                self.toker = str(self.tokers[0])

            if t > self.toke_start + self.toke_end:
                start = int((t - self.toke_start) / 60)

                if len(self.tokers) > 1:
                    if len(self.tokers) == 2:
                        joined = self.tokers[1]
                    else:
                        joined = ''
                        j = 0
                        for name in self.tokers[1:]:
                            if j == len(self.tokers) - 2:
                                joined += 'and ' + name
                            else:
                                joined += name + ', '
                            j += 1

                    thiscodesucks = 'is'  # odsum// ya kids rap that's cool
                    if len(self.tokers) > 2:
                        thiscodesucks = 'are'

                    self.tinybot.send_chat_msg(
                        '\n %s %s called a cheers %s %s ago and %s %s taking part.. . *! CHEERS !*'
                        % (self.tinybot.cheersicon, self.toker, start, self.pluralize('minute', start), joined,
                           thiscodesucks))
                else:
                    self.tinybot.send_chat_msg(
                        '\n %s %s, ya called cheers %s %s ago and nobody joined in.. . oh well *CHEERS*'
                        % (self.tinybot.cheersicon, self.toker, start, self.pluralize('minute', start)))
                self.resettokes()
                break

            if t > self.announceCheck:
                self.announceCheck = t + self.announce

                start = int((t - self.toke_start) / 60)
                self.tinybot.send_chat_msg('\n %s %s called a cheers %s %s ago, %scheers to join in now!' % (
                    self.tinybot.cheersicon, self.toker, str(start), self.pluralize("minute", start), prefix))

    @staticmethod
    def pluralize(text, n, pluralForm=None):
        if n != 1:
            if pluralForm is None:
                text += 's'
        return text

    @staticmethod
    def until(start, end):
        t = int(time.time())
        d = int(round(float(start + end - t) / 60))
        if d == 0:
            d = 1
        return d
