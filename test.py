#!/usr/bin/python
import sys, os
from optparse import OptionParser

from resources.lib.livechannels import *

chans = LiveChannels()
res = chans.getLiveChannels()
for item in res:
    print '{} {}: {}'.format(item['cbc$callSign'], item['title'], item['description'])
    print item['content'][0]['url'] + '\n'

