import webapp2
import json
import urllib
from handlers import ApiHandler
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import logging

class _TA_Task(ndb.Model):

    """store task & pipeline mapping
    """
    root_pipeline_id = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    params = ndb.JsonProperty()

    @property
    def job_id(self):
        return self.key.id()


def load_pipeline(cls_path):
    module_path, class_name = ".".join(cls_path.split('.')[:-1]), cls_path.split('.')[-1]
    mod = __import__(module_path, fromlist=[class_name])
    return getattr(mod, class_name)


class TriggerHandler(ApiHandler):

    def get(self):
        id = self.request.get("id")
        path = self.request.get("path")
        cls_path = self.request.get("cls")
        method = self.request.get("method", "get")
        params = self.request.get("params", "")

        method = method.lower()
        assert path or cls_path
        assert method in ("get", "post")

        cls = load_pipeline(cls_path)
        p = cls(*params)
        p.start()

        task_id = id or p.root_pipeline_id

        _TA_Task(
            id=task_id,
            root_pipeline_id=p.root_pipeline_id,
            params={
                "id": id,
                "cls": cls_path,
                "method": method,
                "path": path,
                "params": params
            }
        ).put()

        return self.output({
            "id": task_id
        })


class StatusHandler(ApiHandler):

    def get(self):
        id = self.request.get("id")
        pipeline_id = self.request.get("root_pipeline_id")
        assert id or pipeline_id

        if id:
            task = _TA_Task.get_by_id(id)
            assert task and task.root_pipeline_id
            root_pipeline_id = task.root_pipeline_id
        else:
            root_pipeline_id = pipeline_id

        r = urlfetch.fetch(
            url=self.request.host_url + '/_ah/pipeline/rpc/tree?root_pipeline_id={}'.format(root_pipeline_id)
        )
        assert r.status_code == 200

        r = json.loads(r.content)

        self.output(r)


class StopHandler(ApiHandler):

    def get(self):
        id = self.request.get("id")
        pipeline_id = self.request.get("root_pipeline_id")
        assert id or pipeline_id

        if id:
            task = _TA_Task.get_by_id(id)
            assert task and task.root_pipeline_id
            root_pipeline_id = task.root_pipeline_id
        else:
            root_pipeline_id = pipeline_id

        pipeline = Pipeline.from_id(root_pipeline_id)
        pipeline_key = str(pipeline.key())

        r = urlfetch.fetch(
            url=self.request.host_url + "/_ah/pipeline/abort",
            method=urlfetch.POST,
            payload=urllib.urlencode({
                "pipeline_key": pipeline_key,
                "purpose": "abort"
            }))

        assert r.status_code == 200
        return self.output({
            "id": id
        })

app = webapp2.WSGIApplication([
    (r'.*/trigger', TriggerHandler),
    (r'.*/status', StatusHandler),
    (r'.*/stop', StopHandler),
], debug=True)
