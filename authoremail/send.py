#!/usr/bin/env python

from pdb import set_trace as debug
import sys, os
from django.template import Template
import traceback

cwd = os.getcwd()

from django.core.wsgi import get_wsgi_application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.conf import settings
sys.path.append(BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'djnipscc.settings'
application = get_wsgi_application()

#from serversettings import *
DATABASE = settings.DATABASE 
from nips.models import *
from nips.excel2dict import excel2dict

from openpyxl import load_workbook, Workbook
from nips.models import Message

from django.utils.html import escape as html_escape

"""Rocketchat logins"""
forum_ids = Events.objects.filter(type="Poster", session__conference__id=2020).exclude(uniqueid__endswith="-2nd").order_by("uniqueid").values_list("uniqueid", flat=True)

rocketchat_logins = {i[1]:"poster_{}".format(i[0]) for i in enumerate(forum_ids, 1)}



"""Rocketchat passwords"""
rocketchat_passwords_data = excel2dict("xltozoom/authoremail/rocketchat-authorPasswords.xlsx")
rocketchat_passwords = {i['email']:i['password'] for i in rocketchat_passwords_data}

ess = Eventspeakers.objects.filter(event__session__conference__id=settings.CURRENT_CONFERENCE, event__type="Poster").exclude(event__uniqueid__endswith="-2nd")



authors = Users.objects.filter(pk__in=Eventspeakers.objects.filter(event__type="Poster", event__session__conference__id=2020).values("speaker")).distinct().order_by("firstname")

all_papers = Events.objects.filter(session__conference__id=2020, type="Poster").order_by("uniqueid")


final_schedule = excel2dict("/Users/lee/Dropbox/ICLR/2020 Addis Ababa/AcceptedPapers/final-updated2.xlsx")
zoom_info = {}
zoom_data_headers = ['uniqueid', "password", "timezone_choice", "host_zoom_user_email", "zoomid", "join_link", "start_link" ]
os.chdir(cwd)

template = Template(open("template.html", 'rb').read().decode("utf-8"))

for row in final_schedule:
    uniqueid = row.get("uniqueid").replace("-2nd", "")
    zoomdata = [uniqueid, row.get("password"), row.get("timezone_choice"), row.get("host_zoom_user_email"), row.get("zoomid"), row.get("join_link"), row.get("start_link") ]
    zoomdatadict = dict(zip(zoom_data_headers, zoomdata))
    zoom_info[uniqueid] = zoom_info.get(uniqueid, []) + [zoomdatadict]


for user in authors:
    papers = ess.filter(speaker=user)
    user.rocketchat_password = rocketchat_passwords[user.email]
    for es in papers:

        es.rocketchat_login = "https://iclr.rocket.chat/channel/{}".format(rocketchat_logins[es.event.uniqueid])
        
        es.zoominfo = zoom_info.get(es.event.uniqueid)
    print(user.lastname)
    html = template.render(Context(locals()))
    filename = "/tmp/{}.html".format(user.email)
    open(filename, 'wb').write(html.encode("utf-8"))
    #os.system("open '{}'".format(filename))


    msg = Message(To=user.email)
    msg.Subject = "ICLR 2020 Author Instructions"
    msg.Html = html
    try:
        msg.snlSend()
    except exception as e:
        tb = traceback.format_exc()
        print(tb)
        debug()
sys.exit()


