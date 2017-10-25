""" Contains functions to fetch API information from last.fm API."""
import logging

import youtube
import util.web

CHART_URL = 'http://lastfm-ajax-vip1.phx1.cbsig.net/kerve/charts?nr={0}&type=track&format=json'

TAG_SEARCH_URL = 'http://lastfm-ajax-vip1.phx1.cbsig.net/kerve/charts?nr={0}&type=track&f=tag:{1}&format=json'

LISTENING_NOW_URL = 'http://lastfm-ajax-vip1.phx1.cbsig.net/kerve/listeningnow?limit={0}&format=json'


log = logging.getLogger(__name__)


def chart(chart_items=5):
    """
    Finds the currently most played tunes on last.fm and turns them in to a youtube list of tracks.
    :param chart_items: int the amount of tracks we want.
    :return: list[ dict{'type=youtube', 'video_id', 'int(video_time)', 'video_title'} ] or None on error.
    """
    url = CHART_URL.format(chart_items)
    lastfm = util.web.http_get(url=url, json=True)

    log.debug('lastfm response %s' % lastfm)
    if lastfm['json'] is not None:
        if 'results' in lastfm['json']:
            if 'track' in lastfm['json']['results']:
                if len(lastfm['json']['results']['track']) is not 0:
                    # make this list unique
                    yt_tracks = []
                    for track in lastfm['json']['results']['track']:
                        search_str = '%s - %s' % (track['artist'], track['name'])
                        yt = youtube.search(search_str)
                        log.info(yt)
                        if yt is not None:
                            yt_tracks.append(yt)
                    return yt_tracks
                return None


def tag_search(search_str, by_id=True, max_tunes=40):
    """
    Search last.fm for tunes matching the search term and turns them in to a youtube list of tracks.
    :param search_str: str the search term to search for.
    :param by_id: bool if set to True, only tunes that have a youtube id will be added(recommended)
    :param max_tunes: int the max amount of tunes to return.
    :return: list[ dict{'type=youtube', 'video_id', 'int(video_time)', 'video_title'} ] or None on error.
    """
    url = TAG_SEARCH_URL.format(max_tunes, util.web.quote(search_str))
    lastfm = util.web.http_get(url=url, json=True)

    log.debug('lastfm response %s' % lastfm)
    if lastfm['json'] is not None:
        if 'track' in lastfm['json']['results']:
            if len(lastfm['json']['results']['track']) is not 0:
                # make this list unique
                yt_tracks = []
                for track in lastfm['json']['results']['track']:
                    search_str = '%s - %s' % (track['artist'], track['name'])
                    if 'playlink' in track:
                        if 'data-youtube-id' in track['playlink']:
                            youtube_id = track['playlink']['data-youtube-id']
                            yt = youtube.video_details(youtube_id)
                            log.debug(yt)
                            if yt is not None:
                                yt_tracks.append(yt)
                        else:
                            if not by_id:
                                yt = youtube.search(search_str)
                                log.debug('search by search string: %s result: %s' % (search_str, yt))
                                if yt is not None:
                                    yt_tracks.append(yt)
                    else:
                        if not by_id:
                            yt = youtube.search(search_str)
                            log.debug('search by search string: %s result: %s' % (search_str, yt))
                            if yt is not None:
                                yt_tracks.append(yt)
                return yt_tracks
            return None


def listening_now(max_tunes, by_id=True):
    """
    Gets a list of tunes other people using last.fm are listening to, and turns them in to a youtube list of tracks.
    :param max_tunes: int the amount of tracks we want.
    :param by_id: bool if set to True, only tunes that have a youtube id will be added(recommended)
    :return: list[ dict{'type=youtube', 'video_id', 'int(video_time)', 'video_title'} ] or None on error.
    """
    url = LISTENING_NOW_URL.format(max_tunes)
    lastfm = util.web.http_get(url=url, json=True)

    log.debug('lastfm response %s' % lastfm)
    if lastfm['json'] is not None:
        if len(lastfm['json']['Users']) is not 0:
            # make this list unique
            yt_tracks = []
            for user in lastfm['json']['Users']:
                if 'playlink' in user:
                    if 'data-youtube-id' in user['playlink']:
                        youtube_id = user['playlink']['data-youtube-id']
                        yt = youtube.video_details(youtube_id)
                        log.debug(yt)
                        if yt is not None:
                            yt_tracks.append(yt)
                else:
                    if 'Track' in user:
                        search_str = '%s - %s' % (user['Track']['Artist'], user['Track']['Name'])
                        if not by_id:
                            yt = youtube.search(search_str)
                            log.debug('search by search string: %s result: %s' % (search_str, yt))
                            if yt is not None:
                                yt_tracks.append(yt)
            return yt_tracks
        return None
