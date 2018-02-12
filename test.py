#!/usr/bin/python
import sys, os
from optparse import OptionParser

# parse the options
parser = OptionParser()
parser.add_option('-g', '--guid', type='string', dest='guid',
                  help="not actually a guid")
(options, args) = parser.parse_args()

from resources.lib.livechannels import *
from resources.lib.cbc import *

cbc = CBC()
chans = LiveChannels()
res = chans.getLiveChannels()
for item in res:
    if options.guid == None:
        print '{}) {} {}: {}'.format(item['guid'], item['cbc$callSign'], item['title'], item['description'])
    elif item['guid'] == options.guid:
        smil = item['content'][0]['url']
        print cbc.parseSmil(smil)

