# Modified to support multiple rooms 02.22.18
# odsum - 'it ain't safe, it ain't safe'

import Queue
import logging
import threading

import tinybot

log = logging.getLogger(__name__)


def buddystart(qbot, croom):
    while True:

        qbot.get()
        if tinybot.pinylib.CONFIG.ACCOUNT and tinybot.pinylib.CONFIG.PASSWORD:
            bot = tinybot.TinychatBot(room=croom, account=tinybot.pinylib.CONFIG.ACCOUNT,
                                      password=tinybot.pinylib.CONFIG.PASSWORD)
        bot.login()
        bot.console_write(tinybot.pinylib.COLOR['bright_green'], 'Logged in as: %s' % bot.account)

        bot.nickname = tinybot.pinylib.CONFIG.BOTNICK
        bot.connect()


if __name__ == '__main__':
    if tinybot.pinylib.CONFIG.DEBUG_TO_FILE:
        formater = '%(asctime)s : %(levelname)s : %(filename)s : %(lineno)d : %(funcName)s() : %(name)s : %(message)s'
        logging.basicConfig(filename=tinybot.pinylib.CONFIG.DEBUG_FILE_NAME,
                            level=tinybot.pinylib.CONFIG.DEBUG_LEVEL,
                            format=formater)
        log.info('Starting BuddyBot: %s, pinylib version: %s' % (tinybot.__version__,
                                                                 tinybot.pinylib.__version__))
    else:
        log.addHandler(logging.NullHandler())

    qbot = Queue.Queue()
    total = 0

    for croom in tinybot.pinylib.CONFIG.ROOMS:
        t = threading.Thread(target=buddystart, args=(qbot, croom))
        t.daemon = True
        t.start()
        total += 1

    print ('Buddybot %s - odsum' % tinybot.__version__)
    print ('Rooms Found: %s ' % total)
    print ('')

    for i in xrange(total):
        qbot.put(total)
    qbot.join()
