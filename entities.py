from google.appengine.ext import ndb

class Team(ndb.Model):
    slack_token = ndb.StringProperty()
    team_id = ndb.StringProperty()

class Image(ndb.Model):
    private_url = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    team = ndb.KeyProperty()
    channel_id = ndb.StringProperty()
    ts = ndb.StringProperty(default="0")
