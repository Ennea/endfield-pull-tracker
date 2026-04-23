import logging
import re
import os
import sys

from enum import StrEnum
from pathlib import Path
from urllib.parse import parse_qs


class CharacterBannerType(StrEnum):
    BEGINNER = 'E_CharacterGachaPoolType_Beginner'
    STANDARD = 'E_CharacterGachaPoolType_Standard'
    EVENT = 'E_CharacterGachaPoolType_Special'

def error_and_exit(msg, *args):
    logging.error(msg, *args)
    sys.exit(1)

def get_auth_token():
    if sys.platform == 'linux':
        try:
            cache_path = Path(os.environ['LOCALAPPDATA']).expanduser() / 'PlatformProcess' / 'Cache' / 'data_1'
        except KeyError:
            error_and_exit('Please set LOCALAPPDATA to point to AppData/Local inside the Wine prefix where Endfield is installed')
            return
    elif sys.platform == 'win32':
        cache_path = Path(os.environ['LOCALAPPDATA']) / 'PlatformProcess' / 'Cache' / 'data_1'
    else:
        error_and_exit('Unsupported platform')
        return

    if not cache_path.exists():
        error_and_exit('Cache path "%s" does not exist', cache_path)

    with cache_path.open('rb') as fp:
        cache_data = fp.read()

    # match all relevant URLs, store the last match
    match = None
    for m in re.finditer(rb'https://ef-webview\.gryphline\.com/page/gacha.+?\?(.+?)\0', cache_data):
        match = m

    if match is None:
        error_and_exit("Could not find auth token, please make sure you've recently opened your pull history ingame")
        return

    query_string = match.group(1).decode('utf-8')
    query_params = parse_qs(query_string)
    auth_token = query_params['u8_token'][0]
    del query_params['u8_token']
    logging.info('Found URL with query params (omitting token): %s', query_params)

    return auth_token
