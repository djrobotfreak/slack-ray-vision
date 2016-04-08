import endpoints
import logging
import webapp2
from entities import *
import urllib
from google.appengine.api import urlfetch
from static import SLACK_BOT_TOKEN, DEREK_SLACK_TOKEN
from google.appengine.api import taskqueue

api = endpoints.api(name='cloud_vision_slackbot', version='v1', description='Slackbot for searching images on GAE')


def send_message_to_channel(text, channel_id, token=SLACK_BOT_TOKEN):
    url = 'https://slack.com/api/chat.postMessage?' + urllib.urlencode({
        'token': token,
        'channel': channel_id,
        'text': text
    })
    logging.info("chat.postMessage Request URL:" + url)
    response = urlfetch.fetch(url)
    if response.status_code != 200:
        logging.error("chat.postMessage failed: " + response.content)

# Adds processes to the taskqueue. This prevents long running requests from timing out.
def get_some_images(message_values):
    taskqueue.add(url="/tasks/vision", params=message_values)

def parse_slack_message(body):
    values = {}
    for row in body.split('&'):
        key, value = row.strip().split('=')
        values[key] = value
    return values

def search_for_tags_in_images(text, channel_id):
    tags = text.split(' ')
    tags.pop(0)
    images = []
    urls = []
    if len(tags):
        images = Image.query(Image.tags.IN(tags), Image.channel_id == channel_id).fetch()
    for image in images:
        urls.append(image.private_url)
    return urls

# Slack outgoing webhook call. This is hit everytime there is a message in the #cloud-vision channel.
class SlackMessageHandler(webapp2.RequestHandler):
    def post(self):
        values = parse_slack_message(self.request.body)
        logging.info("Webhook Message: " + str(values))
        if 'text' in values:
            text = urllib.unquote_plus(values['text'])
            logging.info("Text received from Webhook: " + text)
            # Slack sends the ID for the user during an @mention
            # This is the ID for the slack-ray-vision bot
            if text.startswith("<@U0Z69KYHE>: "):
                urls = search_for_tags_in_images(text, values['channel_id'])
                if len(urls) > 0:
                    for url in urls:
                        send_message_to_channel(url, values["channel_id"])
                else:
                    send_message_to_channel("No Results :disappointed:")
                self.response.write("OK")
                return
        get_some_images(values)
        self.response.write("OK")

# Index Page
class HowdyWorld(webapp2.RedirectHandler):
    def get(self):
        self.response.write("Howdy!")

# Necessary for loader.io load testing.
class LoaderTest(webapp2.RedirectHandler):
    def get(self):
        self.response.write("loaderio-baff6ef8072d19556bfaee0ee03fc39b")

handler = webapp2.WSGIApplication([
    ('/slack/outgoing-web-hook', SlackMessageHandler),
    ('/', HowdyWorld),
    ('/loaderio-baff6ef8072d19556bfaee0ee03fc39b/', LoaderTest)

], debug=True)
