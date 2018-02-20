# BuddyBot

import logging
import threading
import Queue
import sys
import time
import tinybot


log = logging.getLogger(__name__)


def buddy_start(in_queue, out_queue):

    while True:

        item = in_queue.get()
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
                bot.console_write(tinybot.pinylib.COLOR['bright_green'], '[Bot] Account: %s' % bot.account)
            if not do_login:
                bot.account = None
                bot.password = None

        threading.Thread(target=bot.connect).start()

        while not bot.is_connected:
            time.sleep(2)

        while bot.is_connected:
            chat_msg = raw_input()
            bot.send_chat_msg(chat_msg)

        result = item
        out_queue.put(result)
        in_queue.task_done()


if __name__ == '__main__':

    if tinybot.pinylib.CONFIG.DEBUG_TO_FILE:
        formater = '%(asctime)s : %(levelname)s : %(filename)s : %(lineno)d : %(funcName)s() : %(name)s : %(message)s'
        logging.basicConfig(filename=tinybot.pinylib.CONFIG.DEBUG_FILE_NAME,
                            level=tinybot.pinylib.CONFIG.DEBUG_LEVEL,
                            format=formater)
        log.info('Starting buddybot: %s, pinylib version: %s' % (tinybot.__version__,
                                                                       tinybot.pinylib.__version__))
    else:
        log.addHandler(logging.NullHandler())

    work = Queue.Queue()
    results = Queue.Queue()
    total = 1

    for i in xrange(4):
        t = threading.Thread(target=buddy_start, args=(work, results))
        t.daemon = True
        t.start()

    # produce data
    for i in xrange(total):
        work.put(i)

    work.join()

    # get the results
    for i in xrange(total):
        print results.get()

    sys.exit()