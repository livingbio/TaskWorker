from mapreduce import base_handler
from oauth2client.appengine import AppAssertionCredentials
import mapreduce.third_party.pipeline as pipeline
import mapreduce.third_party.pipeline.common as pipeline_common
import logging

credentials = AppAssertionCredentials(
)

http = credentials.authorize(httplib2.Http(memcache))
service = build('translate', 'v2', http=http)

class Translate(base_handler.PipelineBase):
    def run(self, q, target):
        if isinstance(text, basestring):
            q = [q]

        results = service.translations().list(
            target=target,
            q=q
        ).execute()

        return [k['translatedText'] for k in results['translations']]

