import logging
import re
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
    cache_path = Path('~/Games/umu/endfield/drive_c/users/steamuser/AppData/Local/PlatformProcess/Cache').expanduser() / 'data_1'
    if not cache_path.exists():
        error_and_exit('Cache path "%s" does not exist', cache_path)

    with cache_path.open('rb') as fp:
        cache_data = fp.read()

    # match all relevant URLs, store the last match
    match = None
    for m in re.finditer(rb'https://ef-webview\.gryphline\.com/page/gacha.+?\?(.+?)\0', cache_data):
        match = m

    if match is None:
        error_and_exit('Could not find auth token')
        return

    query_string = match.group(1).decode('utf-8')
    query_params = parse_qs(query_string)
    auth_token = query_params['u8_token'][0]
    del query_params['u8_token']
    logging.info('Found URL with query params (omitting token): %s', query_params)

    return auth_token
