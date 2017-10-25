# -*- coding: utf-8 -*-
""" Contains functions to fetch info from youtube's API (googleapis.com/youtube/v3/) """
import logging

import util.web
import util.string_util


ALLOWED_COUNTRIES = ['DK', 'PL', 'UK']

API_KEY = 'AIzaSyCPQe4gGZuyVQ78zdqf9O5iEyfVLPaRwZg'

SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search?' \
             'type=video&key={0}&maxResults=50&q={1}&part=snippet'

PLAYLIST_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search?' \
                      'type=playlist&key={0}&maxResults=50&q={1}&part=snippet'

PLAYLIST_ITEMS_URL = 'https://www.googleapis.com/youtube/v3/playlistItems?' \
                     'key={0}&playlistId={1}&maxResults=50&part=snippet,id'

VIDEO_DETAILS_URL = 'https://www.googleapis.com/youtube/v3/videos?' \
                    'id={1}&key={0}&part=contentDetails,snippet'


log = logging.getLogger(__name__)


def search(search_term):
    """
    Searches the youtube API for a youtube video matching the search term.

    A json response of ~50 possible items matching the search term will be presented.
    Each video_id will then be checked by video_details() until a candidate has been found
    and the resulting dict can be returned.

    :param search_term: The search term str to search for.
    :return: dict{'type=youtube', 'video_id', 'int(video_time)', 'video_title'} or None on error.
    """
    if search_term:
        if 'list' in search_term:
            search_term = search_term.split('?list')[0]

        url = SEARCH_URL.format(API_KEY, util.web.quote(search_term.encode('ascii', 'ignore')))
        response = util.web.http_get(url=url, json=True, referer='http://tinychat.com')

        if response['json'] is not None:
            try:
                if 'items' in response['json']:
                    for item in response['json']['items']:
                        video_id = item['id']['videoId']
                        details = video_details(video_id)
                        if details is not None:
                            return {
                                'type': 'youTube',
                                'video_id': video_id,
                                'video_time': details['video_time'],
                                'video_title': details['video_title'],
                                'image': details['image']
                            }
            except KeyError as ke:
                log.error(ke, exc_info=True)
                return None


def search_list(search_term, results=10):
    """
    Searches the API of youtube for videos matching the search term.

    Instead of returning only one video matching the search term, we return a list of candidates.

    :param search_term: The search term str to search for.
    :param results: int determines how many results we would like on our list
    :return: list[dict{'type=youtube', 'video_id', 'int(video_time)', 'video_title'}] or None on error.
    """
    if search_term:
        url = SEARCH_URL.format(API_KEY, util.web.quote(search_term.encode('ascii', 'ignore')))
        response = util.web.http_get(url=url, json=True, referer='http://tinychat.com')

        if response['json'] is not None:
            media_list = []
            try:
                if 'items' in response['json']:
                    for i, item in enumerate(response['json']['items']):
                        if i == results:
                            return media_list
                        else:
                            video_id = item['id']['videoId']
                            details = video_details(video_id)
                            if details is not None:
                                media_info = {
                                    'type': 'youTube',
                                    'video_id': video_id,
                                    'video_time': details['video_time'],
                                    'video_title': details['video_title'],
                                    'image': details['image']
                                }
                                log.debug('Youtube item %s %s' % (i, media_info))
                                media_list.append(media_info)
            except KeyError as ke:
                log.error(ke, exc_info=True)
                return None


def playlist_search(search_term, results=5):
    """
    Searches youtube for a playlist matching the search term.

    :param search_term: str the search term to search to search for.
    :param results: int the number of playlist matches we want returned.
    :return: list[dict{'playlist_title', 'playlist_id'}] or None on failure.
    """
    if search_term:
        url = PLAYLIST_SEARCH_URL.format(API_KEY, util.web.quote(search_term.encode('ascii', 'ignore')))
        response = util.web.http_get(url=url, json=True, referer='http://tinychat.com')

        if response['json'] is not None:
            play_lists = []
            try:
                if 'items' in response['json']:
                    for i, item in enumerate(response['json']['items']):
                        if i == results:
                            return play_lists
                        playlist_id = item['id']['playlistId']
                        playlist_title = item['snippet']['title']  #
                        play_list_info = {
                            'playlist_title': playlist_title,
                            'playlist_id': playlist_id
                        }
                        play_lists.append(play_list_info)
            except KeyError as ke:
                log.error(ke, exc_info=True)
                return None


def playlist_videos(playlist_id):
    """
    Find the videos for a given playlist ID.

    The list returned will contain a maximum of 50 videos.

    :param playlist_id: str the playlist ID
    :return: list[dict{'type=youTube', 'video_id', 'video_title', 'video_time'}] or None on failure.
    """
    url = PLAYLIST_ITEMS_URL.format(API_KEY, playlist_id)
    response = util.web.http_get(url=url, json=True, referer='http://tinychat.com')

    if response['json'] is not None:
        video_list = []
        # next_page_token = response['json']['nextPageToken']
        try:
            if 'items' in response['json']:
                for item in response['json']['items']:
                    video_id = item['snippet']['resourceId']['videoId']
                    details = video_details(video_id)
                    if details is not None:
                        info = {
                            'type': 'youTube',
                            'video_id': video_id,
                            'video_title': details['video_title'],
                            'video_time': details['video_time'],
                            'image': details['image']
                        }
                        video_list.append(info)
                return video_list
        except KeyError as ke:
            log.error(ke, exc_info=True)
            return None


def video_details(video_id, check=True):
    """
    Youtube helper function to get the video time for a given video id.

    Checks a youtube video id to see if the video is blocked or allowed
    in the ALLOWED_COUNTRIES list. If a video is blocked in one of the countries, 
    None is returned. If a video is NOT allowed in ONE of the countries, 
    None is returned else the video time will be returned.

    :param check: bool True = checks region restriction. False = no check will be done
    :param video_id: The youtube video id str to check.
    :return: dict{'type=youTube', 'video_id', 'video_time', 'video_title'} or None
    """
    url = VIDEO_DETAILS_URL.format(API_KEY, video_id)
    response = util.web.http_get(url=url, json=True, referer='http://tinychat.com')

    if response['json'] is not None:
        try:
            if 'items' in response['json']:
                if len(response['json']['items']) is not 0:
                    contentdetails = response['json']['items'][0]['contentDetails']
                    if check:
                        if 'regionRestriction' in contentdetails:
                            if 'blocked' in contentdetails['regionRestriction']:
                                blocked = contentdetails['regionRestriction']['blocked']
                                if [i for e in ALLOWED_COUNTRIES for i in blocked if e in i]:
                                    log.info('%s is blocked in: %s' %
                                             (video_id, blocked))
                                    return None
                            if 'allowed' in contentdetails['regionRestriction']:
                                allowed = contentdetails['regionRestriction']['allowed']
                                if [i for e in ALLOWED_COUNTRIES for i in allowed if e not in i]:
                                    log.info('%s is allowed in: %s' %
                                             (video_id, allowed))
                                    return None
                    video_time = util.string_util.convert_to_seconds(contentdetails['duration'])
                    video_title = response['json']['items'][0]['snippet']['title']  #
                    thumb = response['json']['items'][0]['snippet']['thumbnails']['medium']['url']

                    return {
                        'type': 'youTube',
                        'video_id': video_id,
                        'video_time': video_time,
                        'video_title': video_title,
                        'image': thumb
                    }
                return None
        except KeyError as ke:
            log.error(ke, exc_info=True)
            return None
