import endpoints
from protorpc import messages, message_types, remote
import logging
import webapp2
from google.appengine.api import urlfetch
from oauth2client.client import GoogleCredentials
from apiclient import discovery
import urllib
import simplejson as json
import base64

api = endpoints.api(name='cloud_vision_slackbot', version='v1', description='Slackbot for searching images on GAE')

SLACK_TOKEN = "xoxp-2315121681-2316431386-31999338550-8b0055b9c7"
DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'

credentials = GoogleCredentials.get_application_default()
service = discovery.build('vision', 'v1', credentials=credentials, discoveryServiceUrl=DISCOVERY_URL)

class SlackMessageRequest(messages.Message):
    message = messages.StringField(1)


class EmptyResponse(messages.Message):
    message = messages.StringField(1)


def get_slack_image_files(ts_from, ts_to, page):
    url_with_params = 'https://slack.com/api/files.list' + urllib.urlencode({
        "token":SLACK_TOKEN,
        "types":"images",
        "ts_from":ts_from,
        "ts_to": ts_to,
        "page": page
    })
    files_response = urlfetch.fetch(url_with_params)
    files_data = json.loads(files_response)
    files = files_data['files']
    paging = files_data['paging']
    return files, paging

def get_last_image_ts():
    # get the last image timestamp from database here
    url = 'https://files.slack.com/files-pri/T02993KL1-F0YEBL5FY/received_10205662956802619.jpeg'
    image_response = urlfetch.fetch(url,headers={"Authorization": "Bearer " + SLACK_TOKEN})
    return


def send_url_to_cloudvision(url):
    image_response = urlfetch.fetch(url, headers={"Authorization": "Bearer " + SLACK_TOKEN})
    image_content = base64.b64encode(image_response.body)
    service_request = service.images().annotate(body={
        'requests': [{
            'image': {
                'content': image_content.decode('UTF-8')
            },
            'features': [{
                'type': 'LABEL_DETECTION',
                'maxResults': 1
            }, {
                'type': ''
            }]
        }]
    })
    response = service_request.execute()


def process_new_images(channel_id):
    files, paging = get_slack_image_files(0, "now", 1)
    for file in files:
        url = file['url_private']
        send_url_to_cloudvision(url, channel_id)




@api.api_class(resource_name='cloud_vision_api')
class RESTApi(remote.Service):
    @endpoints.method(SlackMessageRequest, EmptyResponse, path='/test',
                      http_method='POST', name='slack.incomingMessage')
    def organization_info(self, request):
        logging.info(request.message)
        return EmptyResponse(message="OK")

API = endpoints.api_server([api])

class SlackMessageHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('OK')
        self.response.set_status(200)

    def post(self):
        logging.info("Request Body: " + str(self.request.body))
        values = [dict(row.strip().split('=') for key_value in row) for row in self.request.body.split('&')]
        logging.info("Webhook Message: " + str(values))

        self.response.write("OK")


class ImageSearch(webapp2.RedirectHandler):
    def post(self):
        logging.info("Request Body: " + str(self.request.body))
        self.response.write("No images found.")


app = webapp2.WSGIApplication([
    ('/test', SlackMessageHandler),
    ('/imagesearch', ImageSearch)
], debug=True)