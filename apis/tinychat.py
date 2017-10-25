import time
import util.web


def rtc_version(room):
    """
    Parse the current tinychat RTC version.
    
    :param room: This could be a static room name, since we just need the html of any room.
    :type room: str
    :return: The current tinychat rtc version, or None on parse failure.
    :rtype: str | None
    """
    _url = 'https://tinychat.com/room/{0}'.format(room)
    response = util.web.http_get(url=_url)

    if response['content'] is not None:
        pattern = '<link rel="manifest" href="/webrtc/'
        return response['content'].split(pattern)[1].split('/manifest.json">')[0]


def get_connect_token(room):
    """ 
    Get the connect token needed for connecting to the WebRTC application.

    :param room: The room to get the token for.
    :type room: str
    :return: The connect token, or None on failure to fetch token.
    :rtype: str | None
    """
    _url = 'https://tinychat.com/api/v1.0/room/token/{0}'.format(room)

    response = util.web.http_get(url=_url, json=True)
    if response['json'] is not None:
        return response['json']['result']


def user_info(tc_account):
    """ 
    Finds info for a given tinychat account name.

    :param tc_account: str the account name.
    :return: dict {'username', 'tinychat_id', 'last_active', 'name', 'location', 'biography'} or None on error.
    """
    url = 'https://tinychat.com/api/tcinfo?username=%s' % tc_account
    response = util.web.http_get(url=url, json=True)
    if response['json'] is not None:
        if 'error' not in response['json']:
            username = response['json']['username']
            user_id = response['json']['id']
            last_active = time.ctime(int(response['json']['last_active']))
            name = response['json']['name']
            location = response['json']['location']
            biography = response['json']['biography']

            return {
                'username': username,
                'tinychat_id': user_id,
                'last_active': last_active,
                'name': name,
                'location': location,
                'biography': biography
            }
        else:
            return None


def spy_info(room):
    """ 
    Finds info for a given room name.

    The info shows how many mods, broadcasters and total users(list)

    :param room: str the room name to get spy info for.
    :return: dict{'mod_count', 'broadcaster_count', 'total_count', list('users')} or {'error'}.
    """
    url = 'https://api.tinychat.com/%s.json' % room
    response = util.web.http_get(url, json=True)
    if response['json'] is not None:
        if 'error' not in response['json']:
            mod_count = str(response['json']['mod_count'])
            broadcaster_count = str(response['json']['broadcaster_count'])
            total_count = response['json']['total_count']
            if total_count > 0:
                users = response['json']['names']
                return {
                    'mod_count': mod_count,
                    'broadcaster_count': broadcaster_count,
                    'total_count': total_count,
                    'users': users
                }
        else:
            return {'error': response['json']['error']}
