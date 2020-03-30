from zoomus.client import ZoomClient
integrations_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(integrations_dir, "zoomus"))
import json

client = ZoomClient("xxxxxxxxxxxxxxxxxxxxxxx", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx") #(API_KEY, API_SECRET)

user_result = json.loads(client.user.get(id='xxxx@example.com').content)

user_id = user_result.get('id')