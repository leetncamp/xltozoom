#!/usr/bin/env python

import os
import sys
import json

from pdb import set_trace as debug
import dateutil.parser
import datetime
import pytz
stop = debug
from argparse import ArgumentParser
import copy
from email.utils import parseaddr
from nameparser import HumanName
import traceback

from secrets import *
mytz = pytz.timezone("America/Los_Angeles")
UTC = pytz.timezone("UTC")
NOW = datetime.datetime.now()

integrations_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(integrations_dir, "zoomus"))
sys.path.append(integrations_dir)
parent = os.path.dirname(integrations_dir)

if parent:
    sys.path.append(parent)

import copy

timeformat = "%Y-%m-%dT%H:%M:00Z"   # the python datetime object should be in UTC time.
roundingerror = datetime.timedelta(microseconds=5)


#def clearAll(client=None, user_id=None):
#
#    if not client:
#        from zsecrets import client
#
#    if user_id and type(user_id) == str:
#        user_result = json.loads(client.user.get(id=user_id).content)
#        user_id = user_result.get('id')
#    else:
#        from zsecrets import user_id  #use the user_id in zsecrets 
#
#
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
#    return

#def users():
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
#    return


webinar_update_errors = {
    200: "Webinar subscription plan is missing.",
    204: "Webinar Updated",
    300: "Invalid webinar Id or Invalid recurrence settings",
    400: "Bad Request.  Invalid User or access denied to the meeting. Are you the host?",
}

meeting_update_errors = {
    204: "Meeting Updated",
    300: "Invalid enforce_login_domains, separate multiple domains by semicolon, OR The maximum of meetings can be created/updated for a single user in one day.",
    400: "Bad Request. Invalid User. Are you the host?",
    404: "Trying to add a host that is not associated with a Zoom",
}


results = {}



existing_zoom_events = {}
existing_checked = False



        
def get_existing_meetings(user_id=None, client=None):

    """leave two variables in the global namespace of this file: existing_zoom_events and existing_checked. Look up
    existing events here rather than hitting the API for each event.  existing_checked indicates whether
    existing_zoom_events has already been loaded.  user_id is an email address or zoom alphanumeric id. """

    """TODO re-write this to avoid using globals.  No need for that in the current design where each presenter gets
    their own license"""
    print(f"user_id: {user_id}")
    try:
        if not client:
            from zsecrets import client

        if user_id and type(user_id) == str:
            user_result = json.loads(client.user.get(id=user_id).content)
            user_id = user_result.get('id')
        else:
            print("Defaulting to user_id in zsecrets")
            from zsecrets import user_id  # use the user_id in zsecrets


        existing_meetings_result = client.meeting.list(user_id=user_id, page_size=300)
        if existing_meetings_result.ok:
            emresults = json.loads(existing_meetings_result.content)
            existing_meeting_list = emresults.get("meetings")
            existing_meetings = {item.get("agenda"): item for item in existing_meeting_list}
        else:
            print(traceback.format_exc())
            stop()

        existing_webinars_result = client.webinar.list(user_id=user_id, page_size=300)
        if existing_webinars_result.ok:
            emresults = json.loads(existing_webinars_result.content)
            existing_webinar_list = emresults.get("webinars")
            print("Found {} existing webinars".format(len(existing_webinar_list)))
            print("Total reported: {}".format(emresults.get("total_records")))
            existing_webinars = {item.get("agenda"): item for item in existing_webinar_list}
        else:
            resultDict = json.loads(existing_webinars_result.content)
            if not resultDict.get("message", "").startswith("Cannot use webinar API"):
                print(existing_webinars_result.content)
            existing_webinars = {}

        existing_checked = True
        
        NONE = existing_zoom_events.pop(None, None)
    except Exception as e:
        print(traceback.format_exc())
        stop()
        existing_meetings = []
        existing_webinars = []
    return(existing_meetings, existing_webinars)


def get_all_events():
    try:
        from zsecrets import client, user_id, meeting_defaults, webinar_defaults
    except ImportError:
        stop()

    from zsecrets import social_client as client
    from zsecrets import social_user_id as user_id
    meetings = json.loads(client.meeting.list(user_id=user_id, page_size=300).content).get("meetings")
    #    while meetings:
    #        print("Found {0}".format(len(meetings)))
    #        for meeting in meetings:
    #            name = meeting.get("topic")
    #            if name in ["Zoom Meeting", "AIWeb", "ICLR Meeting", "Lee Campbell's Zoom Meeting"]:
    #                result = client.meeting.delete(user_id=user_id, id=meeting.get("id"))
    #            print(name)
    #        meetings = json.loads(client.webinar.list(user_id=user_id, page_size=300).content).get("meetings")
    #    sys.exit()


    
    results = True
    count = 1
    users = set()
    while results:
        size = len(users)
        results = json.loads(client.user.list(page_size=300, page_number=count).content).get("users")
        print(len(results))
        ids = [i.get('id') for i in results]
        users = users.union(set(ids))
        count += 1
        if len(users) == size:
            #No new names were added. Stop
            results = False
    
    events = {}
    for user in users:
        result = client.meeting.list(user_id=user, page_size=300)
        meetings = json.loads(result.content).get("meetings")
        result = client.webinar.list(user_id=user, page_size=300)

        webinars = json.loads(result.content).get("webinars")
        if not webinars:
            #If the users is unlicensed for a webinar, a None is returned. That will fail below. Change it to an empty list. 
            webinars = []

        print('.', end="")
        sys.stdout.flush()

        for meeting in meetings: 
            meeting.update({"type":"meeting"})
        events[user] = events.get(user, []) + meetings

        for webinar in webinars: 
            webinar.update({"type":"webinar"})
        events[user] = events.get(user, []) + webinars
        if meetings or webinars:
            print(events)
    import pickle
    pickle.dump(events, open("/tmp/events.pickle", 'wb'))
    print(json.dumps(events, indent=4))


