import logging
import threading
import time
import tinybot

log = logging.getLogger(__name__)


def main():
    room_name = tinybot.pinylib.CONFIG.ROOM
    if tinybot.pinylib.CONFIG.ACCOUNT and tinybot.pinylib.CONFIG.PASSWORD:
        bot = tinybot.TinychatBot(room=room_name, account=tinybot.pinylib.CONFIG.ACCOUNT,
                                  password=tinybot.pinylib.CONFIG.PASSWORD)
    else:
        bot = tinybot.TinychatBot(room=room_name)

    bot.nickname = tinybot.pinylib.CONFIG.BOTNICK

    do_login = 1
    if do_login:
        if not bot.account:
            bot.account = raw_input('Account: ').strip()
        if not bot.password:
            bot.password = raw_input('Password: ')

        is_logged_in = bot.login()
        while not is_logged_in:
            bot.account = raw_input('Account: ').strip()
            bot.password = raw_input('Password: ')
            if bot.account == '/' or bot.password == '/':
                main()
                break
            elif bot.account == '//' or bot.password == '//':
                do_login = False
                break
            else:
                is_logged_in = bot.login()
        if is_logged_in:
            bot.console_write(tinybot.pinylib.COLOR['bright_green'], 'Logged in as: %s' % bot.account)
        if not do_login:
            bot.account = None
            bot.password = None

    threading.Thread(target=bot.connect).start()

    while not bot.is_connected:
        time.sleep(2)

    while bot.is_connected:
        chat_msg = raw_input()
        if chat_msg.startswith('/'):
            msg_parts = chat_msg.split(' ')
            cmd = msg_parts[0].lower().strip()
            if cmd == '/q':
                bot.disconnect()
            elif cmd == '/a':
                if len(bot.users.signed_in) == 0:
                    print ('No signed in users in the room.')
                else:
                    for user in bot.users.signed_in:
                        print ('%s:%s' % (user.nick, user.account))
            elif cmd == '/u':
                for user in bot.users.all:
                    print ('%s: %s' % (bot.users.all[user].nick, bot.users.all[user].user_level))
            elif cmd == '/m':
                if len(bot.users.mods) == 0:
                    print ('No moderators in the room.')
                else:
                    for mod in bot.users.mods:
                        print (mod.nick)
            elif cmd == '/n':
                if len(bot.users.norms) == 0:
                    print ('No normal users in the room.')
                else:
                    for norm in bot.users.norms:
                        print (norm.nick)
            elif cmd == '/l':
                if len(bot.users.lurkers) == 0:
                    print ('No lurkers in the room.')
                else:
                    for lurker in bot.users.lurkers:
                        print (lurker.nick)

            # FOR DEBUGGING METHODS!
            elif cmd == '/t':
                pass

        else:
            bot.send_chat_msg(chat_msg)

if __name__ == '__main__':
    if tinybot.pinylib.CONFIG.DEBUG_TO_FILE:
        formater = '%(asctime)s : %(levelname)s : %(filename)s : %(lineno)d : %(funcName)s() : %(name)s : %(message)s'
        logging.basicConfig(filename=tinybot.pinylib.CONFIG.DEBUG_FILE_NAME,
                            level=tinybot.pinylib.CONFIG.DEBUG_LEVEL,
                            format=formater)
        log.info('Starting tinybot: %s, pinylib version: %s' % (tinybot.__version__,
                                                                       tinybot.pinylib.__version__))
    else:
        log.addHandler(logging.NullHandler())
    main()
