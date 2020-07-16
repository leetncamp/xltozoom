import os
import sys
integrations_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(integrations_dir, "zoomus"))
from zoomus.client import ZoomClient
import json



client = ZoomClient("xxxxxxxxxxxxxxxxxxxxxxx", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx") #(API_KEY, API_SECRET)

user_result = json.loads(client.user.get(id='xxxx@example.com').content) #The email address used to generate the keys

user_id = user_result.get('id')

#-----------------------------------

graphical_warning = False


meeting_defaults = {
    "type": 5,
    "recurrence": {
      "type": 1,
      "repeat_interval": 1,
      #"end_date_time": endtime,
    },
    "settings": {
      "allow_multiple_devices": "true",
      "approval_type": 0,
      "audio": 'both',
      "auto_recording": "cloud",
      "cn_meeting": "true",
      "in_meeting": "true",
      "enforce_login": "true",
      "enforce_login_domains": "",
      "global_dial_in_countries": [],
      "host_video": "false",
      "join_before_host": "false",
      "mute_upon_entry": "true",
      "participant_video": "false",
      "registrants_email_notification": "false",
      "registration_type": 0,
      "use_pmi": "false",
      "watermark": "false",
    }
}


webinar_defaults = {

    "type": 6,
    "duration": "60",
    "recurrence": {
        "type": 1,
        "repeat_interval": 1,
        #"end_date_time": endtime,
    },
    "settings": {
        "allow_multiple_devices": "true",
        #"alternative_hosts": "terrence.gaines@hp.com",
        "approval_type": 0,
        "audio": "both",
        "auto_recording": "cloud",
        "close_registration": "true",
        "cn_meeting": "true",
        "in_meeting": "true",
        "enforce_login": "true",
        "enforce_login_domains": "",
        "hd_video": "true",
        "host_video": "true",
        "meeting_authentication": "false",
        "on_demand": "true",
        "panelists_video": "true",
        "practice_session": "false",
        "registrants_email_notification": "false",
        "registration_type": 1,
        "show_share_button": "false",
    },
}