def license_users():
    from zsecrets import client, user_id, meeting_defaults, webinar_defaults
    users = sorted(list(set(["iclrconf+BJgy96EYvr@gmail.com", "iclrconf+HyeSin4FPB@gmail.com", "iclrconf+rJe2syrtvS@gmail.com", "iclrconf+B1lPaCNtPB@gmail.com", "iclrconf+BJe55gBtvH@gmail.com", "iclrconf+BJlRs34Fvr@gmail.com", "iclrconf+HJenn6VFvB@gmail.com", "iclrconf+S1xitgHtvS@gmail.com", "iclrconf+rkxZyaNtwB@gmail.com", "iclrconf+rygf-kSYwH@gmail.com", "iclrconf+Skgvy64tvr@gmail.com", "iclrconf+S1evHerYPr@gmail.com", "iclrconf+HkxARkrFwB@gmail.com", "iclrconf+ryeYpJSKwr@gmail.com", "iclrconf+rJgsskrFwH@gmail.com", "iclrconf+Skep6TVYDB@gmail.com", "iclrconf+BkgzMCVtPB@gmail.com", "iclrconf+r1gfQgSFDr@gmail.com", "iclrconf+BJgnXpVYwS@gmail.com", "iclrconf+SJxSDxrKDr@gmail.com", "iclrconf+Bkl5kxrKDr@gmail.com", "iclrconf+B1evfa4tPB@gmail.com", "iclrconf+B1g5sA4twr@gmail.com", "iclrconf+B1gZV1HYvS@gmail.com", "iclrconf+Sylgsn4Fvr@gmail.com", "iclrconf+SJeNz04tDS@gmail.com", "iclrconf+ryxz8CVYDH@gmail.com", "iclrconf+S1ly10EKDS@gmail.com", "iclrconf+B1gHokBKwS@gmail.com", "iclrconf+HJgC60EtwB@gmail.com", "iclrconf+SylVNerFvr@gmail.com", "iclrconf+r1g6ogrtDr@gmail.com", "iclrconf+SkgscaNYPS@gmail.com", "iclrconf+BJlahxHYDS@gmail.com", "iclrconf+Bkl7bREtDr@gmail.com", "iclrconf+BJlguT4YPr@gmail.com", "iclrconf+ryebG04YvB@gmail.com", "iclrconf+rkeuAhVKvB@gmail.com", "iclrconf+S1g6xeSKDS@gmail.com", "iclrconf+rkeNfp4tPr@gmail.com", "iclrconf+rygwLgrYPB@gmail.com", "iclrconf+rkgqN1SYvr@gmail.com", "iclrconf+H1lZJpVFvr@gmail.com", "iclrconf+B1lGU64tDr@gmail.com", "iclrconf+H1loF2NFwr@gmail.com", "iclrconf+H1lmyRNFvr@gmail.com", "iclrconf+H1x5wRVtvS@gmail.com", "iclrconf+SkeFl1HKwr@gmail.com", "iclrconf+B1gF56VYPH@gmail.com", "iclrconf+r1lZgyBYwS@gmail.com", "iclrconf+SJx9ngStPH@gmail.com", "iclrconf+H1exf64KwH@gmail.com", "iclrconf+HJgK0h4Ywr@gmail.com", "iclrconf+Sye0XkBKvS@gmail.com", "iclrconf+Hye1RJHKwB@gmail.com", "iclrconf+rJleKgrKwS@gmail.com", "iclrconf+SJxE8erKDH@gmail.com", "iclrconf+SJgdnAVKDH@gmail.com", "iclrconf+SyljQyBFDH@gmail.com", "iclrconf+rJehNT4YPr@gmail.com", "iclrconf+Hkg-xgrYvH@gmail.com", "iclrconf+r1xMH1BtvB@gmail.com", "iclrconf+HklXn1BKDH@gmail.com", "iclrconf+rkg1ngrFPr@gmail.com", "iclrconf+rylvYaNYDH@gmail.com", "iclrconf+SylL0krYPS@gmail.com", "iclrconf+SJxrKgStDH@gmail.com", "iclrconf+BygSP6Vtvr@gmail.com", "iclrconf+SyevYxHtDB@gmail.com", "iclrconf+SylO2yStDr@gmail.com", "iclrconf+H1lK_lBtvS@gmail.com", "iclrconf+H1lmhaVtvr@gmail.com", "iclrconf+HJgCF0VFwr@gmail.com", "iclrconf+HkgH0TEYwH@gmail.com", "iclrconf+HkldyTNYwH@gmail.com", "iclrconf+B1x1ma4tDr@gmail.com", "iclrconf+rJeB36NKvB@gmail.com", "iclrconf+H1enKkrFDB@gmail.com", "iclrconf+H1gBsgBYwH@gmail.com", "iclrconf+H1ebhnEYDH@gmail.com", "iclrconf+HyeSin4FPB@gmail.com", "iclrconf+SJlpYJBKvH@gmail.com", "iclrconf+SkxpxJBKwS@gmail.com", "iclrconf+B1xm3RVtwB@gmail.com", "iclrconf+S1xitgHtvS@gmail.com", "iclrconf+S1evHerYPr@gmail.com", "iclrconf+rJgsskrFwH@gmail.com", "iclrconf+Skep6TVYDB@gmail.com", "iclrconf+BklEFpEYwS@gmail.com", "iclrconf+BklEFpEYwS@gmail.com", "iclrconf+S1glGANtDr@gmail.com", "iclrconf+S1glGANtDr@gmail.com", "iclrconf+S1gFvANKDS@gmail.com", "iclrconf+B1elCp4KwH@gmail.com", "iclrconf+Hkxzx0NtDB@gmail.com", "iclrconf+r1gfQgSFDr@gmail.com", "iclrconf+ryxdEkHtPS@gmail.com", "iclrconf+r1etN1rtPB@gmail.com", "iclrconf+SJxSDxrKDr@gmail.com", "iclrconf+SJeD3CEFPH@gmail.com", "iclrconf+r1e9GCNKvH@gmail.com", "iclrconf+HJgEMpVFwB@gmail.com", "iclrconf+ryl3ygHYDB@gmail.com", "iclrconf+Sylgsn4Fvr@gmail.com", "iclrconf+B1lj20NFDS@gmail.com", "iclrconf+rygfnn4twS@gmail.com", "iclrconf+S1ly10EKDS@gmail.com", "iclrconf+SkxQp1StDH@gmail.com", "iclrconf+SkgscaNYPS@gmail.com", "iclrconf+ByxaUgrFvH@gmail.com", "iclrconf+rkllGyBFPH@gmail.com", "iclrconf+rJlnxkSYPS@gmail.com", "iclrconf+rylHspEKPr@gmail.com", "iclrconf+SJlh8CEYDB@gmail.com", "iclrconf+rygGQyrFvH@gmail.com", "iclrconf+HJe_Z04Yvr@gmail.com", "iclrconf+r1lF_CEYwS@gmail.com", "iclrconf+rkgqN1SYvr@gmail.com", "iclrconf+rJeXS04FPH@gmail.com", "iclrconf+Syx7A3NFvH@gmail.com", "iclrconf+HyxG3p4twS@gmail.com", "iclrconf+Hyx0slrFvH@gmail.com", "iclrconf+Skxuk1rFwB@gmail.com", "iclrconf+BJlzm64tDH@gmail.com", "iclrconf+rkgO66VKDS@gmail.com", "iclrconf+SJg5J6NtDr@gmail.com", "iclrconf+HJxV-ANKDH@gmail.com", "iclrconf+rylBK34FDS@gmail.com", "iclrconf+ryxC6kSYPr@gmail.com", "iclrconf+S1lEX04tPr@gmail.com", "iclrconf+HyxJhCEFDS@gmail.com", "iclrconf+B1gqipNYwH@gmail.com", "iclrconf+HklQYxBKwS@gmail.com", "iclrconf+BkxXe0Etwr@gmail.com", "iclrconf+BJgZGeHFPH@gmail.com", "iclrconf+B1g8VkHFPH@gmail.com", "iclrconf+rklk_ySYPB@gmail.com", "iclrconf+HJeT3yrtDr@gmail.com", "iclrconf+HJxEhREKDH@gmail.com", "iclrconf+S1l8oANFDH@gmail.com", "iclrconf+H1lhqpEYPr@gmail.com", "iclrconf+Hkg-xgrYvH@gmail.com", "iclrconf+B1l4SgHKDH@gmail.com", "iclrconf+r1gelyrtwH@gmail.com", "iclrconf+HJeqhA4YDS@gmail.com", "iclrconf+B1lnbRNtwr@gmail.com", "iclrconf+ryxmb1rKDS@gmail.com", "iclrconf+Hyg-JC4FDr@gmail.com", "iclrconf+rkl3m1BFDB@gmail.com", "iclrconf+rkl8dlHYvB@gmail.com", "iclrconf+B1e9Y2NYvS@gmail.com", "iclrconf+B1x1ma4tDr@gmail.com", "iclrconf+rJe2syrtvS@gmail.com", "iclrconf+Bkeb7lHtvH@gmail.com", "iclrconf+SkxpxJBKwS@gmail.com", "iclrconf+rygf-kSYwH@gmail.com", "iclrconf+rkeiQlBFPB@gmail.com", "iclrconf+Syg-ET4FPS@gmail.com", "iclrconf+Syg-ET4FPS@gmail.com", "iclrconf+HJxNAnVtDS@gmail.com", "iclrconf+HkxCzeHFDB@gmail.com", "iclrconf+B1g5sA4twr@gmail.com", "iclrconf+ryxz8CVYDH@gmail.com", "iclrconf+SkxxtgHKPS@gmail.com", "iclrconf+BJgQ4lSFPH@gmail.com", "iclrconf+r1g6ogrtDr@gmail.com", "iclrconf+Bkl7bREtDr@gmail.com", "iclrconf+Sye_OgHFwH@gmail.com", "iclrconf+rJlUt0EYwS@gmail.com", "iclrconf+Skxd6gSYDS@gmail.com", "iclrconf+B1lGU64tDr@gmail.com", "iclrconf+BJlZ5ySKPH@gmail.com", "iclrconf+Hyx0slrFvH@gmail.com", "iclrconf+H1x5wRVtvS@gmail.com", "iclrconf+S1xKd24twB@gmail.com", "iclrconf+r1lZgyBYwS@gmail.com", "iclrconf+SJgaRA4FPH@gmail.com", "iclrconf+HJgK0h4Ywr@gmail.com", "iclrconf+HJxV-ANKDH@gmail.com", "iclrconf+HJxK5pEYvr@gmail.com", "iclrconf+ryxC6kSYPr@gmail.com", "iclrconf+r1evOhEKvH@gmail.com", "iclrconf+B1x6w0EtwH@gmail.com", "iclrconf+SJxE8erKDH@gmail.com", "iclrconf+BkxXe0Etwr@gmail.com", "iclrconf+HklUCCVKDB@gmail.com", "iclrconf+BJgd81SYwr@gmail.com", "iclrconf+B1g8VkHFPH@gmail.com", "iclrconf+SJgdnAVKDH@gmail.com", "iclrconf+rJehNT4YPr@gmail.com", "iclrconf+r1gelyrtwH@gmail.com", "iclrconf+SJx0q1rtvS@gmail.com", "iclrconf+r1xMH1BtvB@gmail.com", "iclrconf+HklXn1BKDH@gmail.com", "iclrconf+rkl8dlHYvB@gmail.com", "iclrconf+B1lDoJSYDH@gmail.com", "iclrconf+HkldyTNYwH@gmail.com", "iclrconf+S1gEIerYwH@gmail.com", "iclrconf+rkenmREFDr@gmail.com", "iclrconf+SylKikSYDH@gmail.com", "iclrconf+ByxGkySKwH@gmail.com", "iclrconf+HyxY6JHKwr@gmail.com", "iclrconf+SygpC6Ntvr@gmail.com", "iclrconf+HyxJ1xBYDH@gmail.com", "iclrconf+SJx-j64FDr@gmail.com", "iclrconf+ByxRM0Ntvr@gmail.com", "iclrconf+rJeB36NKvB@gmail.com", "iclrconf+H1enKkrFDB@gmail.com", "iclrconf+H1gBsgBYwH@gmail.com", "iclrconf+H1ebhnEYDH@gmail.com", "iclrconf+SJlpYJBKvH@gmail.com", "iclrconf+H1xscnEKDr@gmail.com", "iclrconf+H1xscnEKDr@gmail.com", "iclrconf+B1xm3RVtwB@gmail.com", "iclrconf+HJenn6VFvB@gmail.com", "iclrconf+Skgvy64tvr@gmail.com", "iclrconf+rkgbYyHtwB@gmail.com", "iclrconf+SJeqs6EFvB@gmail.com", "iclrconf+S1gFvANKDS@gmail.com", "iclrconf+B1elCp4KwH@gmail.com", "iclrconf+Hkxzx0NtDB@gmail.com", "iclrconf+ryxdEkHtPS@gmail.com", "iclrconf+r1etN1rtPB@gmail.com", "iclrconf+BJgnXpVYwS@gmail.com", "iclrconf+SJeD3CEFPH@gmail.com", "iclrconf+HJgEMpVFwB@gmail.com", "iclrconf+HkxCzeHFDB@gmail.com", "iclrconf+ryl3ygHYDB@gmail.com", "iclrconf+SJeNz04tDS@gmail.com", "iclrconf+B1lj20NFDS@gmail.com", "iclrconf+B1gHokBKwS@gmail.com", "iclrconf+HJgpugrKPS@gmail.com", "iclrconf+ByxaUgrFvH@gmail.com", "iclrconf+rkllGyBFPH@gmail.com", "iclrconf+Sye_OgHFwH@gmail.com", "iclrconf+rJlnxkSYPS@gmail.com", "iclrconf+ryebG04YvB@gmail.com", "iclrconf+rylHspEKPr@gmail.com", "iclrconf+S1g6xeSKDS@gmail.com", "iclrconf+SJlh8CEYDB@gmail.com", "iclrconf+rygGQyrFvH@gmail.com", "iclrconf+HJe_Z04Yvr@gmail.com", "iclrconf+r1lF_CEYwS@gmail.com", "iclrconf+rkeNfp4tPr@gmail.com", "iclrconf+rJeXS04FPH@gmail.com", "iclrconf+BJlZ5ySKPH@gmail.com", "iclrconf+Syx7A3NFvH@gmail.com", "iclrconf+HyxG3p4twS@gmail.com", "iclrconf+S1xKd24twB@gmail.com", "iclrconf+Skxuk1rFwB@gmail.com", "iclrconf+BJlzm64tDH@gmail.com", "iclrconf+SJg5J6NtDr@gmail.com", "iclrconf+BJgWE1SFwS@gmail.com", "iclrconf+SJgaRA4FPH@gmail.com", "iclrconf+H1exf64KwH@gmail.com", "iclrconf+rylBK34FDS@gmail.com", "iclrconf+S1lEX04tPr@gmail.com", "iclrconf+r1evOhEKvH@gmail.com", "iclrconf+HyxJhCEFDS@gmail.com", "iclrconf+B1gqipNYwH@gmail.com", "iclrconf+rJleKgrKwS@gmail.com", "iclrconf+HklQYxBKwS@gmail.com", "iclrconf+HklUCCVKDB@gmail.com", "iclrconf+BJgZGeHFPH@gmail.com", "iclrconf+rklk_ySYPB@gmail.com", "iclrconf+HJeT3yrtDr@gmail.com", "iclrconf+HJxEhREKDH@gmail.com", "iclrconf+S1l8oANFDH@gmail.com", "iclrconf+H1lhqpEYPr@gmail.com", "iclrconf+B1l4SgHKDH@gmail.com", "iclrconf+HJeqhA4YDS@gmail.com", "iclrconf+SJx0q1rtvS@gmail.com", "iclrconf+B1lnbRNtwr@gmail.com", "iclrconf+ryxmb1rKDS@gmail.com", "iclrconf+Hyg-JC4FDr@gmail.com", "iclrconf+rkl3m1BFDB@gmail.com", "iclrconf+rylvYaNYDH@gmail.com", "iclrconf+SylL0krYPS@gmail.com", "iclrconf+B1lDoJSYDH@gmail.com", "iclrconf+SylO2yStDr@gmail.com", "iclrconf+HJe6uANtwH@gmail.com", "iclrconf+B1e9Y2NYvS@gmail.com", "iclrconf+BJgy96EYvr@gmail.com", "iclrconf+Bkeb7lHtvH@gmail.com", "iclrconf+B1lPaCNtPB@gmail.com", "iclrconf+BJe55gBtvH@gmail.com", "iclrconf+BJlRs34Fvr@gmail.com", "iclrconf+rkxZyaNtwB@gmail.com", "iclrconf+HkxARkrFwB@gmail.com", "iclrconf+ryeYpJSKwr@gmail.com", "iclrconf+rkgbYyHtwB@gmail.com", "iclrconf+SJeqs6EFvB@gmail.com", "iclrconf+BkgzMCVtPB@gmail.com", "iclrconf+rkeiQlBFPB@gmail.com", "iclrconf+HJxNAnVtDS@gmail.com", "iclrconf+Bkl5kxrKDr@gmail.com", "iclrconf+B1evfa4tPB@gmail.com", "iclrconf+r1e9GCNKvH@gmail.com", "iclrconf+B1gZV1HYvS@gmail.com", "iclrconf+rygfnn4twS@gmail.com", "iclrconf+SkxxtgHKPS@gmail.com", "iclrconf+BJgQ4lSFPH@gmail.com", "iclrconf+HJgC60EtwB@gmail.com", "iclrconf+SylVNerFvr@gmail.com", "iclrconf+SkxQp1StDH@gmail.com", "iclrconf+HJgpugrKPS@gmail.com", "iclrconf+BJlahxHYDS@gmail.com", "iclrconf+BJlguT4YPr@gmail.com", "iclrconf+rJlUt0EYwS@gmail.com", "iclrconf+rkeuAhVKvB@gmail.com", "iclrconf+rygwLgrYPB@gmail.com", "iclrconf+Skxd6gSYDS@gmail.com", "iclrconf+H1lZJpVFvr@gmail.com", "iclrconf+H1loF2NFwr@gmail.com", "iclrconf+H1lmyRNFvr@gmail.com", "iclrconf+SkeFl1HKwr@gmail.com", "iclrconf+B1gF56VYPH@gmail.com", "iclrconf+rkgO66VKDS@gmail.com", "iclrconf+SJx9ngStPH@gmail.com", "iclrconf+BJgWE1SFwS@gmail.com", "iclrconf+HJxK5pEYvr@gmail.com", "iclrconf+Sye0XkBKvS@gmail.com", "iclrconf+Hye1RJHKwB@gmail.com", "iclrconf+B1x6w0EtwH@gmail.com", "iclrconf+BJgd81SYwr@gmail.com", "iclrconf+SyljQyBFDH@gmail.com", "iclrconf+rkg1ngrFPr@gmail.com", "iclrconf+SJxrKgStDH@gmail.com", "iclrconf+BygSP6Vtvr@gmail.com", "iclrconf+SyevYxHtDB@gmail.com", "iclrconf+HJe6uANtwH@gmail.com", "iclrconf+H1lK_lBtvS@gmail.com", "iclrconf+H1lmhaVtvr@gmail.com", "iclrconf+HJgCF0VFwr@gmail.com", "iclrconf+HkgH0TEYwH@gmail.com", "iclrconf+S1gEIerYwH@gmail.com", "iclrconf+rkenmREFDr@gmail.com", "iclrconf+SylKikSYDH@gmail.com", "iclrconf+ByxGkySKwH@gmail.com", "iclrconf+HyxY6JHKwr@gmail.com", "iclrconf+SygpC6Ntvr@gmail.com", "iclrconf+HyxJ1xBYDH@gmail.com", "iclrconf+SJx-j64FDr@gmail.com", "iclrconf+ByxRM0Ntvr@gmail.com", "iclrconf+rygeHgSFDH@gmail.com", "iclrconf+Hyx-jyBFPr@gmail.com", "iclrconf+SJxpsxrYPS@gmail.com", "iclrconf+HJxrVA4FDS@gmail.com", "iclrconf+rklEj2EFvB@gmail.com", "iclrconf+HJlA0C4tPS@gmail.com", "iclrconf+BygPO2VKPH@gmail.com", "iclrconf+SylkYeHtwr@gmail.com", "iclrconf+BygXFkSYDH@gmail.com", "iclrconf+Skey4eBYPS@gmail.com", "iclrconf+S1xWh1rYwB@gmail.com", "iclrconf+rklr9kHFDB@gmail.com", "iclrconf+rkgvXlrKwH@gmail.com", "iclrconf+rJxAo2VYwr@gmail.com", "iclrconf+B1l2bp4YwS@gmail.com", "iclrconf+Byg9A24tvB@gmail.com", "iclrconf+ByeUBANtvB@gmail.com", "iclrconf+ryeFY0EFwS@gmail.com", "iclrconf+H1e0Wp4KvH@gmail.com", "iclrconf+Hkx1qkrKPr@gmail.com", "iclrconf+SygXPaEYvH@gmail.com", "iclrconf+BJg1f6EFDB@gmail.com", "iclrconf+r1lPleBFvH@gmail.com", "iclrconf+S1esMkHYPr@gmail.com", "iclrconf+rkg-mA4FDr@gmail.com", "iclrconf+Hklr204Fvr@gmail.com", "iclrconf+rkgHY0NYwr@gmail.com", "iclrconf+ryxK0JBtPr@gmail.com", "iclrconf+rkgz2aEKDr@gmail.com", "iclrconf+HkePNpVKPB@gmail.com", "iclrconf+BylsKkHYvH@gmail.com", "iclrconf+r1lOgyrKDS@gmail.com", "iclrconf+SkeAaJrKDS@gmail.com", "iclrconf+HyxLRTVKPH@gmail.com", "iclrconf+rkgpv2VFvr@gmail.com", "iclrconf+rklTmyBKPH@gmail.com", "iclrconf+SkgKO0EtvS@gmail.com", "iclrconf+Bylx-TNKvH@gmail.com", "iclrconf+rkeJRhNYDH@gmail.com", "iclrconf+BJgqQ6NYvB@gmail.com", "iclrconf+HJgBA2VYwH@gmail.com", "iclrconf+r1gixp4FPH@gmail.com", "iclrconf+rJlnOhVYPS@gmail.com", "iclrconf+SygW0TEFwH@gmail.com", "iclrconf+ByglLlHFDS@gmail.com", "iclrconf+SkxybANtDB@gmail.com", "iclrconf+rJgBd2NYPH@gmail.com", "iclrconf+rkeIq2VYPr@gmail.com", "iclrconf+HyeJf1HKvS@gmail.com", "iclrconf+SklkDkSFPB@gmail.com", "iclrconf+H1xPR3NtPB@gmail.com", "iclrconf+BylA_C4tPr@gmail.com", "iclrconf+Hyl7ygStwB@gmail.com", "iclrconf+BkgWahEFvr@gmail.com", "iclrconf+ryxWIgBFPS@gmail.com", "iclrconf+BJxkOlSYDH@gmail.com", "iclrconf+ryx6WgStPB@gmail.com", "iclrconf+rygjHxrYDB@gmail.com", "iclrconf+HkgB2TNYPS@gmail.com", "iclrconf+rJx1Na4Fwr@gmail.com", "iclrconf+ByeMPlHKPH@gmail.com", "iclrconf+BJluxREKDB@gmail.com", "iclrconf+B1x6BTEKwr@gmail.com", "iclrconf+HkgxW0EYDS@gmail.com", "iclrconf+HJgcvJBFvB@gmail.com", "iclrconf+BJxI5gHKDr@gmail.com", "iclrconf+SygagpEKwB@gmail.com", "iclrconf+SJlKrkSFPH@gmail.com", "iclrconf+HJedXaEtvS@gmail.com", "iclrconf+HJgJtT4tvB@gmail.com", "iclrconf+SJgzLkBKPB@gmail.com", "iclrconf+rklbKA4YDS@gmail.com", "iclrconf+HkgsWxrtPB@gmail.com", "iclrconf+HJe_yR4Fwr@gmail.com", "iclrconf+rkgfdeBYvH@gmail.com", "iclrconf+SklD9yrFPS@gmail.com", "iclrconf+r1genAVKPB@gmail.com", "iclrconf+r1eyceSYPr@gmail.com", "iclrconf+H1l_0JBYwS@gmail.com", "iclrconf+rJljdh4KDH@gmail.com", "iclrconf+BJliakStvH@gmail.com", "iclrconf+BJeKh3VYDH@gmail.com", "iclrconf+SJxUjlBtwB@gmail.com", "iclrconf+HklSeREtPB@gmail.com", "iclrconf+BkgrBgSYDS@gmail.com", "iclrconf+rkl8sJBYvH@gmail.com", "iclrconf+S1eALyrYDH@gmail.com", "iclrconf+rkeS1RVtPS@gmail.com", "iclrconf+rkgvXlrKwH@gmail.com", "iclrconf+HkxlcnVFwB@gmail.com", "iclrconf+SJgwzCEKwH@gmail.com", "iclrconf+SJezGp4YPr@gmail.com", "iclrconf+SJleNCNtDH@gmail.com", "iclrconf+rke-f6NKvS@gmail.com", "iclrconf+HJxR7R4FvS@gmail.com", "iclrconf+r1e_FpNFDr@gmail.com", "iclrconf+rylrdxHFDr@gmail.com", "iclrconf+BJl6bANtwH@gmail.com", "iclrconf+HylpqA4FwS@gmail.com", "iclrconf+r1egIyBFPS@gmail.com", "iclrconf+S1xnXRVFwH@gmail.com", "iclrconf+BJl-5pNKDB@gmail.com", "iclrconf+SklTQCNtvS@gmail.com", "iclrconf+SJexHkSFPS@gmail.com", "iclrconf+rkgz2aEKDr@gmail.com", "iclrconf+Byg5ZANtvH@gmail.com", "iclrconf+HkePNpVKPB@gmail.com", "iclrconf+r1xCMyBtPS@gmail.com", "iclrconf+rJld3hEYvS@gmail.com", "iclrconf+H1gzR2VKDH@gmail.com", "iclrconf+r1lOgyrKDS@gmail.com", "iclrconf+SylOlp4FvH@gmail.com", "iclrconf+SkgKO0EtvS@gmail.com", "iclrconf+S1gmrxHFvB@gmail.com", "iclrconf+BkeWw6VFwr@gmail.com", "iclrconf+SygcCnNKwr@gmail.com", "iclrconf+SygKyeHKDH@gmail.com", "iclrconf+Hye_V0NKwr@gmail.com", "iclrconf+HygDF6NFPB@gmail.com", "iclrconf+SkgpBJrtvS@gmail.com", "iclrconf+r1gixp4FPH@gmail.com", "iclrconf+rJxWxxSYvB@gmail.com", "iclrconf+BJlBSkHtDS@gmail.com", "iclrconf+SkxJ8REYPH@gmail.com", "iclrconf+Syx1DkSYwB@gmail.com", "iclrconf+Byl5NREFDr@gmail.com", "iclrconf+Hkx6hANtwH@gmail.com", "iclrconf+HkxTwkrKDB@gmail.com", "iclrconf+SJg7spEYDS@gmail.com", "iclrconf+HklBjCEKvH@gmail.com", "iclrconf+SJgmR0NKPr@gmail.com", "iclrconf+BJxkOlSYDH@gmail.com", "iclrconf+Hyg96gBKPS@gmail.com", "iclrconf+HkeryxBtPB@gmail.com", "iclrconf+S1xtORNFwH@gmail.com", "iclrconf+ByeWogStDS@gmail.com", "iclrconf+Bkg0u3Etwr@gmail.com", "iclrconf+rJeW1yHYwH@gmail.com", "iclrconf+SklGryBtwr@gmail.com", "iclrconf+ByeMPlHKPH@gmail.com", "iclrconf+BJe8pkHFwS@gmail.com", "iclrconf+B1x62TNtDS@gmail.com", "iclrconf+rylXBkrYDS@gmail.com", "iclrconf+HkgxW0EYDS@gmail.com", "iclrconf+HJgcvJBFvB@gmail.com", "iclrconf+Bkxv90EKPB@gmail.com", "iclrconf+SJlsFpVtDB@gmail.com", "iclrconf+SygagpEKwB@gmail.com", "iclrconf+SJlKrkSFPH@gmail.com", "iclrconf+H1edEyBKDS@gmail.com", "iclrconf+SyxrxR4KPS@gmail.com", "iclrconf+BJliakStvH@gmail.com", "iclrconf+HJlA0C4tPS@gmail.com", "iclrconf+BygPO2VKPH@gmail.com", "iclrconf+S1eALyrYDH@gmail.com", "iclrconf+BJgNJgSFPS@gmail.com", "iclrconf+rkeZIJBYvr@gmail.com", "iclrconf+ryeFY0EFwS@gmail.com", "iclrconf+SygXPaEYvH@gmail.com", "iclrconf+Hklso24Kwr@gmail.com", "iclrconf+rylrdxHFDr@gmail.com", "iclrconf+Hklr204Fvr@gmail.com", "iclrconf+r1egIyBFPS@gmail.com", "iclrconf+rkgHY0NYwr@gmail.com", "iclrconf+HJxdTxHYvB@gmail.com", "iclrconf+r1x0lxrFPS@gmail.com", "iclrconf+ryxK0JBtPr@gmail.com", "iclrconf+BJeKwTNFvB@gmail.com", "iclrconf+rkgg6xBYDH@gmail.com", "iclrconf+SkeIyaVtwB@gmail.com", "iclrconf+HklOo0VFDH@gmail.com", "iclrconf+HyxLRTVKPH@gmail.com", "iclrconf+SJxSOJStPr@gmail.com", "iclrconf+r1lL4a4tDB@gmail.com", "iclrconf+ryenvpEKDr@gmail.com", "iclrconf+SygKyeHKDH@gmail.com", "iclrconf+rkeJRhNYDH@gmail.com", "iclrconf+BJgqQ6NYvB@gmail.com", "iclrconf+rJlnOhVYPS@gmail.com", "iclrconf+rJxtgJBKDr@gmail.com", "iclrconf+HyxnMyBKwB@gmail.com", "iclrconf+rJg76kStwH@gmail.com", "iclrconf+BkgXHTNtvS@gmail.com", "iclrconf+H1ezFREtwH@gmail.com", "iclrconf+HygsuaNFwr@gmail.com", "iclrconf+rygG4AVFvH@gmail.com", "iclrconf+H1xPR3NtPB@gmail.com", "iclrconf+BkgWahEFvr@gmail.com", "iclrconf+ryx6WgStPB@gmail.com", "iclrconf+rygjHxrYDB@gmail.com", "iclrconf+HkgB2TNYPS@gmail.com", "iclrconf+rJx1Na4Fwr@gmail.com", "iclrconf+BJe8pkHFwS@gmail.com", "iclrconf+BJluxREKDB@gmail.com", "iclrconf+HyxjOyrKvr@gmail.com", "iclrconf+B1x6BTEKwr@gmail.com", "iclrconf+Bkxv90EKPB@gmail.com", "iclrconf+BJxI5gHKDr@gmail.com", "iclrconf+H1edEyBKDS@gmail.com", "iclrconf+SJgzLkBKPB@gmail.com", "iclrconf+rklbKA4YDS@gmail.com", "iclrconf+HkgsWxrtPB@gmail.com", "iclrconf+HJe_yR4Fwr@gmail.com", "iclrconf+H1lxVyStPH@gmail.com", "iclrconf+rke7geHtwH@gmail.com", "iclrconf+HkgrZ0EYwB@gmail.com", "iclrconf+S1erpeBFPB@gmail.com", "iclrconf+rklOg6EFwS@gmail.com", "iclrconf+r1ecqn4YwB@gmail.com", "iclrconf+SJeQEp4YDH@gmail.com", "iclrconf+SJetQpEYvB@gmail.com", "iclrconf+HJg2b0VYDr@gmail.com", "iclrconf+HkxjqxBYDB@gmail.com", "iclrconf+SklD9yrFPS@gmail.com", "iclrconf+r1genAVKPB@gmail.com", "iclrconf+r1eyceSYPr@gmail.com", "iclrconf+HygOjhEYDH@gmail.com", "iclrconf+B1eWbxStPH@gmail.com", "iclrconf+H1l_0JBYwS@gmail.com", "iclrconf+Hyx-jyBFPr@gmail.com", "iclrconf+rJljdh4KDH@gmail.com", "iclrconf+SJxpsxrYPS@gmail.com", "iclrconf+HJxrVA4FDS@gmail.com", "iclrconf+SJxUjlBtwB@gmail.com", "iclrconf+HklSeREtPB@gmail.com", "iclrconf+SylkYeHtwr@gmail.com", "iclrconf+BkgrBgSYDS@gmail.com", "iclrconf+rkl8sJBYvH@gmail.com", "iclrconf+BygXFkSYDH@gmail.com", "iclrconf+Skey4eBYPS@gmail.com", "iclrconf+rkeS1RVtPS@gmail.com", "iclrconf+HkxlcnVFwB@gmail.com", "iclrconf+SJgwzCEKwH@gmail.com", "iclrconf+rJxAo2VYwr@gmail.com", "iclrconf+SJezGp4YPr@gmail.com", "iclrconf+SJleNCNtDH@gmail.com", "iclrconf+rke-f6NKvS@gmail.com", "iclrconf+H1e0Wp4KvH@gmail.com", "iclrconf+HJxR7R4FvS@gmail.com", "iclrconf+r1e_FpNFDr@gmail.com", "iclrconf+r1lPleBFvH@gmail.com", "iclrconf+BJl6bANtwH@gmail.com", "iclrconf+rkg-mA4FDr@gmail.com", "iclrconf+HylpqA4FwS@gmail.com", "iclrconf+S1xnXRVFwH@gmail.com", "iclrconf+BJl-5pNKDB@gmail.com", "iclrconf+SklTQCNtvS@gmail.com", "iclrconf+SJexHkSFPS@gmail.com", "iclrconf+HJxdTxHYvB@gmail.com", "iclrconf+Byg5ZANtvH@gmail.com", "iclrconf+r1xCMyBtPS@gmail.com", "iclrconf+rJld3hEYvS@gmail.com", "iclrconf+ByeNra4FDB@gmail.com", "iclrconf+BJeKwTNFvB@gmail.com", "iclrconf+H1gzR2VKDH@gmail.com", "iclrconf+SkeAaJrKDS@gmail.com", "iclrconf+S1gmrxHFvB@gmail.com", "iclrconf+ryenvpEKDr@gmail.com", "iclrconf+BkeWw6VFwr@gmail.com", "iclrconf+Hye_V0NKwr@gmail.com", "iclrconf+HygDF6NFPB@gmail.com", "iclrconf+SkgpBJrtvS@gmail.com", "iclrconf+HJgBA2VYwH@gmail.com", "iclrconf+Hke0V1rKPS@gmail.com", "iclrconf+rJxtgJBKDr@gmail.com", "iclrconf+SygW0TEFwH@gmail.com", "iclrconf+rJxWxxSYvB@gmail.com", "iclrconf+rJg76kStwH@gmail.com", "iclrconf+H1ezFREtwH@gmail.com", "iclrconf+SkxJ8REYPH@gmail.com", "iclrconf+rJgBd2NYPH@gmail.com", "iclrconf+rkeIq2VYPr@gmail.com", "iclrconf+Syx1DkSYwB@gmail.com", "iclrconf+Byl5NREFDr@gmail.com", "iclrconf+Hkx6hANtwH@gmail.com", "iclrconf+BylA_C4tPr@gmail.com", "iclrconf+SJg7spEYDS@gmail.com", "iclrconf+HklBjCEKvH@gmail.com", "iclrconf+SJgmR0NKPr@gmail.com", "iclrconf+Hyg96gBKPS@gmail.com", "iclrconf+HkeryxBtPB@gmail.com", "iclrconf+S1xtORNFwH@gmail.com", "iclrconf+ByeWogStDS@gmail.com", "iclrconf+Bkg0u3Etwr@gmail.com", "iclrconf+rJeW1yHYwH@gmail.com", "iclrconf+SklGryBtwr@gmail.com", "iclrconf+B1x62TNtDS@gmail.com", "iclrconf+rylXBkrYDS@gmail.com", "iclrconf+SyxrxR4KPS@gmail.com", "iclrconf+HygOjhEYDH@gmail.com", "iclrconf+B1eWbxStPH@gmail.com", "iclrconf+rygeHgSFDH@gmail.com", "iclrconf+S1e_9xrFvS@gmail.com", "iclrconf+S1e_9xrFvS@gmail.com", "iclrconf+rklEj2EFvB@gmail.com", "iclrconf+BJeKh3VYDH@gmail.com", "iclrconf+S1xWh1rYwB@gmail.com", "iclrconf+BJgNJgSFPS@gmail.com", "iclrconf+rklr9kHFDB@gmail.com", "iclrconf+rkeZIJBYvr@gmail.com", "iclrconf+B1l2bp4YwS@gmail.com", "iclrconf+Byg9A24tvB@gmail.com", "iclrconf+ByeUBANtvB@gmail.com", "iclrconf+Hkx1qkrKPr@gmail.com", "iclrconf+BJg1f6EFDB@gmail.com", "iclrconf+Hklso24Kwr@gmail.com", "iclrconf+S1esMkHYPr@gmail.com", "iclrconf+r1x0lxrFPS@gmail.com", "iclrconf+BylsKkHYvH@gmail.com", "iclrconf+ByeNra4FDB@gmail.com", "iclrconf+rkgg6xBYDH@gmail.com", "iclrconf+SkeIyaVtwB@gmail.com", "iclrconf+HklOo0VFDH@gmail.com", "iclrconf+rkgpv2VFvr@gmail.com", "iclrconf+rklTmyBKPH@gmail.com", "iclrconf+SylOlp4FvH@gmail.com", "iclrconf+SJxSOJStPr@gmail.com", "iclrconf+r1lL4a4tDB@gmail.com", "iclrconf+Bylx-TNKvH@gmail.com", "iclrconf+SygcCnNKwr@gmail.com", "iclrconf+Hke0V1rKPS@gmail.com", "iclrconf+HyxnMyBKwB@gmail.com", "iclrconf+ByglLlHFDS@gmail.com", "iclrconf+BJlBSkHtDS@gmail.com", "iclrconf+BkgXHTNtvS@gmail.com", "iclrconf+SkxybANtDB@gmail.com", "iclrconf+HygsuaNFwr@gmail.com", "iclrconf+rygG4AVFvH@gmail.com", "iclrconf+HyeJf1HKvS@gmail.com", "iclrconf+SklkDkSFPB@gmail.com", "iclrconf+HkxTwkrKDB@gmail.com", "iclrconf+Hyl7ygStwB@gmail.com", "iclrconf+ryxWIgBFPS@gmail.com", "iclrconf+HyxjOyrKvr@gmail.com", "iclrconf+SJlsFpVtDB@gmail.com", "iclrconf+HJedXaEtvS@gmail.com", "iclrconf+HJgJtT4tvB@gmail.com", "iclrconf+H1lxVyStPH@gmail.com", "iclrconf+rkgfdeBYvH@gmail.com", "iclrconf+rke7geHtwH@gmail.com", "iclrconf+HkgrZ0EYwB@gmail.com", "iclrconf+S1erpeBFPB@gmail.com", "iclrconf+rklOg6EFwS@gmail.com", "iclrconf+r1ecqn4YwB@gmail.com", "iclrconf+SJeQEp4YDH@gmail.com", "iclrconf+SJetQpEYvB@gmail.com", "iclrconf+HJg2b0VYDr@gmail.com", "iclrconf+HkxjqxBYDB@gmail.com", "iclrconf+HyevIJStwH@gmail.com", "iclrconf+BJxsrgStvr@gmail.com", "iclrconf+Hke-WTVtwr@gmail.com", "iclrconf+ByeGzlrKwH@gmail.com", "iclrconf+S1ldO2EFPr@gmail.com", "iclrconf+BJg866NFvB@gmail.com", "iclrconf+S1xCPJHtDB@gmail.com", "iclrconf+SkeyppEFvS@gmail.com", "iclrconf+SJgndT4KwB@gmail.com", "iclrconf+SJgndT4KwB@gmail.com", "iclrconf+BkgYPREtPr@gmail.com", "iclrconf+rkg6sJHYDr@gmail.com", "iclrconf+SJeLIgBKPS@gmail.com", "iclrconf+rkgNKkHtvB@gmail.com", "iclrconf+ryghZJBKPS@gmail.com", "iclrconf+ByxtC2VtPB@gmail.com", "iclrconf+rJx4p3NYDB@gmail.com", "iclrconf+HkgaETNtDB@gmail.com", "iclrconf+HklxbgBKvr@gmail.com", "iclrconf+SklOUpEYvB@gmail.com", "iclrconf+Bke89JBtvB@gmail.com", "iclrconf+BkxfaTVFwH@gmail.com", "iclrconf+ryxQuANKPB@gmail.com", "iclrconf+Hkx7_1rKwS@gmail.com", "iclrconf+BygFVAEKDH@gmail.com", "iclrconf+BJl2_nVFPB@gmail.com", "iclrconf+BkepbpNFwr@gmail.com", "iclrconf+rJeQoCNYDS@gmail.com", "iclrconf+S1g8K1BFwS@gmail.com", "iclrconf+ByxQB1BKwH@gmail.com", "iclrconf+HJlnC1rKPB@gmail.com", "iclrconf+Byx4NkrtDS@gmail.com", "iclrconf+H1eCw3EKvH@gmail.com", "iclrconf+rke2P1BFwS@gmail.com", "iclrconf+SyxV9ANFDH@gmail.com", "iclrconf+B1gX8kBtPr@gmail.com", "iclrconf+rJe4_xSFDB@gmail.com", "iclrconf+rJgQkT4twH@gmail.com", "iclrconf+SklKcRNYDH@gmail.com", "iclrconf+SJxhNTNYwB@gmail.com", "iclrconf+rylVHR4FPB@gmail.com", "iclrconf+B1xIj3VYvr@gmail.com", "iclrconf+H1laeJrKDB@gmail.com", "iclrconf+H1gX8C4YPr@gmail.com", "iclrconf+BJeS62EtwH@gmail.com", "iclrconf+HkgsPhNYPS@gmail.com", "iclrconf+rkxoh24FPH@gmail.com", "iclrconf+HygpthEtvr@gmail.com", "iclrconf+SkgGCkrKvH@gmail.com", "iclrconf+SJxbHkrKDH@gmail.com", "iclrconf+HJem3yHKwH@gmail.com", "iclrconf+ryxgsCVYPr@gmail.com", "iclrconf+rylJkpEtwS@gmail.com", "iclrconf+S1eRbANtDB@gmail.com", "iclrconf+H1gfFaEYDS@gmail.com", "iclrconf+SJgVU0EKwS@gmail.com", "iclrconf+rkl03ySYDH@gmail.com", "iclrconf+ryxyCeHtPB@gmail.com", "iclrconf+rylb3eBtwr@gmail.com", "iclrconf+ByexElSYDr@gmail.com", "iclrconf+SJxzFySKwH@gmail.com", "iclrconf+B1eyO1BFPr@gmail.com", "iclrconf+rklB76EKPr@gmail.com", "iclrconf+SJem8lSFwB@gmail.com", "iclrconf+Hkl1iRNFwS@gmail.com", "iclrconf+BJewlyStDr@gmail.com", "iclrconf+ryeG924twB@gmail.com", "iclrconf+H1lNPxHKDH@gmail.com", "iclrconf+BJg4NgBKvH@gmail.com", "iclrconf+H1ldzA4tPr@gmail.com", "iclrconf+HklRwaEKwB@gmail.com", "iclrconf+S1e4jkSKvB@gmail.com", "iclrconf+Sklgs0NFvr@gmail.com", "iclrconf+HyxyIgHFvr@gmail.com", "iclrconf+ryxjnREFwH@gmail.com", "iclrconf+BJg866NFvB@gmail.com", "iclrconf+S1xCPJHtDB@gmail.com", "iclrconf+Syx79eBKwr@gmail.com", "iclrconf+S1lOTC4tDS@gmail.com", "iclrconf+Hkx7xRVYDr@gmail.com", "iclrconf+rJg8TeSFDH@gmail.com", "iclrconf+HkxYzANYDB@gmail.com", "iclrconf+rJgJDAVKvB@gmail.com", "iclrconf+S1g2skStPB@gmail.com", "iclrconf+rkg6sJHYDr@gmail.com", "iclrconf+rygixkHKDH@gmail.com", "iclrconf+Ske31kBtPr@gmail.com", "iclrconf+BJlQtJSKDB@gmail.com", "iclrconf+rklHqRVKvH@gmail.com", "iclrconf+HJgzt2VKPB@gmail.com", "iclrconf+BkxpMTEtPB@gmail.com", "iclrconf+SkxSv6VFvS@gmail.com", "iclrconf+rkgMkCEtPB@gmail.com", "iclrconf+HklxbgBKvr@gmail.com", "iclrconf+BJxG_0EtDS@gmail.com", "iclrconf+ByxT7TNFvH@gmail.com", "iclrconf+BkxfaTVFwH@gmail.com", "iclrconf+HJlSmC4FPS@gmail.com", "iclrconf+SJeYe0NtvH@gmail.com", "iclrconf+rke3TJrtPS@gmail.com", "iclrconf+B1gskyStwr@gmail.com", "iclrconf+Skgy464Kvr@gmail.com", "iclrconf+BJe1334YDH@gmail.com", "iclrconf+rkecJ6VFvr@gmail.com", "iclrconf+BkepbpNFwr@gmail.com", "iclrconf+r1xGP6VYwH@gmail.com", "iclrconf+BJx040EFvH@gmail.com", "iclrconf+HkgsUJrtDB@gmail.com", "iclrconf+Bkeeca4Kvr@gmail.com", "iclrconf+Skln2A4YDB@gmail.com", "iclrconf+HJli2hNKDH@gmail.com", "iclrconf+ryxnY3NYPS@gmail.com", "iclrconf+rkxawlHKDr@gmail.com", "iclrconf+S1lxKlSKPH@gmail.com", "iclrconf+H1lBj2VFPS@gmail.com", "iclrconf+rkem91rtDB@gmail.com", "iclrconf+S1l-C0NtwS@gmail.com", "iclrconf+rklp93EtwH@gmail.com", "iclrconf+Syx4wnEtvH@gmail.com", "iclrconf+Skl4mRNYDr@gmail.com", "iclrconf+SkeHuCVFDr@gmail.com", "iclrconf+rkgOlCVYvB@gmail.com", "iclrconf+Byx_YAVYPH@gmail.com", "iclrconf+HJgfDREKDB@gmail.com", "iclrconf+ByxY8CNtvr@gmail.com", "iclrconf+BylEqnVFDB@gmail.com", "iclrconf+S1eRbANtDB@gmail.com", "iclrconf+Sklf1yrYDr@gmail.com", "iclrconf+BJxVI04YvB@gmail.com", "iclrconf+HJgLLyrYwB@gmail.com", "iclrconf+BJedHRVtPB@gmail.com", "iclrconf+BJxt60VtPr@gmail.com", "iclrconf+H1emfT4twB@gmail.com", "iclrconf+BygdyxHFDS@gmail.com", "iclrconf+BJxWx0NYPr@gmail.com", "iclrconf+HJx8HANFDH@gmail.com", "iclrconf+HkxBJT4YvB@gmail.com", "iclrconf+SJx1URNKwH@gmail.com", "iclrconf+SJgMK64Ywr@gmail.com", "iclrconf+HJgSwyBKvr@gmail.com", "iclrconf+BJeGlJStPr@gmail.com", "iclrconf+rylb3eBtwr@gmail.com", "iclrconf+SJgVHkrYDH@gmail.com", "iclrconf+B1eY_pVYvB@gmail.com", "iclrconf+SkeuexBtDr@gmail.com", "iclrconf+BkxUvnEYDH@gmail.com", "iclrconf+BJxsrgStvr@gmail.com", "iclrconf+Syx79eBKwr@gmail.com", "iclrconf+rJxbJeHFPS@gmail.com", "iclrconf+SJeLIgBKPS@gmail.com", "iclrconf+r1eBeyHFDH@gmail.com", "iclrconf+rkgNKkHtvB@gmail.com", "iclrconf+rJx4p3NYDB@gmail.com", "iclrconf+HkgaETNtDB@gmail.com", "iclrconf+ryxQuANKPB@gmail.com", "iclrconf+Hkx7_1rKwS@gmail.com", "iclrconf+HklkeR4KPB@gmail.com", "iclrconf+HygnDhEtvr@gmail.com", "iclrconf+BJe1334YDH@gmail.com", "iclrconf+rkecJ6VFvr@gmail.com", "iclrconf+BJl2_nVFPB@gmail.com", "iclrconf+HkejNgBtPB@gmail.com", "iclrconf+H1guaREYPr@gmail.com", "iclrconf+B1l6y0VFPr@gmail.com", "iclrconf+HkgsUJrtDB@gmail.com", "iclrconf+Skgxcn4YDS@gmail.com", "iclrconf+SklKcRNYDH@gmail.com", "iclrconf+SJxhNTNYwB@gmail.com", "iclrconf+B1xIj3VYvr@gmail.com", "iclrconf+rkxawlHKDr@gmail.com", "iclrconf+HJeO7RNKPr@gmail.com", "iclrconf+H1gX8C4YPr@gmail.com", "iclrconf+rkxxA24FDr@gmail.com", "iclrconf+ryxOUTVYDH@gmail.com", "iclrconf+H1lBj2VFPS@gmail.com", "iclrconf+Hkem-lrtvH@gmail.com", "iclrconf+HJl8_eHYvS@gmail.com", "iclrconf+r1eowANFvr@gmail.com", "iclrconf+SJxDDpEKvH@gmail.com", "iclrconf+SJxbHkrKDH@gmail.com", "iclrconf+HkgeGeBYDB@gmail.com", "iclrconf+BJxwPJHFwS@gmail.com", "iclrconf+SJgMK64Ywr@gmail.com", "iclrconf+BJeGlJStPr@gmail.com", "iclrconf+SJgVHkrYDH@gmail.com", "iclrconf+B1eY_pVYvB@gmail.com", "iclrconf+BJgMFxrYPB@gmail.com", "iclrconf+ByexElSYDr@gmail.com", "iclrconf+SJxzFySKwH@gmail.com", "iclrconf+rkevSgrtPr@gmail.com", "iclrconf+B1eyO1BFPr@gmail.com", "iclrconf+rklB76EKPr@gmail.com", "iclrconf+Hkl1iRNFwS@gmail.com", "iclrconf+ryeG924twB@gmail.com", "iclrconf+SJlVY04FwH@gmail.com", "iclrconf+H1lNPxHKDH@gmail.com", "iclrconf+SygWvAVFPr@gmail.com", "iclrconf+H1e_cC4twS@gmail.com", "iclrconf+SkeuexBtDr@gmail.com", "iclrconf+H1ldzA4tPr@gmail.com", "iclrconf+HklRwaEKwB@gmail.com", "iclrconf+HyevIJStwH@gmail.com", "iclrconf+S1e4jkSKvB@gmail.com", "iclrconf+Sklgs0NFvr@gmail.com", "iclrconf+HyxyIgHFvr@gmail.com", "iclrconf+ryxjnREFwH@gmail.com", "iclrconf+BkgYPREtPr@gmail.com", "iclrconf+S1eZYeHFDS@gmail.com", "iclrconf+S1lOTC4tDS@gmail.com", "iclrconf+Hkx7xRVYDr@gmail.com", "iclrconf+rJg8TeSFDH@gmail.com", "iclrconf+HkxYzANYDB@gmail.com", "iclrconf+rJgJDAVKvB@gmail.com", "iclrconf+rJxbJeHFPS@gmail.com", "iclrconf+rygixkHKDH@gmail.com", "iclrconf+Ske31kBtPr@gmail.com", "iclrconf+BJlQtJSKDB@gmail.com", "iclrconf+rklHqRVKvH@gmail.com", "iclrconf+ryghZJBKPS@gmail.com", "iclrconf+SJe5P6EYvS@gmail.com", "iclrconf+HJgzt2VKPB@gmail.com", "iclrconf+Hyl9xxHYPr@gmail.com", "iclrconf+BkxpMTEtPB@gmail.com", "iclrconf+SkxSv6VFvS@gmail.com", "iclrconf+rkgMkCEtPB@gmail.com", "iclrconf+BJxG_0EtDS@gmail.com", "iclrconf+rkxDoJBYPB@gmail.com", "iclrconf+ByxT7TNFvH@gmail.com", "iclrconf+HJlSmC4FPS@gmail.com", "iclrconf+SJeYe0NtvH@gmail.com", "iclrconf+rke3TJrtPS@gmail.com", "iclrconf+B1gskyStwr@gmail.com", "iclrconf+Skgy464Kvr@gmail.com", "iclrconf+rJeQoCNYDS@gmail.com", "iclrconf+r1xGP6VYwH@gmail.com", "iclrconf+S1g8K1BFwS@gmail.com", "iclrconf+BJx040EFvH@gmail.com", "iclrconf+ByxQB1BKwH@gmail.com", "iclrconf+Byx4NkrtDS@gmail.com", "iclrconf+B1gX8kBtPr@gmail.com", "iclrconf+rJe4_xSFDB@gmail.com", "iclrconf+Skln2A4YDB@gmail.com", "iclrconf+SkxBUpEKwH@gmail.com", "iclrconf+HJli2hNKDH@gmail.com", "iclrconf+rylVHR4FPB@gmail.com", "iclrconf+ryxnY3NYPS@gmail.com", "iclrconf+S1lxKlSKPH@gmail.com", "iclrconf+Hkem-lrtvH@gmail.com", "iclrconf+rkem91rtDB@gmail.com", "iclrconf+S1l-C0NtwS@gmail.com", "iclrconf+SJxDDpEKvH@gmail.com", "iclrconf+rklp93EtwH@gmail.com", "iclrconf+Syx4wnEtvH@gmail.com", "iclrconf+Skl4mRNYDr@gmail.com", "iclrconf+SkeHuCVFDr@gmail.com", "iclrconf+rkgOlCVYvB@gmail.com", "iclrconf+Byx_YAVYPH@gmail.com", "iclrconf+HJgfDREKDB@gmail.com", "iclrconf+ByxY8CNtvr@gmail.com", "iclrconf+HJem3yHKwH@gmail.com", "iclrconf+BylEqnVFDB@gmail.com", "iclrconf+Sklf1yrYDr@gmail.com", "iclrconf+BJxVI04YvB@gmail.com", "iclrconf+H1gfFaEYDS@gmail.com", "iclrconf+HJgLLyrYwB@gmail.com", "iclrconf+BJedHRVtPB@gmail.com", "iclrconf+BJxt60VtPr@gmail.com", "iclrconf+H1emfT4twB@gmail.com", "iclrconf+BygdyxHFDS@gmail.com", "iclrconf+SJgVU0EKwS@gmail.com", "iclrconf+rkl03ySYDH@gmail.com", "iclrconf+HJx8HANFDH@gmail.com", "iclrconf+HkxBJT4YvB@gmail.com", "iclrconf+BkxUvnEYDH@gmail.com", "iclrconf+Hke-WTVtwr@gmail.com", "iclrconf+ByeGzlrKwH@gmail.com", "iclrconf+S1ldO2EFPr@gmail.com", "iclrconf+SkeyppEFvS@gmail.com", "iclrconf+S1eZYeHFDS@gmail.com", "iclrconf+S1g2skStPB@gmail.com", "iclrconf+r1eBeyHFDH@gmail.com", "iclrconf+SJe5P6EYvS@gmail.com", "iclrconf+Hyl9xxHYPr@gmail.com", "iclrconf+ByxtC2VtPB@gmail.com", "iclrconf+SklOUpEYvB@gmail.com", "iclrconf+Bke89JBtvB@gmail.com", "iclrconf+rkxDoJBYPB@gmail.com", "iclrconf+HklkeR4KPB@gmail.com", "iclrconf+HygnDhEtvr@gmail.com", "iclrconf+BygFVAEKDH@gmail.com", "iclrconf+HkejNgBtPB@gmail.com", "iclrconf+H1guaREYPr@gmail.com", "iclrconf+HJlnC1rKPB@gmail.com", "iclrconf+B1l6y0VFPr@gmail.com", "iclrconf+H1eCw3EKvH@gmail.com", "iclrconf+rke2P1BFwS@gmail.com", "iclrconf+SyxV9ANFDH@gmail.com", "iclrconf+Bkeeca4Kvr@gmail.com", "iclrconf+Skgxcn4YDS@gmail.com", "iclrconf+rJgQkT4twH@gmail.com", "iclrconf+SkxBUpEKwH@gmail.com", "iclrconf+HJeO7RNKPr@gmail.com", "iclrconf+H1laeJrKDB@gmail.com", "iclrconf+rkxxA24FDr@gmail.com", "iclrconf+BJeS62EtwH@gmail.com", "iclrconf+ryxOUTVYDH@gmail.com", "iclrconf+HkgsPhNYPS@gmail.com", "iclrconf+rkxoh24FPH@gmail.com", "iclrconf+HJl8_eHYvS@gmail.com", "iclrconf+HygpthEtvr@gmail.com", "iclrconf+r1eowANFvr@gmail.com", "iclrconf+SkgGCkrKvH@gmail.com", "iclrconf+ryxgsCVYPr@gmail.com", "iclrconf+rylJkpEtwS@gmail.com", "iclrconf+HkgeGeBYDB@gmail.com", "iclrconf+ryxyCeHtPB@gmail.com", "iclrconf+BJxWx0NYPr@gmail.com", "iclrconf+BJxwPJHFwS@gmail.com", "iclrconf+SJx1URNKwH@gmail.com", "iclrconf+HJgSwyBKvr@gmail.com", "iclrconf+BJgMFxrYPB@gmail.com", "iclrconf+rkevSgrtPr@gmail.com", "iclrconf+SJem8lSFwB@gmail.com", "iclrconf+BJewlyStDr@gmail.com", "iclrconf+SJlVY04FwH@gmail.com", "iclrconf+BJg4NgBKvH@gmail.com", "iclrconf+SygWvAVFPr@gmail.com", "iclrconf+H1e_cC4twS@gmail.com", "iclrconf+SJgwNerKvB@gmail.com", "iclrconf+r1g87C4KwB@gmail.com", "iclrconf+H1gNOeHKPS@gmail.com", "iclrconf+Byl8hhNYPS@gmail.com", "iclrconf+B1e3OlStPB@gmail.com", "iclrconf+S1e2agrFvS@gmail.com", "iclrconf+BJxSI1SKDH@gmail.com", "iclrconf+BJlS634tPr@gmail.com", "iclrconf+HJeTo2VFwH@gmail.com", "iclrconf+rJehVyrKwH@gmail.com", "iclrconf+HkxQRTNYPH@gmail.com", "iclrconf+BkluqlSFDS@gmail.com", "iclrconf+H1gax6VtDB@gmail.com", "iclrconf+BJlrF24twB@gmail.com", "iclrconf+r1lGO0EKDH@gmail.com", "iclrconf+BJeB5hVtvB@gmail.com", "iclrconf+HylAoJSKvH@gmail.com", "iclrconf+HkxdQkSYDB@gmail.com", "iclrconf+rJeqeCEtvH@gmail.com", "iclrconf+rJgUfTEYvH@gmail.com", "iclrconf+HJx81ySKwr@gmail.com", "iclrconf+B1l8L6EtDS@gmail.com", "iclrconf+r1gRTCVFvB@gmail.com", "iclrconf+r1xPh2VtPB@gmail.com", "iclrconf+r1eIiCNYwS@gmail.com", "iclrconf+HygrdpVKvr@gmail.com", "iclrconf+HJeiDpVFPr@gmail.com", "iclrconf+rkecl1rtwB@gmail.com", "iclrconf+Hygab1rKDS@gmail.com", "iclrconf+BJe-91BtvH@gmail.com", "iclrconf+HJgExaVtwr@gmail.com", "iclrconf+rJeINp4KwH@gmail.com", "iclrconf+rJxycxHKDS@gmail.com", "iclrconf+rJl31TNYPr@gmail.com", "iclrconf+Hyg9anEFPS@gmail.com", "iclrconf+Bke_DertPB@gmail.com", "iclrconf+H1lj0nNFwB@gmail.com", "iclrconf+SJlHwkBYDH@gmail.com", "iclrconf+rJxlc0EtDr@gmail.com", "iclrconf+rkgU1gHtvr@gmail.com", "iclrconf+B1guLAVFDB@gmail.com", "iclrconf+Bke61krFvS@gmail.com", "iclrconf+rkxs0yHFPH@gmail.com", "iclrconf+rkgyS0VFvr@gmail.com", "iclrconf+HyeYTgrFPB@gmail.com", "iclrconf+S1xFl64tDr@gmail.com", "iclrconf+SyxIWpVYvr@gmail.com", "iclrconf+S1lSapVtwS@gmail.com", "iclrconf+H1gBhkBFDH@gmail.com", "iclrconf+B1eWOJHKvB@gmail.com", "iclrconf+SkgGjRVKDS@gmail.com", "iclrconf+SJxWS64FwH@gmail.com", "iclrconf+rJgzzJHtDB@gmail.com", "iclrconf+ryxgJTEYDr@gmail.com", "iclrconf+r1gdj2EKPB@gmail.com", "iclrconf+SyxhVkrYvr@gmail.com", "iclrconf+SyxL2TNtvr@gmail.com", "iclrconf+Sye57xStvB@gmail.com", "iclrconf+SJeq9JBFvH@gmail.com", "iclrconf+r1eiu2VtwH@gmail.com", "iclrconf+B1eB5xSFvr@gmail.com", "iclrconf+BylQSxHFwr@gmail.com", "iclrconf+rylnK6VtDH@gmail.com", "iclrconf+HyebplHYwB@gmail.com", "iclrconf+B1esx6EYvr@gmail.com", "iclrconf+rygjmpVFvB@gmail.com", "iclrconf+rylwJxrYDS@gmail.com", "iclrconf+HJx-3grYDB@gmail.com", "iclrconf+Hkl9JlBYvr@gmail.com", "iclrconf+HyeaSkrYPH@gmail.com", "iclrconf+H1eqQeHFDS@gmail.com", "iclrconf+BJl07ySKvS@gmail.com", "iclrconf+HJlWWJSFDH@gmail.com", "iclrconf+rkeu30EtvS@gmail.com", "iclrconf+BkxRRkSKwr@gmail.com", "iclrconf+BJge3TNKwH@gmail.com", "iclrconf+BkevoJSYPB@gmail.com", "iclrconf+BygzbyHFvB@gmail.com", "iclrconf+H1xFWgrFPS@gmail.com", "iclrconf+Hkekl0NFPr@gmail.com", "iclrconf+Hklz71rYvS@gmail.com", "iclrconf+B1gdkxHFDH@gmail.com", "iclrconf+SJl5Np4tPr@gmail.com", "iclrconf+rJehVyrKwH@gmail.com", "iclrconf+H1gDNyrKDS@gmail.com", "iclrconf+BJeAHkrYDS@gmail.com", "iclrconf+S1gSj0NKvB@gmail.com", "iclrconf+H1lma24tPB@gmail.com", "iclrconf+HJgLZR4KvH@gmail.com", "iclrconf+H1gax6VtDB@gmail.com", "iclrconf+SJxstlHFPH@gmail.com", "iclrconf+rJxGLlBtwH@gmail.com", "iclrconf+rJeqeCEtvH@gmail.com", "iclrconf+HJeVnCEKwH@gmail.com", "iclrconf+B1e-kxSKDH@gmail.com", "iclrconf+SJgIPJBFvH@gmail.com", "iclrconf+ryx1wRNFvB@gmail.com", "iclrconf+SkxgnnNFvH@gmail.com", "iclrconf+Byg-wJSYDS@gmail.com", "iclrconf+Byg1v1HKDB@gmail.com", "iclrconf+HJeiDpVFPr@gmail.com", "iclrconf+H1gB4RVKvB@gmail.com", "iclrconf+rkg-TJBFPB@gmail.com", "iclrconf+rye5YaEtPr@gmail.com", "iclrconf+BJe-91BtvH@gmail.com", "iclrconf+rJeg7TEYwB@gmail.com", "iclrconf+rygFWAEFwS@gmail.com", "iclrconf+Skx82ySYPH@gmail.com", "iclrconf+rJxX8T4Kvr@gmail.com", "iclrconf+S1exA2NtDB@gmail.com", "iclrconf+HJepXaVYDr@gmail.com", "iclrconf+SJxIm0VtwH@gmail.com", "iclrconf+rJxlc0EtDr@gmail.com", "iclrconf+B1lLw6EYwB@gmail.com", "iclrconf+rkxs0yHFPH@gmail.com", "iclrconf+HyeYTgrFPB@gmail.com", "iclrconf+BJxg_hVtwH@gmail.com", "iclrconf+ryloogSKDS@gmail.com", "iclrconf+S1g7tpEYDS@gmail.com", "iclrconf+HJxMYANtPH@gmail.com", "iclrconf+SylzhkBtDB@gmail.com", "iclrconf+BkeoaeHKDS@gmail.com", "iclrconf+Hke3gyHYwH@gmail.com", "iclrconf+B1lJzyStvS@gmail.com", "iclrconf+BkgnhTEtDS@gmail.com", "iclrconf+SJg7KhVKPH@gmail.com", "iclrconf+r1laNeBYPB@gmail.com", "iclrconf+ryxGuJrFvS@gmail.com", "iclrconf+B1xwcyHFDr@gmail.com", "iclrconf+ryxB2lBtvH@gmail.com", "iclrconf+HylsTT4FvB@gmail.com", "iclrconf+Hye1kTVFDS@gmail.com", "iclrconf+SkgC6TNFvr@gmail.com", "iclrconf+HygegyrYwH@gmail.com", "iclrconf+r1xGnA4Kvr@gmail.com", "iclrconf+rJgqMRVYvr@gmail.com", "iclrconf+B1xSperKvH@gmail.com", "iclrconf+S1ltg1rFDS@gmail.com", "iclrconf+HylxE1HKwS@gmail.com", "iclrconf+SkgsACVKPH@gmail.com", "iclrconf+Sye57xStvB@gmail.com", "iclrconf+BJgr4kSFDS@gmail.com", "iclrconf+HkgTTh4FDH@gmail.com", "iclrconf+BJgza6VtPB@gmail.com", "iclrconf+HJlfuTEtvB@gmail.com", "iclrconf+ryeHuJBtPH@gmail.com", "iclrconf+BJgQfkSYDS@gmail.com", "iclrconf+HJlWWJSFDH@gmail.com", "iclrconf+r1g87C4KwB@gmail.com", "iclrconf+rkeu30EtvS@gmail.com", "iclrconf+Byl8hhNYPS@gmail.com", "iclrconf+r1lZ7AEKvB@gmail.com", "iclrconf+HJxyZkBKDr@gmail.com", "iclrconf+HJxyZkBKDr@gmail.com", "iclrconf+BJlS634tPr@gmail.com", "iclrconf+H1eA7AEtvS@gmail.com", "iclrconf+Hke0K1HKwr@gmail.com", "iclrconf+S1efxTVYDr@gmail.com", "iclrconf+H1gDNyrKDS@gmail.com", "iclrconf+BkluqlSFDS@gmail.com", "iclrconf+H1lma24tPB@gmail.com", "iclrconf+rJxGLlBtwH@gmail.com", "iclrconf+rkgt0REKwS@gmail.com", "iclrconf+HkxdQkSYDB@gmail.com", "iclrconf+SkxLFaNKwB@gmail.com", "iclrconf+r1gRTCVFvB@gmail.com", "iclrconf+HJezF3VYPB@gmail.com", "iclrconf+SJxZnR4YvB@gmail.com", "iclrconf+BkglSTNFDB@gmail.com", "iclrconf+HJeOekHKwr@gmail.com", "iclrconf+SJlbGJrtDB@gmail.com", "iclrconf+r1eIiCNYwS@gmail.com", "iclrconf+HJlxIJBFDr@gmail.com", "iclrconf+rkecl1rtwB@gmail.com", "iclrconf+SJgob6NKvH@gmail.com", "iclrconf+ByedzkrKvH@gmail.com", "iclrconf+rJeg7TEYwB@gmail.com", "iclrconf+HJgExaVtwr@gmail.com", "iclrconf+rJeINp4KwH@gmail.com", "iclrconf+Bkxe2AVtPS@gmail.com", "iclrconf+rJl31TNYPr@gmail.com", "iclrconf+rJxX8T4Kvr@gmail.com", "iclrconf+ryg48p4tPH@gmail.com", "iclrconf+HJloElBYvB@gmail.com", "iclrconf+BylVcTNtDS@gmail.com", "iclrconf+BJxH22EKPS@gmail.com", "iclrconf+rkgyS0VFvr@gmail.com", "iclrconf+BkgXT24tDS@gmail.com", "iclrconf+rkeIIkHKvS@gmail.com", "iclrconf+B1xMEerYvB@gmail.com", "iclrconf+rJxe3xSYDS@gmail.com", "iclrconf+Bke8UR4FPB@gmail.com", "iclrconf+rJeIcTNtvS@gmail.com", "iclrconf+rJgzzJHtDB@gmail.com", "iclrconf+ryxB2lBtvH@gmail.com", "iclrconf+SJeLopEYDH@gmail.com", "iclrconf+r1gdj2EKPB@gmail.com", "iclrconf+H1gmHaEKwB@gmail.com", "iclrconf+HyxjNyrtPr@gmail.com", "iclrconf+BJgr4kSFDS@gmail.com", "iclrconf+SJeY-1BKDS@gmail.com", "iclrconf+BylQSxHFwr@gmail.com", "iclrconf+rylmoxrFDH@gmail.com", "iclrconf+BkxSmlBFvr@gmail.com", "iclrconf+B1esx6EYvr@gmail.com", "iclrconf+SJlRUkrFPS@gmail.com", "iclrconf+rkgAGAVKPr@gmail.com", "iclrconf+H1eqQeHFDS@gmail.com", "iclrconf+SJgwNerKvB@gmail.com", "iclrconf+BkxRRkSKwr@gmail.com", "iclrconf+BJge3TNKwH@gmail.com", "iclrconf+BygzbyHFvB@gmail.com", "iclrconf+H1xFWgrFPS@gmail.com", "iclrconf+Hkekl0NFPr@gmail.com", "iclrconf+B1gdkxHFDH@gmail.com", "iclrconf+SJl5Np4tPr@gmail.com", "iclrconf+r1lfF2NYvH@gmail.com", "iclrconf+ByxxgCEYDS@gmail.com", "iclrconf+ByxxgCEYDS@gmail.com", "iclrconf+BJeAHkrYDS@gmail.com", "iclrconf+S1gSj0NKvB@gmail.com", "iclrconf+HJgLZR4KvH@gmail.com", "iclrconf+BJlrF24twB@gmail.com", "iclrconf+r1lGO0EKDH@gmail.com", "iclrconf+SJxstlHFPH@gmail.com", "iclrconf+BJeB5hVtvB@gmail.com", "iclrconf+rJgUfTEYvH@gmail.com", "iclrconf+HJeVnCEKwH@gmail.com", "iclrconf+r1xPh2VtPB@gmail.com", "iclrconf+HJezF3VYPB@gmail.com", "iclrconf+SJgIPJBFvH@gmail.com", "iclrconf+ryx1wRNFvB@gmail.com", "iclrconf+SkxgnnNFvH@gmail.com", "iclrconf+Byg-wJSYDS@gmail.com", "iclrconf+HygrdpVKvr@gmail.com", "iclrconf+Byg1v1HKDB@gmail.com", "iclrconf+SJgob6NKvH@gmail.com", "iclrconf+H1gB4RVKvB@gmail.com", "iclrconf+rkg-TJBFPB@gmail.com", "iclrconf+Bkxe2AVtPS@gmail.com", "iclrconf+rygFWAEFwS@gmail.com", "iclrconf+Skx82ySYPH@gmail.com", "iclrconf+S1exA2NtDB@gmail.com", "iclrconf+HJepXaVYDr@gmail.com", "iclrconf+SJxIm0VtwH@gmail.com", "iclrconf+ByxdUySKvS@gmail.com", "iclrconf+rkgU1gHtvr@gmail.com", "iclrconf+B1guLAVFDB@gmail.com", "iclrconf+B1lLw6EYwB@gmail.com", "iclrconf+B1xMEerYvB@gmail.com", "iclrconf+BJxg_hVtwH@gmail.com", "iclrconf+ryloogSKDS@gmail.com", "iclrconf+S1g7tpEYDS@gmail.com", "iclrconf+HJxMYANtPH@gmail.com", "iclrconf+SylzhkBtDB@gmail.com", "iclrconf+BkeoaeHKDS@gmail.com", "iclrconf+Hke3gyHYwH@gmail.com", "iclrconf+B1lJzyStvS@gmail.com", "iclrconf+rklnDgHtDS@gmail.com", "iclrconf+BkgnhTEtDS@gmail.com", "iclrconf+SJg7KhVKPH@gmail.com", "iclrconf+r1laNeBYPB@gmail.com", "iclrconf+ryxGuJrFvS@gmail.com", "iclrconf+SJeLopEYDH@gmail.com", "iclrconf+HylsTT4FvB@gmail.com", "iclrconf+ryxgJTEYDr@gmail.com", "iclrconf+Hye1kTVFDS@gmail.com", "iclrconf+SkgC6TNFvr@gmail.com", "iclrconf+HygegyrYwH@gmail.com", "iclrconf+r1xGnA4Kvr@gmail.com", "iclrconf+rJgqMRVYvr@gmail.com", "iclrconf+B1xSperKvH@gmail.com", "iclrconf+S1ltg1rFDS@gmail.com", "iclrconf+HylxE1HKwS@gmail.com", "iclrconf+SkgsACVKPH@gmail.com", "iclrconf+SyxL2TNtvr@gmail.com", "iclrconf+HkgTTh4FDH@gmail.com", "iclrconf+BJgza6VtPB@gmail.com", "iclrconf+HJlfuTEtvB@gmail.com", "iclrconf+rkxNh1Stvr@gmail.com", "iclrconf+ryeHuJBtPH@gmail.com", "iclrconf+BJgQfkSYDS@gmail.com", "iclrconf+B1eB5xSFvr@gmail.com", "iclrconf+H1gNOeHKPS@gmail.com", "iclrconf+r1lZ7AEKvB@gmail.com", "iclrconf+B1e3OlStPB@gmail.com", "iclrconf+S1e2agrFvS@gmail.com", "iclrconf+BkevoJSYPB@gmail.com", "iclrconf+BJxSI1SKDH@gmail.com", "iclrconf+Hklz71rYvS@gmail.com", "iclrconf+H1eA7AEtvS@gmail.com", "iclrconf+HJeTo2VFwH@gmail.com", "iclrconf+r1lfF2NYvH@gmail.com", "iclrconf+Hke0K1HKwr@gmail.com", "iclrconf+S1efxTVYDr@gmail.com", "iclrconf+HkxQRTNYPH@gmail.com", "iclrconf+rkgt0REKwS@gmail.com", "iclrconf+HylAoJSKvH@gmail.com", "iclrconf+HJx81ySKwr@gmail.com", "iclrconf+B1e-kxSKDH@gmail.com", "iclrconf+B1l8L6EtDS@gmail.com", "iclrconf+SkxLFaNKwB@gmail.com", "iclrconf+SJxZnR4YvB@gmail.com", "iclrconf+BkglSTNFDB@gmail.com", "iclrconf+HJeOekHKwr@gmail.com", "iclrconf+SJlbGJrtDB@gmail.com", "iclrconf+HJlxIJBFDr@gmail.com", "iclrconf+Hygab1rKDS@gmail.com", "iclrconf+rye5YaEtPr@gmail.com", "iclrconf+ByedzkrKvH@gmail.com", "iclrconf+rJxycxHKDS@gmail.com", "iclrconf+Hyg9anEFPS@gmail.com", "iclrconf+ryg48p4tPH@gmail.com", "iclrconf+HJloElBYvB@gmail.com", "iclrconf+Bke_DertPB@gmail.com", "iclrconf+H1lj0nNFwB@gmail.com", "iclrconf+ByxdUySKvS@gmail.com", "iclrconf+SJlHwkBYDH@gmail.com", "iclrconf+BylVcTNtDS@gmail.com", "iclrconf+Bke61krFvS@gmail.com", "iclrconf+BJxH22EKPS@gmail.com", "iclrconf+S1xFl64tDr@gmail.com", "iclrconf+SyxIWpVYvr@gmail.com", "iclrconf+BkgXT24tDS@gmail.com", "iclrconf+S1lSapVtwS@gmail.com", "iclrconf+rkeIIkHKvS@gmail.com", "iclrconf+H1gBhkBFDH@gmail.com", "iclrconf+B1eWOJHKvB@gmail.com", "iclrconf+SkgGjRVKDS@gmail.com", "iclrconf+rJxe3xSYDS@gmail.com", "iclrconf+rklnDgHtDS@gmail.com", "iclrconf+SJxWS64FwH@gmail.com", "iclrconf+Bke8UR4FPB@gmail.com", "iclrconf+rJeIcTNtvS@gmail.com", "iclrconf+B1xwcyHFDr@gmail.com", "iclrconf+H1gmHaEKwB@gmail.com", "iclrconf+SyxhVkrYvr@gmail.com", "iclrconf+SJeq9JBFvH@gmail.com", "iclrconf+HyxjNyrtPr@gmail.com", "iclrconf+r1eiu2VtwH@gmail.com", "iclrconf+rkxNh1Stvr@gmail.com", "iclrconf+SJeY-1BKDS@gmail.com", "iclrconf+rylmoxrFDH@gmail.com", "iclrconf+rylnK6VtDH@gmail.com", "iclrconf+HyebplHYwB@gmail.com", "iclrconf+BkxSmlBFvr@gmail.com", "iclrconf+rygjmpVFvB@gmail.com", "iclrconf+rylwJxrYDS@gmail.com", "iclrconf+HJx-3grYDB@gmail.com", "iclrconf+Hkl9JlBYvr@gmail.com", "iclrconf+SJlRUkrFPS@gmail.com", "iclrconf+HyeaSkrYPH@gmail.com", "iclrconf+rkgAGAVKPr@gmail.com", "iclrconf+BJl07ySKvS@gmail.com"])))
    for user in users:
        existing = client.user.get(id=user)
        result = client.user.update(id=user, type=2)
        print(result.content)





