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
    logging.info("sending message as bot" + url)
    response = urlfetch.fetch(url)
    if response.status_code != 200:
        logging.error("sending message failed: " + response.content)

def get_some_images(message_values):
    taskqueue.add(url="/tasks/vision", params=message_values)

def parse_slack_message(body):
    values = {}
    for row in body.split('&'):
        logging.info(row)
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


class SlackMessageHandler(webapp2.RequestHandler):
    def post(self):
        logging.info("Request Body: " + str(self.request.body))

        values = parse_slack_message(self.request.body)

        logging.info("Webhook Message: " + str(values))

        if 'text' in values:
            text = urllib.unquote_plus(values['text'])
            logging.info("Text received from Webhook: " + text)
            # ID for the slack-ray-vision bot
            if text.startswith("<@U0Z69KYHE>: "):
                urls = search_for_tags_in_images(text, values['channel_id'])
                if len(urls):
                    for url in urls:
                        send_message_to_channel(url, values["channel_id"])
                else:
                    send_message_to_channel("No Results :disappointed:")
                self.response.write("OK")
                return
        get_some_images(values)
        self.response.write("OK")

class HowdyWorld(webapp2.RedirectHandler):
    def get(self):
        self.response.write("Howdy!")

class LoaderTest(webapp2.RedirectHandler):
    def get(self):
        self.response.write("loaderio-baff6ef8072d19556bfaee0ee03fc39b")

handler = webapp2.WSGIApplication([
    ('/slack/outgoing-web-hook', SlackMessageHandler),
    ('/howdyworld', HowdyWorld),
    ('/loaderio-baff6ef8072d19556bfaee0ee03fc39b/', LoaderTest)

], debug=True)
