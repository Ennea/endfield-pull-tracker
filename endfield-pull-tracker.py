#!/bin/env python3

import argparse
import json
import logging
import os
import tempfile
import time
import subprocess

from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode

from database import Database
from util import get_auth_token, CharacterBannerType


CHARACTER_API_URL = 'https://ef-webview.gryphline.com/api/record/char'
WEAPON_API_URL = 'https://ef-webview.gryphline.com/api/record/weapon'


def retrieve_pull_data():
    db = Database()
    auth_token = get_auth_token()

    # character banners
    for banner_type in (CharacterBannerType.BEGINNER, CharacterBannerType.STANDARD, CharacterBannerType.EVENT):
        query_params = {
            'lang': 'en-us',
            'server_id': 3,
            'pool_type': banner_type,
            'token': auth_token
        }

        bail_id = db.get_latest_character_pull_id(banner_type)
        logging.info('Fetching character pulls for banner type "%s"; latest pull ID we have is %s', banner_type, bail_id)
        while True:
            try:
                logging.info('Requesting character pulls starting after ID %s', query_params['seq_id'] if 'seq_id' in query_params else None)
                with urlopen(f'{CHARACTER_API_URL}?{urlencode(query_params)}') as request:
                    result = request.read()
                    json_result = json.loads(result)

                    # map pulls as a list of tuples for DB insertion
                    pulls = []
                    bail_id_reached = False
                    for e in json_result['data']['list']:
                        if bail_id is not None and not bail_id_reached and int(e['seqId']) <= bail_id:
                            bail_id_reached = True

                        pulls.append((
                            e['seqId'],
                            e['poolId'],
                            e['poolName'],
                            e['charId'],
                            e['charName'],
                            e['rarity'],
                            e['gachaTs'],
                            1 if e['isNew'] else 0,
                            1 if e['isFree'] else 0
                        ))

                    db.insert_character_pulls(pulls)

                    # determine whether we stop querying now
                    if not json_result['data']['hasMore']:
                        logging.info('API does not have more data, stopping')
                        break

                    if bail_id_reached:
                        logging.info('Bail ID reached, stopping')
                        break

                    # set the last sequence ID for the next request
                    query_params['seq_id'] = json_result['data']['list'][-1]['seqId']
            except Exception as e:
                logging.error('Error: %s', e)
                break
            finally:
                time.sleep(2)

    # weapon banners
    query_params = {
        'lang': 'en-us',
        'server_id': 3,
        'token': auth_token
    }

    bail_id = db.get_latest_weapon_pull_id()
    logging.info('Fetching weapon pulls; latest pull ID we have is %s', bail_id)
    while True:
        try:
            logging.info('Requesting weapon pulls starting after ID %s', query_params['seq_id'] if 'seq_id' in query_params else None)
            with urlopen(f'{WEAPON_API_URL}?{urlencode(query_params)}') as request:
                result = request.read()
                json_result = json.loads(result)

                # map pulls as a list of tuples for DB insertion
                pulls = []
                bail_id_reached = False
                for e in json_result['data']['list']:
                    if bail_id is not None and not bail_id_reached and int(e['seqId']) <= bail_id:
                        bail_id_reached = True

                    pulls.append((
                        e['seqId'],
                        e['poolId'],
                        e['poolName'],
                        e['weaponId'],
                        e['weaponName'],
                        e['weaponType'],
                        e['rarity'],
                        e['gachaTs'],
                        1 if e['isNew'] else 0
                    ))

                db.insert_weapon_pulls(pulls)

                # determine whether we stop querying now
                if not json_result['data']['hasMore']:
                    logging.info('API does not have more data, stopping')
                    break

                if bail_id_reached:
                    logging.info('Bail ID reached, stopping')
                    break

                # set the last sequence ID for the next request
                query_params['seq_id'] = json_result['data']['list'][-1]['seqId']
        except Exception as e:
            logging.error('Error: %s', e)
            break
        finally:
            time.sleep(2)

def transform_pull_data(pulls):
    ten_pull = None
    for i in range(len(pulls)):
        p = pulls[i]

        p['new'] = True if p['new'] == 1 else False
        p['free'] = True if 'free' in p and p['free'] == 1 else False

        # flag the first pull after switching banners
        banner_change = False
        if i > 0 and p['bannerID'] != pulls[i - 1]['bannerID']:
            banner_change = True
        p['bannerChange'] = banner_change

        # mark all pulls belonging to a 10-pull
        if (
            ten_pull is None and
            i + 9 <= len(pulls) - 1 and  # there's enough space forward
            p['timestamp'] == pulls[i + 9]['timestamp']  # same timestamp on this pull and 9 ahead
        ):
            ten_pull = 9
            p['tenPull'] = 'start'
        elif ten_pull is not None and ten_pull > 0:
            ten_pull -= 1
            if ten_pull == 0:
                ten_pull = None
                p['tenPull'] = 'end'
            else:
                p['tenPull'] = 'middle'
        else:
            p['tenPull'] = None

def generate_report():
    db = Database()

    character_pulls = db.get_character_pulls()
    weapon_pulls = db.get_weapon_pulls()

    transform_pull_data(character_pulls)
    transform_pull_data(weapon_pulls)

    # open all template files
    html_fp = Path(__file__).with_name('index.html').open('r', encoding='utf-8')
    css_fp = Path(__file__).with_name('style.css').open('r', encoding='utf-8')
    js_fp = Path(__file__).with_name('script.js').open('r', encoding='utf-8')

    tmp_fd, tmp_path = tempfile.mkstemp('.html', text=True)
    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as tmp_fp:
        tmp_fp.write(
            html_fp.read()
                .replace('<link rel="stylesheet" href="style.css">', '<style>' + css_fp.read() + '</style>')
                .replace(
                    '<script src="script.js"></script>',
                    f'<script>{js_fp.read()}\nBuildVisualization("characters", {json.dumps(character_pulls)});\nBuildVisualization("weapons", {json.dumps(weapon_pulls)});</script>'
                )
        )

    html_fp.close()
    css_fp.close()
    js_fp.close()

    subprocess.run([ 'firefox-developer-edition', tmp_path ])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    argument_parser = argparse.ArgumentParser('Endfield Pull Tracker')
    argument_parser.add_argument('command', choices=[ 'retrieve-data', 'generate-report' ], default='retrieve-data', nargs='?')

    arguments = argument_parser.parse_args()
    if arguments.command == 'retrieve-data':
        retrieve_pull_data()
    elif arguments.command == 'generate-report':
        generate_report()
