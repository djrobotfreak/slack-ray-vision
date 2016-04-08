import webapp2
from google.appengine.api import urlfetch
from oauth2client.client import GoogleCredentials
from apiclient import discovery
import urllib
import simplejson as json
import base64
import logging
from entities import Image, Team

DISCOVERY_URL = 'https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'
SLACK_TOKEN = "xoxp-2315121681-2316431386-31999338550-8b0055b9c7"

credentials = GoogleCredentials.get_application_default()
service = discovery.build('vision', 'v1', credentials=credentials, discoveryServiceUrl=DISCOVERY_URL)

def get_slack_image_files(channel_id, ts_from=0, page=1):
    url_with_params = 'https://slack.com/api/files.list?' + urllib.urlencode({
        "token": SLACK_TOKEN,
        "types": "images",
        "ts_from": ts_from,
        "page": page,
        "channel": channel_id
    })
    response = urlfetch.fetch(url_with_params)
    logging.info(dir(response))
    if response.status_code != 200:
        raise Exception()
    files_data = json.loads(response.content)
    files = files_data['files']
    paging = files_data['paging']
    return files, paging

def get_last_image_ts(channel_id):
    image = Image.query(Image.channel_id == channel_id, projection=[Image.ts]).get()
    if not image:
        return 0

    return image.ts

def send_url_to_cloudvision(url, slack_token=SLACK_TOKEN):
    image_response = urlfetch.fetch(url, headers={"Authorization": "Bearer " + slack_token})
    image_content = base64.b64encode(image_response.content)
    service_request = service.images().annotate(body={
        'requests': [{
            'image': {
                'content': image_content.decode('UTF-8')
            },
            'features': [{
                'type': 'LABEL_DETECTION',
                'maxResults': 15
            }]
        }]
    })
    response = service_request.execute()
    img_labels = []
    logging.info(str(response))
    try:
        for label in response['responses'][0]['labelAnnotations']:
            img_labels.append(label['description'])
    except:
        logging.info("No labels found for image: " + url)
    logging.info("Labels found: " + str(img_labels))
    return img_labels

def send_reaction(_file, token=SLACK_TOKEN):
    logging.info("Sending reaction for file id" + _file['id'])
    file_id = _file['id']
    url = 'https://slack.com/api/reactions.add?' + urllib.urlencode(
        {'token': SLACK_TOKEN, 'file': file_id, 'name': 'muscle'})
    response = urlfetch.fetch(url)
    if response.status_code != 200:
        logging.info("Send response failed with: " + response.status_code + ": " + str(response.content))

def process_new_images(message_values):

    files, paging = get_slack_image_files(channel_id=message_values["channel_id"],
                                          ts_from=get_last_image_ts(message_values['channel_id']),
                                          page=1)

    team = Team.query(Team.team_id == message_values["team_id"]).get()
    if not team:
        team = Team()
        team.team_id = message_values["team_id"]
        team.put()
    for _file in files:
        logging.info("dealing with file:" + _file["id"])
        image = Image.query(Image.private_url == _file['url_private']).get()
        if image:
            continue
        image = Image()
        image.private_url = _file['url_private']
        image.team = team.key
        image.channel_id = message_values["channel_id"]
        image.ts = message_values["timestamp"]
        image.tags = send_url_to_cloudvision(image.private_url)
        image.put()
        send_reaction(_file)
        logging.info("completed one file successfully!!!")

class ImageTaskHandler(webapp2.RequestHandler):
    def post(self):
        values = self.request.params
        process_new_images(values)
        self.response.write("OK")

handler = webapp2.WSGIApplication([
    ('/tasks/vision', ImageTaskHandler),
], debug=True)
