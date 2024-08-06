#!/usr/bin/env python3
import sys
from optparse import OptionParser
from operator import itemgetter
from resources.lib.epg import get_iptv_epg

# parse the options
parser = OptionParser()
parser.add_option('-a', '--authorize', action='store_true', dest='authorize')
parser.add_option('-u', '--username', type='string', dest='username', help='CBC username')
parser.add_option('-p', '--password', type='string', dest='password', help='CBC password')
parser.add_option('-b', '--browse', action='store_true')
parser.add_option('-f', '--format', action='store')
# ?
parser.add_option('-g', '--guide', action='store_true', dest='guide', help="run guide code")
parser.add_option('-l', '--live-programs', action='store_true', dest='progs')
parser.add_option('-i', '--iptv', action='store_true', dest='iptv', help="IPTV Channel List")
parser.add_option('-I', '--iptv-channel', type='string', dest='channel', help="IPTV Channel ID")
parser.add_option('-c', '--channels', action='store_true', dest='chans')
parser.add_option('-C', '--category', action='store', dest='category')
parser.add_option('-v', '--video', action='store_true', dest='video')
parser.add_option('-s', '--shows', action='store_true', dest='shows')
parser.add_option('-S', '--show', action='store')
parser.add_option('-e', '--episode', action='store')
(options, args) = parser.parse_args()

from resources.lib.livechannels import *
# from resources.lib.liveprograms import *
# from resources.lib.shows import *
from resources.lib.cbc import CBC
from resources.lib.gemv2 import GemV2

def progress(x):
    print(x)

cbc = CBC()
chans = LiveChannels()
# events = LivePrograms()
# shows = Shows()
res = []

if options.authorize:
    if not cbc.azure_authorize(options.username, options.password, progress):
        print('Error: Authorization failed')
        sys.exit(1)
    print('Authorization successful')
    sys.exit(0)
if options.browse:
    b = GemV2.get_browse()
    if b is None:
        print('None from get_browse')
        sys.exit(1)
    for a in b:
        print(a)
    sys.exit(0)
if options.format:
    b = GemV2.get_format(options.format)
    i = 7
    # i = 0
    n = GemV2.normalized_format_item(b[i])
    p = GemV2.normalized_format_path(b[i])
    print(n)
    b = GemV2.get_format(p)
    n = GemV2.normalized_format_item(b[0])
    p = GemV2.normalized_format_path(b[0])
    print(n)
    b = GemV2.get_format(p)
    n = GemV2.normalized_format_item(b[1])
    p = GemV2.normalized_format_path(b[1])
    print(n)
    s = GemV2.get_stream(id=p, app_code=n['app_code'])
    print(f"{s['type']} {s['url']}")
    x = GemV2.get_stream_drm(s)
    wv_url, wv_tok = GemV2.get_stream_drm(s)
    print(wv_url)
    print(wv_tok)
    sys.exit(0)
if options.guide:
    get_iptv_epg()
elif options.iptv:
    live = LiveChannels()
    for channel in live.get_iptv_channels():
        id, name = itemgetter('id', 'name')(channel)
        print(f'{id} - {name}')
elif options.channel:
    live = LiveChannels()
    stream = live.get_channel_stream(options.channel)
    print(stream)    
elif options.chans:
    res = chans.get_live_channels()
    print(res)
elif options.progs:
    res = events.getLivePrograms()
elif options.video:
    try:
        res = shows.getStream(args[0])
    except CBCAuthError as e:
        print('ERROR: login required' if e.payment else 'ERROR: Unauthorized')
        sys.exit(1)
    print(res)
    sys.exit(0)
else:
    print('\nPlease specify something to do\n')
    parser.print_help()
    sys.exit(1)

if 'categories' in res:
    for category in res['categories']:
        id, title, _ = category.values()
        print(f'Category: {id} - {title}')
if 'shelves' in res:
    for shelf in res['shelves']:
        id, title, _, items = shelf.values()
        print(f'Shelves:  {id} - {title}')
