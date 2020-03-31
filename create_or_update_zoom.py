#!/usr/bin/env python

import os
import sys
import json

from pdb import set_trace as debug
import dateutil.parser
import datetime
import pytz
from pdb import set_trace as debug
from argparse import ArgumentParser
import copy

parser = ArgumentParser()
parser.add_argument("--clearAll", action="store_true", help="delete any existing webinars that start with AIWeb")
parser.add_argument("--users", action="store_true")
parser.add_argument("--meeting", action="store_true", help="create a meeting not a webinar")

ns = parser.parse_args()

from secrets import *
mytz = pytz.timezone("America/Los_Angeles")
UTC = pytz.timezone("UTC")

integrations_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(integrations_dir, "zoomus"))
import copy

timeformat = "%Y-%m-%dT%H:%M:00Z"   # the python datetime object should be in UTC time.
roundingerror = datetime.timedelta(microseconds=5)


#if ns.clearAll:
#    webinars = json.loads(client.webinar.list(user_id=user_id, page_size=300).content).get("webinars")
#    while webinars:
#        print("Found {0}".format(len(webinars)))
#        for webinar in webinars:
#            name = webinar.get("topic")
#            if name in ["Zoom Meeting", "AIWeb", "ICLR Meeting", "Lee and Andrea"]:
#                result = client.webinar.delete(user_id=user_id, id=webinar.get("id"))
#            print(name)
#        webinars = json.loads(client.webinar.list(user_id=user_id, page_size=300).content).get("webinars")
#
#    meetings = json.loads(client.meeting.list(user_id=user_id, page_size=300).content).get("meetings")
#    while meetings:
#        print("Found {0}".format(len(meetings)))
#        for meeting in meetings:
#            name = meeting.get("topic")
#            if name in ["Zoom Meeting", "AIWeb", "ICLR Meeting", "Lee Campbell's Zoom Meeting"]:
#                result = client.meeting.delete(user_id=user_id, id=meeting.get("id"))
#            print(name)
#        meetings = json.loads(client.webinar.list(user_id=user_id, page_size=300).content).get("meetings")
#    sys.exit()
#
#if ns.users:
#    template = {
#        "action":"create",
#        "user_info": {
#            "type":1
#        }
#    }
#    #needed_users = [{"email":'brockmeyer@salk.edu', "first_name":"Brad", "last_name":"Brockmeyer"}, {"email":"terrence.gaines@hp.com", "first_name":"Terrence", "last_name":"Gaines"}, {"email":"meperry@salk.edu", "first_name":"Mary Ellen", "last_name":"Perry"}]
#    needed_users = [{"email":"terrence.gaines@hp.com", "first_name":"Terrence", "last_name":"Gaines"}]
#    existing_emails = [item.get("email") for item in user_list.get("users")]
#
#    for user in needed_users:
#        if not user.get("email") in existing_emails:
#            this_template = copy.copy(template)
#            this_template['user_info'].update(user)
#            result = client.user.create(**this_template)
#            print(result.content)
#    sys.exit()


results = {}

def create_or_update_zoom(excel_data):

    """Handle starttime and endtime as strings or naive datetime objects depending on how the user typed them in"""

    starttime = excel_data.get("starttime")
    endtime = excel_data.get("endtime")
    
    if starttime and endtime:
        
        if type(starttime) == str:
            starttime = datetime.datetime.strptime(starttime, "%Y-%m-%dT%H:%M:00Z")
            endtime = datetime.datetime.strptime(endtime, "%Y-%m-%dT%H:%M:00Z")

    
        timezone_name = excel_data.get("timezone")
        if not timezone_name:
            timezone_name = "UTC"
        TZ = pytz.timezone(timezone_name)

        starttime += roundingerror  #Somemtimes we get a rounding error from Excel. Round to nearest.
        starttime = starttime.replace(microsecond=0)
        endtime += roundingerror  
        endtime = endtime.replace(microsecond=0)
        starttime = TZ.localize(starttime)
        endtime = TZ.localize(endtime)
        utc_starttime = UTC.normalize(starttime).strftime(timeformat)
        utc_endtime = UTC.normalize(endtime).strftime(timeformat)
        meeting_type = excel_data.get("meeting_or_webinar")

        #if excel_data.get("peerreviewid") == "Workshopapplication-36":
        #    debug()

        """Update an existing meeting if there is one noted in the excel spreadsheet"""
        existing_meeting_id = excel_data.get("zoomid")
        
        if meeting_type in ['meeting', "webinar"]:
            if existing_meeting_id:
                """Update an existing meeting"""
                existing_meeting = eval("client.{0}.get(user_id=int({1}), meetingId={2}".format(meeting_type, user_id, existing_meeting_id))
            else:
                """"Create a new meeting or webinar"""
                zoom_data = copy.copy(eval("{0}_defaults".format(meeting_type)))

                """Load the defaults definition"""
                zoom_data = copy.copy(eval("{0}_defaults".format(meeting_type)))
                zoom_data.update({
                    "agenda": str(excel_data.get("peerreviewid")),
                    "topic": excel_data.get("title"),
                    "start_time": utc_starttime,
                    })
                zoom_data['recurrence'].update({"endtime": utc_endtime})
                function_call = eval("client.{0}.create".format(meeting_type))
                result = function_call(user_id=user_id, **zoom_data)
                return_val = json.loads(result.content)
                return_val['status'] = result.ok
                return_val['action'] = "create"
            return(return_val)
        else:
            return({"action": "skipped due to incorrect meeting type in meeting_or_webinar: {}".format(excel_data.get("title"))})

    else:
        return({"action": "skipped due to no start or no end time".format(excel_data.get("title"))})



   