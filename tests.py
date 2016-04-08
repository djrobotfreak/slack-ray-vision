import webapp2
import time

class DBQuery(webapp2.RedirectHandler):
    def get(self):
        time.sleep(0.5)  # Some long process
        self.response.write("Finished!")

class HowdyWorld(webapp2.RedirectHandler):
    def get(self):
        self.response.write("Howdy!")

handler = webapp2.WSGIApplication([
    ('/test/howdyworld', HowdyWorld),
    ('/test/dbquery', DBQuery),
], debug=True)
