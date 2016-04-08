import webapp2
from entities import *

class DBQuery(webapp2.RedirectHandler):
    def get(self):
        Image().query().get(use_cache=False, use_memcache=False)  # gets random image and loads from db. Just to test a long task.
        self.response.write("Loaded Image!")

class HowdyWorld(webapp2.RedirectHandler):
    def get(self):
        self.response.write("Howdy!")

handler = webapp2.WSGIApplication([
    ('/test/howdyworld', HowdyWorld),
    ('/test/dbquery', DBQuery),

], debug=True)
