#!/usr/bin/env python

from pdb import set_trace as debug
import sys, os
from django.core.wsgi import get_wsgi_application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.conf import settings
sys.path.append(BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'djnipscc.settings'
application = get_wsgi_application()

#from serversettings import *
DATABASE = settings.DATABASE 

from nips.excel2dict import excel2dict

import openpyxl

rocketchat = excel2dict("xltozoom/authoremail/rocketchat.xlsx")

