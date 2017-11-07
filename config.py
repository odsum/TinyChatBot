# Tinychat account.
ACCOUNT = ''
# Password for account
PASSWORD = ''
BOTNICK = ''
ROOM = ''
# Fallback rtc version.
FALLBACK_RTC_VERSION = '2.0.22-4'
# Log chat messages and events.
CHAT_LOGGING = True
# Show additional info/errors in console.
DEBUG_MODE = False
# Log debug info to file.
DEBUG_TO_FILE = False
# Logging level for the debug file.
DEBUG_LEVEL = 30
# Use colors for the console.
CONSOLE_COLORS = False
# Time format.
USE_24HOUR = True
# The name of pinylib's debug log file.
DEBUG_FILE_NAME = 'pinylib_debug.log'
# The path to the config folder.
CONFIG_PATH = 'rooms/'
B_PREFIX = '!'

# Is there a hub bot?
B_BOT_HUB = False
B_BOT_HUB_HOST = ''
B_BOT_HUB_PORT = 1337
B_HUB_KEY = '12345678'

# If you're running two bots, set one to Master.  Splits the functionality
B_IS_MASTER = True

# The maximum amount of match bans.
B_MAX_MATCH_BANS = 1
# Public commands enabled.
B_PUBLIC_CMD = True
# Greet user when joining.
B_GREET = True
# Allow newuser to join the room.
B_ALLOW_NEWUSERS = True
# Allow broadcasting.
B_ALLOW_BROADCASTS = True
# Allow guests to enter the room.
B_ALLOW_GUESTS = True
# Allow lurkers to enter the room.
B_ALLOW_LURKERS = True
# Allow guest nicks.
B_ALLOW_GUESTS_NICKS = True
B_USE_KICK_AS_AUTOBAN = False
# Forgive auto bans.
B_FORGIVE_AUTO_BANS = False
# The file name of nick bans.
B_NICK_BANS_FILE_NAME = 'nick_bans.txt'
# A list of all the nick bans.
B_NICK_BANS = []
# The file name of account bans.
B_ACCOUNT_BANS_FILE_NAME = 'account_bans.txt'
# The file name of account bans.
B_ACCOUNT_VERIFIED_FILE_NAME = 'account_verified.txt'
B_ACCOUNT_VERIFIED = []

B_ACCOUNT_CHATMOD_FILE_NAME = 'account_chatmod.txt'
B_ACCOUNT_CHATMOD = []

B_ACCOUNT_CHATADMIN_FILE_NAME = 'account_chatadmin.txt'
B_ACCOUNT_CHATADMIN = []
# A list of account bans.
B_ACCOUNT_BANS = []
# The file name of string(words) bans.
B_STRING_BANS_FILE_NAME = 'string_bans.txt'
# A list of string bans.
B_STRING_BANS = []
