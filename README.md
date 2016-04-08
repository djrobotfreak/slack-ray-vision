# slack-ray-vision

Slack-ray-vision is an integration for slack that uses the Google Cloud Vision API to document images you upload in slack!

## File structure
 - main.py: Main request handler. This contains handlers for slack outgoing-webhook integrations.
 - tasks.py: Taskqueue request handler. This contains the code for cloud vision apis
 - static.py: This contains public variables shared across code
 - tests.py: Request handler for load testing
 - entities.py: Contains all db definitions.
 - app.yaml: setup for appengine stuff