def create_or_update_zoom(excel_data):

    """Create or up a meeting or webinar. Excel_data is a dictionary of information with headers similar to row1 in the
    Excel sample file.  Handle starttime and endtime as strings or naive datetime objects depending on how the user
    typed them into Excel. If this function is imported into django/python, it should send timezone aware datetime
    objects. """

    action = str(excel_data.get("action", excel_data.get("action", ""))).lower()


    if action == "skip":
        return {"action": "skip"}


    uniqueid = excel_data.get("uniqueid")
    if not uniqueid:
        print("the uniqueid field is required")
        stop()
        return {"action": "error"}

    from zsecrets import client, meeting_defaults, webinar_defaults
    zoom_user_id = excel_data.get('zoom_username')  # An email address
    if zoom_user_id:
        user_result = json.loads(client.user.get(id=zoom_user_id).content)
        user_id = user_result.get('id')
    else:
        try:
            from zsecrets import user_id
        except ImportError:
            stop()

    # existing_webinars and existing_meetings for this user
    if not zoom_user_id:
        from zsecrets import user_id
    existing_meetings, existing_webinars = get_existing_meetings(user_id=zoom_user_id, client=client)

    existing_meetings.update(existing_webinars)
    existing_zoom_events = existing_meetings

    # alternative_host = "iclrconf+{}@gmail.com".format(excel_data.get("uniqueid"))  #Now all meetings are hosted in their own account.

    starttime = excel_data.get("starttime")
    endtime = excel_data.get("endtime")

    # Starttime and endtime are required in the spreadsheet even though it's possible to schedule a recurring webinar without them.
    if starttime and endtime:
        if type(starttime) == str:
            if not starttime.endswith("Z"):
                starttime = starttime + "Z"
            if not endtime.endswith("Z"):
                endtime = endtime + "Z"
            starttime = UTC.localize(datetime.datetime.strptime(starttime, "%Y-%m-%d %H:%M:00Z"))
            endtime = UTC.localize(datetime.datetime.strptime(endtime, "%Y-%m-%d %H:%M:00Z"))

        elif type(starttime) == datetime.datetime:
            if starttime.tzinfo is None:

                """Excel has no concept of timezones. The timezone is in a column with header 'timezone'. If a 
                timezone is found in the datetime.datetime, then honor it. Otherwise, looking for a 'timezone' key in 
                the dictionary """
                try:
     
                    timezone_name = excel_data.get("timezone")
                    if not timezone_name or timezone_name == "None":
                        timezone_name = "UTC"
                    TZ = pytz.timezone(timezone_name)
                except:
                    stop()
                starttime += roundingerror  # Sometimes we get a rounding error from Excel. Round to nearest.
                starttime = starttime.replace(microsecond=0)
                endtime += roundingerror  
                endtime = endtime.replace(microsecond=0)
                starttime = TZ.localize(starttime)
                endtime = TZ.localize(endtime)
            else:
                TZ = starttime.tzinfo
        
        utc_starttime = UTC.normalize(starttime).strftime(timeformat)
        utc_endtime = UTC.normalize(endtime).strftime(timeformat)
        meeting_type = excel_data.get("meeting_or_webinar")


        """Update an existing meeting if there is one noted in the excel spreadsheet"""

        if meeting_type in ['meeting', "webinar"]:
            uniqueid = str(excel_data.get("uniqueid"))
            existing_zoom_event = existing_zoom_events.get(uniqueid)
            if action == "delete":
                if existing_zoom_event:
                    function_call = eval("client.{}.delete".format(meeting_type))
                    try:
                        result = function_call(user_id=user_id, id=existing_zoom_event.get('id'))
                    except:
                        stop()
                    if result.ok:
                        print("Deleted {}".format(existing_zoom_event.get('id')))
                        return {"action": "Deleted"}
                    else:
                        return {"action": "Error: unable to delete"}
                return {"action": "No Event to delete"}

            action = "update" if existing_zoom_event else "create"
            """"Create or update a new meeting or webinar"""
            """Load the defaults definition"""
            zoom_data = copy.copy(eval("{0}_defaults".format(meeting_type)))
            zoom_data.update({
                "agenda": str(uniqueid),
                "topic": excel_data.get("name"),
                "start_time": utc_starttime,
                "duration": int((endtime - starttime).seconds / 60),
                "password": excel_data.get("zoom_meeting_password"),
                })

            alternative_hosts = excel_data.get("alternative_hosts")
            if alternative_hosts:
                zoom_data['settings'].update({"alternative_hosts": alternative_hosts})

            zoom_data['recurrence'].update({"endtime": utc_endtime})

            if existing_zoom_event:
                function_call = eval("client.{0}.{1}".format(meeting_type, action))
                result = function_call(user_id=user_id, id=existing_zoom_event.get("id"), **zoom_data)
            else:
                function_call = eval("client.{0}.{1}".format(meeting_type, action))
                result = function_call(user_id=user_id, **zoom_data)

            if not (199 < result.status_code < 299):
                error_msg = eval("{0}_update_errors.get({1}, '___')".format(meeting_type, result.status_code))
                print("An abnormal return code received when updating {0}. ".format(uniqueid, error_msg))
                print(result.content)
                return_val = json.loads(result.content)
                return_val["action"] = "error"
                stop()
                return return_val
            print("{0} {1}".format(action, zoom_data.get("topic")))

            if action == "create":
                return_val = json.loads(result.content)
            elif action == "update":
                return_val = existing_zoom_events.get(excel_data.get(uniqueid))
                function_call = eval("client.{}.get".format(meeting_type))
                return_val = json.loads(function_call(id=existing_zoom_event.get('id')).content)
                existing_zoom_events[uniqueid] = return_val
            #print(return_val.get("start_url"))
            #print()
            #print(return_val.get("join_url"))
            return_val['zoom_id'] = return_val.get("id")
            return_val['status'] = result.ok
            return_val['action'] = action


            if action == "create":
                #add this meeting to the dictionary of meeitngs. 
                existing_zoom_events.update({return_val.get("agenda"): return_val})

            if meeting_type == "webinar":

                existing_zoom_event = return_val  # I lookup the meeting ID from existing_zoom_event below.

                """If this is a webinar, add the authors of the excel event as panelists"""

                pheaders = ['name', 'email']
                panelistStr = excel_data.get("panelists")  # comma separated list of emails Lee Campbell<lee@eventhosts.cc>, Brad Brockmeyer<brad@eventhosts.cc>
                if panelistStr is None:
                    plist = []
                else:
                    panelist_list = [parseaddr(item) for item in panelistStr.split(",")]
                    plist = [dict(zip(pheaders, item)) for item in panelist_list]
                    #zoom drops a panelist if the name is empty.   

                plist = [i if i.get("name") else {"name": 'Name Unavailable', 'email': i.get("email")} for i in plist]

                panelist_emails = [item.get("email") for item in plist]

                panelist_data = {
                    "panelists": plist
                }

                result = client.webinar.add_panelists(user_id=user_id, id=existing_zoom_event.get('id'), **panelist_data)
                if not result.ok:
                    print(json.loads(result.content))
                """Remove panelists that are not listed in the source (excel) data"""
                result = client.webinar.list_panelists(user_id=user_id, id=existing_zoom_event.get("id"))
                if result.ok:
                    listed_panelists = json.loads(result.content).get("panelists")
                    to_be_removed = [item for item in listed_panelists if not item.get("email") in panelist_emails ]
                    for webinar_panelist in to_be_removed:
                        pid = webinar_panelist.get("id")
                        result = client.webinar.remove_a_panelist(user_id=user_id, id=existing_zoom_event.get("id"), panelistid=pid)

            else:
                pass  # we need to add alternative hosts here if possible. 
            return return_val
        else:
            return {"action": "skipped due to incorrect meeting type in meeting_or_webinar: {}".format(excel_data.get("name"))}


    else:
        return {"action": "skipped ... no start or no end time: {}?".format(excel_data.get("name"))}



if __name__=="__main__":
    #create_iclr2020_posterusers()
    #create_chair_zoom_accounts()
    #result = get_all_events()
    #license_users()
    #delete_all_main_poster_meetings()
    #create_climate_users()
    parser = ArgumentParser()
    parser.add_argument("--clearAll", action="store_true", help="delete any existing webinars that start with AIWeb")
    parser.add_argument("--users", action="store_true")
    parser.add_argument("--meeting", action="store_true", help="create a meeting not a webinar")
    parser.add_argument("--getAllEvents", action="store_true")

    #
    #ns = parser.parse_args()
    #
    #if ns.getAllEvents:
    #    get_all_events()
    #
    #if ns.clearAll:
    #    clearAll()

