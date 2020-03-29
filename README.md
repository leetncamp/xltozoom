# XLtoZoom

Create and update zoom meetings from an Excel spreadsheet

### Dependencies
zoomus (https://github.com/actmd/zoomus) Do not pip install this. See below for more info. 

### Installation
The zoomus python package handles creating and updating the JWT auth tokens.  Otherwise, it just a thin wrapper over the zoom apis. I found 2 issues with the zoomus python package.

1. The zoomus package failed to wrap the API that adds panelists to a webinar. I added that wrapper in the static copy provided here.

2. Also, zoomus's documentation is thin, and it's likely I'm probably not using it correctly. When posting, the zoom API complained that zoomus was submitting the data as post parameters rather than a vaild json object.   I monkeypatched the post_request function in util.py to post the data as a json object.  

For these two reasons, do *not* pip install zoomus. Use the one provided here until these 2 issues are resolved.  

### Usage

You need to generate an API_KEY and an API_SECRET.  More information is here https://github.com/zoom/zoom-api-jwt.git.  Following the pattern of the secrets.sample.py, add your keys to secrets.py.

Load your schedule into schedule.xlsx following the example in schedule.sample.xlsx.

Run generate.py to either create or update your zoom meetings or webinars from the schedule.

