# Voteban 1.0
# odsum

import threading
import time


class Voting:

    def __init__(self, tinybot, conf):

        self.tinybot = tinybot
        self.config = conf

        self.announce = 0
        self.announceCheck = 0

        self.voters = []
        self.friends = []

        self.vote_start = 0
        self.vote_end = 0

        self.vote_mode = False
        self.voteban = None
        self.votetype = None

    def votesession(self, cmd_args):

        prefix = self.config.B_PREFIX
        if cmd_args == "!!":
            if self.tinybot.active_user.user_level < 5:
                self.resetvotes()
                self.tinybot.send_chat_msg('Voting has been reset.')
            return

        if self.vote_mode:

            if cmd_args.lower() == "no":
                if self.tinybot.active_user.nick in self.voters:
                    self.voters.remove(self.tinybot.active_user.nick)

                if self.tinybot.active_user.nick in self.friends:
                    self.tinybot.send_chat_msg('You have already voted!')
                    return
                else:
                    self.friends.append(self.tinybot.active_user.nick)
                    return

            if self.tinybot.active_user.nick in self.voters:
                self.tinybot.send_chat_msg('You have already voted!')

                if self.tinybot.active_user.nick in self.friends:
                    self.friends.remove(self.tinybot.active_user.nick)
                self.voters.append(self.tinybot.active_user.nick)
                return
        else:
            if self.tinybot.active_user.user_level < 5:

                parts = cmd_args.split(' ')

                try:
                    action = parts[0].lower().strip()
                except:
                    self.tinybot.send_chat_msg('Please define action: %svote cam/ban nick' % prefix)
                    return

                try:
                    userwho = parts[1].lower().strip()
                except:
                    self.tinybot.send_chat_msg('Nick is missing:  %svote cam/ban nick' % prefix)
                    return

                try:
                    _user = self.tinybot.users.search_by_nick(userwho)
                    if _user is None:
                        raise Exception()
                except:
                    self.tinybot.send_chat_msg('User not online:  %svote cam/ban nick' % prefix)
                    return

                lang = 'Ban'
                kcmd = 0

                if action == "cam":
                    broadcasters = self.tinybot.users.broadcaster
                    lang = 'Cam down'
                    kcmd = 1
                    if _user not in broadcasters:
                        self.tinybot.send_chat_msg('hmmm, %s is not on cam.' % _user.nick)
                        return

                if action == "ban":
                    kcmd = 1

                if action == "kick":
                    lang = 'Kick'
                    kcmd = 1

                if kcmd and not self.vote_mode:
                    _user = self.tinybot.users.search_by_nick(userwho)
                    self.startvoting(_user.id, action)
                    mins = self.until(self.vote_start, self.vote_end)
                    self.tinybot.send_chat_msg(
                        '\n Vote %s: %s %s for you to %s %s from this room.  PM me or type in the chat %svote to cast your voice.' % (
                            lang, str(mins), self.pluralize('minute', mins), lang, _user.nick, prefix))

    def startvoting(self, voteban, votetype):
        self.vote_mode = True
        t = int(time.time())
        self.votetype = votetype
        self.announce = int(1) * 60  # announce every minute
        self.announceCheck = t + self.announce
        self.vote_start = t
        self.voteban = voteban
        self.vote_end = int(2) * 60  # 2 minutes for ban

        thread = threading.Thread(target=self.vote_count, args=())
        thread.daemon = True
        thread.start()

    def resetvotes(self):
        self.vote_mode = False
        self.announce = 0
        self.announceCheck = 0
        self.voters[:] = []
        self.friends[:] = []
        self.vote_start = 0
        self.voteban = None
        return

    def vote_count(self):
        # prefix = pinylib.CONFIG.B_PREFIX

        while True:
            time.sleep(0.3)
            t = time.time()

            if not self.vote_mode:
                time.sleep(5)
                break

            _user = self.tinybot.users.search(self.voteban)

            if _user is None:
                self.tinybot.send_chat_msg('awww.. %s left. ' % _user.nick)
                self.resetvotes()
                break

            # if t > self.vote_start + self.vote_end:
            #     votes_required = 30
            #     totalusers = len(self.users.all)
            #     voterz = len(self.voters)
            #     friends = len(self.friends)
            #     total_votes = float(voterz) / float(totalusers) * 100
            #     total_friends = float(friends) / float(totalusers) * 100
            #     total_voters = float(total_friends) + float(total_votes)
            #
            # #   someone fix real democracy above - vars bring back 0 i don't really care. - 30% is real!
            #
            #     if total_votes > votes_required:
            #         if total_friends > total_votes:
            #             self.send_chat_msg('\n %s was saved by the power of democracy this time! %s of users voted to keep %s here.' % (self.voteban, str(total_friends), self.voteban))
            #             self.resetvotes()
            #             break

            voterz = len(self.voters)

            if t > self.vote_start + self.vote_end:
                self.tinybot.send_chat_msg('%s ya lucky, no one cared.' % _user.nick)
                self.resetvotes()
                break

            if voterz > 4:
                if _user is None:
                    self.tinybot.send_chat_msg('%s is sneaky.. .' % _user.nick)
                else:
                    if self.votetype == "cam":
                        if _user.is_broadcasting:
                            self.tinybot.send_close_user_msg(_user.id)
                            _user.is_broadcasting = False
                        else:
                            self.tinybot.send_chat_msg('i dont see %s on cam' % _user.nick)

                    elif self.votetype == "ban":
                        self.tinybot.send_ban_msg(_user.id)

                    elif self.votetype == "kick":
                        self.tinybot.send_kick_msg(_user.id)

                    self.tinybot.send_chat_msg('%s was outcasted!' % _user.nick)
                    # self.send_chat_msg('\n %s was voted to be banned, %s percent voted to ban, a total of %s of '
                    #                   'users took part in this vote. The people have decided to ban you. '
                    #                   % (_user.nick, total_votes, str(total_voters)))
                # else:
                #     self.send_chat_msg('%s, no hard feelings... friends still?'% (_user.nick))
                self.resetvotes()
                break

            # if t > self.announceCheck:
            #     self.announceCheck = t + self.announce
            #
            #     mins = self.until(self.vote_start, self.vote_end)
            #     self.send_chat_msg('\n Voting to ban %s - To cast your voice, type %svote for yes or %svote No for against.  %s %s left for voting. ' % (_user.nick, prefix, prefix, str(mins), self.pluralize("minute", mins)))

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
