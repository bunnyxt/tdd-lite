import requests
import argparse
import schedule
import threading
import logging
import time
import json
from collections import namedtuple
from utils import a2b, b2a, is_valid_bvid, now_ts, ts2str

Record = namedtuple('Record', ['added', 'aid', 'bvid', 'view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like'])


def fetch_video_stat(aid, output_filename):
    with open(output_filename, 'a') as f:
        r = requests.get('http://api.bilibili.com/x/web-interface/archive/stat?aid=%d' % aid)

        if r.status_code != 200:
            logging.warning('Unexpected HTTP status code %d got, continue.' % r.status_code)
            return

        try:
            obj = json.loads(r.text)
        except Exception:
            logging.warning('Fail to parse response text %s, continue.' % r.text)
            return

        if obj['code'] != 0:
            logging.warning('Unexpected response code %d got, continue.' % obj['code'])
            return

        try:
            obj_data = obj['data']
        except Exception:
            logging.warning('Fail to get data of obj %s, continue.' % str(obj))
            return

        record = Record(
            added=now_ts(), aid=aid, bvid=a2b(aid),
            view=obj_data['view'], danmaku=obj_data['danmaku'], reply=obj_data['reply'], favorite=obj_data['favorite'],
            coin=obj_data['coin'], share=obj_data['share'], like=obj_data['like'],
        )

        logging.info(record)
        f.write('%d,%d,%s,%d,%d,%d,%d,%d,%d,%d\n' % (
            record.added, record.aid, record.bvid,
            record.view, record.danmaku, record.reply, record.favorite, record.coin, record.share, record.like
        ))


def fetch_video_stat_task(aid, output_filename):
    threading.Thread(target=fetch_video_stat, args=(aid, output_filename)).start()


def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--aid',
        type=int,
        help='aid of video, ex: 456930',
    )
    parser.add_argument(
        '-b', '--bvid',
        type=str,
        help='bvid of video, ex: 19x411F7kL',
    )
    parser.add_argument(
        '-i', '--interval',
        type=int,
        help='interval of fetch task (seconds), default: 60',
        default=60,
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='output filename',
    )
    # TODO finish flag, after %d seconds or %d fetch nums

    args = parser.parse_args()
    aid = args.aid
    bvid = args.bvid
    interval = args.interval
    output_filename = args.output

    # aid or bvid must be assigned
    if aid is None and bvid is None:
        logging.error('No aid or bvid assigned, exit.')
        exit(1)

    # both aid and bvid assigned, ignore bvid
    if aid is not None and bvid is not None:
        bvid = None
        logging.warning('Both aid (%d) and bvid (%s) assigned, ignore bvid.' % (aid, bvid))

    # fill aid and bvid
    if aid is None:
        if not is_valid_bvid(bvid):
            logging.error('Assigned bvid %s is invalid, exit.' % bvid)
            exit(1)
        aid = b2a(bvid)
    if bvid is None:
        bvid = a2b(aid)

    # set output_filename
    if output_filename is None:
        output_filename = 'output_av%d_%ds_%s.csv' % (aid, interval, ts2str(now_ts(), '%Y%m%d%H%M%S'))
    with open(output_filename, 'a') as f:
        f.write('added,aid,bvid,view,danmaku,reply,favorite,coin,share,like\n')

    # set up schedule
    schedule.every(interval).seconds.do(fetch_video_stat_task, aid=aid, output_filename=output_filename)
    logging.info('Will fetch stat of video (aid: %d, bvid: %s) every %d seconds and save to file %s...' % (
        aid, bvid, interval, output_filename,
    ))

    # schedule loop
    fetch_video_stat_task(aid, output_filename)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s][%(name)s][%(levelname)s]: %(message)s', level=logging.INFO)
    main()
