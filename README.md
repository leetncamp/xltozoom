# XLtoZoom

This project uses JWT Tokens and is deprecated by Zoom.us. 
Create and update zoom meetings from an Excel spreadsheet

### Dependencies
pythonn3  
openpyxl  
pytz  


### Installation
The zoomus python package handles creating and updating the zoom API JWT auth tokens.  Otherwise, it just a thin wrapper over the zoom apis. I found 2 issues with the standard zoomus python package. 

1. The zoomus package failed to wrap the API that adds panelists to a webinar. I added that wrapper in the static copy provided here.

2. Also, zoomus's documentation is thin, and it's likely I'm probably not using it correctly. When posting, the zoom API complained that zoomus was submitting the data as post parameters rather than a vaild json object.   I monkeypatched the post_request and post_delete function in util.py to post the data as a json object.  

For these two reasons, do *not* pip install zoomus. The patched version is included with this repository. Keep the patched version until I resolve these 2 issues.  

### Usage

You need to generate an API_KEY and an API_SECRET.  More information is here https://github.com/zoom/zoom-api-jwt.git.  Following the pattern of the secrets.sample.py, add your keys to secrets.py.

Load your schedule into schedule.xlsx following the example in schedule.sample.xlsx.  Create secrets.py based off secrets.sample.py.  Add your API key and secret to the file. Review and update the meeeting and webinar settings in your secrets.py file. 

Run go.py to create or update your zoom meetings or webinars from schedule.xlsx. If go.py creates a meeting, it will write that meeting's ID into the zoomid column.  For this reason, do not have schedule.xlsx open when running go.py.  

You may update the start and endtimes, the timezone, title, abstracts or panelists and re-run go.py.   Panelists are ignored when creating a meeting.

You may import the function create_or_update_zoom directly without using excel. It takes a dictionary where the keys are the same as the column headers in the excel file. 

Warning: When you add panelists to a webinar, they are immediatly sent an email invitation directly from zoom.  As of April 2, there is no way to disable this email.  Otherwise, no emails are sent.
