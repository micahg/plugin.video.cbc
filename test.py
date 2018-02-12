#!/usr/bin/python
import sys, os
from optparse import OptionParser

# parse the options
parser = OptionParser()
parser.add_option('-g', '--guid', type='string', dest='guid',
                  help="not actually a guid")
parser.add_option('-p', '--programs', action='store_true', dest='progs')
parser.add_option('-c', '--channels', action='store_true', dest='chans')
(options, args) = parser.parse_args()

from resources.lib.livechannels import *
from resources.lib.liveprograms import *
from resources.lib.cbc import *

cbc = CBC()
chans = LiveChannels()
events = LivePrograms()
res = []

if options.chans:
    res = chans.getLiveChannels()
elif options.progs:
    res = events.getLivePrograms()

for item in res:
    if options.guid == None:
        if options.chans:
            print '{}) {} {}: {}'.format(item['guid'], item['cbc$callSign'], item['title'], item['description'])
        elif options.progs:
            if item['availabilityState'] == 'available':
                print '{}) {}: {}'.format(item['guid'], item['title'], item['description'])
    elif item['guid'] == options.guid:
        smil = item['content'][0]['url']
        print cbc.parseSmil(smil)

