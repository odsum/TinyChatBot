""" Functions to do different string operations with. """
import random
from web import quote, unquote


def quote_str(input_str, safe=':,./&+?#=@'):
    """
    Quote a string.
    :param input_str: str input string.
    :param safe: str characters not to be quoted.
    :return: str quoted string
    """
    return quote(input_str, safe=safe)


def unquote_str(input_str):
    """
    Unquote a string.
    :param input_str: str input string to unquote.
    :return: str unquoted string
    """
    return unquote(input_str)


def chunk_string(input_str, length):
    """
    Splits a string in to smaller chunks.
    NOTE: http://stackoverflow.com/questions/18854620/
    :param input_str: str the input string to chunk.
    :param length: int the length of each chunk.
    :return: list of input str chunks.
    """
    return list((input_str[0 + i:length + i] for i in range(0, len(input_str), length)))


def create_random_string(min_length, max_length, upper=False):
    """
    Creates a random string of letters and numbers.
    :param min_length: int the minimum length of the string
    :param max_length: int the maximum length of the string
    :param upper: bool do we need upper letters
    :return: random str of letters and numbers
    """
    randlength = random.randint(min_length, max_length)
    junk = 'abcdefghijklmnopqrstuvwxyz0123456789'
    if upper:
        junk += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join((random.choice(junk) for _ in xrange(randlength)))


def convert_to_seconds(duration):
    """
    Converts a ISO 8601 unicode duration str to seconds.
    :param duration: The ISO 8601 unicode duration str
    :return:  int seconds
    """
    duration_string = duration.replace('PT', '').upper()
    seconds = 0
    number_string = ''

    for char in duration_string:
        if char.isnumeric():
            number_string += char
        try:
            if char == 'H':
                seconds += (int(number_string) * 60) * 60
                number_string = ''
            if char == 'M':
                seconds += int(number_string) * 60
                number_string = ''
            if char == 'S':
                seconds += int(number_string)
        except ValueError:
            return 0
    return seconds
