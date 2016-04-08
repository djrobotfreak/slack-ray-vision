import endpoints
import logging
import webapp2
from entities import *
import urllib
from google.appengine.api import urlfetch


from google.appengine.api import taskqueue

SLACK_SECRET = '3d8c07ab1fb8a2668ff1fc100d3b2b27'
SLACK_TOKEN = "xoxp-2315121681-2316431386-31999338550-8b0055b9c7"

api = endpoints.api(name='cloud_vision_slackbot', version='v1', description='Slackbot for searching images on GAE')

def send_message_to_channel(text, channel_id, token=SLACK_TOKEN):
    url = 'https://slack.com/api/chat.postMessage?' + urllib.urlencode({
        'token': token,
        'channel': channel_id,
        'text': text
    })
    logging.info("sending links to url: " + url)
    response = urlfetch.fetch(url)
    if response.status_code != 200:
        logging.info("sending message failed: " + response.content)

def get_some_images(message_values):
    taskqueue.add(url="/tasks/vision", params=message_values)


def parse_slack_message(body):
    values = {}
    for row in body.split('&'):
        logging.info(row)
        key, value = row.strip().split('=')
        values[key] = value
    return values

def search_for_tags_in_images(text, channel_id, toke=SLACK_SECRET):
    tags = text.split(' ')
    tags.pop(0)
    images = []
    urls = []
    if len(tags):
        images = Image.query(Image.tags.IN(tags), Image.channel_id == channel_id).fetch()
    for image in images:
        urls.append(image.private_url)
    return urls


class SlackMessageHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('OK')
        self.response.set_status(200)

    def post(self):
        logging.info("Request Body: " + str(self.request.body))

        values = parse_slack_message(self.request.body)
        logging.info("Webhook Message: " + str(values))

        if 'text' in values:
            text = urllib.unquote_plus(values['text'])

            if text.startswith("slackvision: "):
                urls = search_for_tags_in_images(text, values['channel_id'])
                for url in urls:
                    send_message_to_channel(url, values["channel_id"])
                self.response.write("OK")
                return

        get_some_images(values)
        self.response.write("OK")

class ImageSearch(webapp2.RedirectHandler):
    def post(self):
        logging.info("Request Body: " + str(self.request.body))
        self.response.write("No images found.")


handler = webapp2.WSGIApplication([
    ('/slack/outgoing-web-hook', SlackMessageHandler),
    ('/imagesearch', ImageSearch)
], debug=True)
