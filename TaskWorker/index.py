import webapp2
import json
import urllib
import logging
import mapreduce.third_party.pipeline as pipeline
import mapreduce.third_party.pipeline.models as pipeline_models
from handlers import ApiHandler, PermissionError
from google.appengine.api import taskqueue, users, memcache
from google.appengine.ext import ndb, db
from .config import *

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


class TaskAuthHandler(ApiHandler):
    def dispatch(self):
        token = self.request.get("token")
        assert token, PermissionError("login required")
        token_expire = memcache.get("token")

        if isinstance(token_expire, datetime) and token_expire > datetime.utcnow():
            return super(self, TaskAuthApiHandler).dispatch()

        raise PermissionError("token is not correct")


class LoginHandler(webapp2.RequestHandler):
    def login(self):
        import os, base64
        token = LOGIN_TOKEN_PREFIX + base64.b64encode(os.urandom(15))

        memcache.set(token, token, DEFAULT_LOGIN_EXPIRE_SECONDS)
        self.response.out.write(josn.dumps({"token": token}))

    def post(self):
        from Crypto.PublicKey import RSA

        if users.is_current_user_admin():
            return self.login()

        else:
            key = self.request.get("key")
            assert key
            assert key == AUTH_KEY, PermissionError("login failed")
            return self.login()


def load_pipeline(cls_path):
    module_path, class_name = ".".join(cls_path.split('.')[:-1]), cls_path.split('.')[-1]
    mod = __import__(module_path, fromlist=[class_name])
    return getattr(mod, class_name)


class TriggerHandler(LoginHandler):
    def post(self):
        self.get()

    def get(self):
        id = self.request.get("id")
        path = self.request.get("path")
        args = self.request.get("args")
        kwargs = self.request.get("kwargs")

        assert path

        args = json.loads(args) if args else []
        kwargs = json.loads(kwargs) if kwargs else {}

        assert isinstance(args, list)
        assert isinstance(kwargs, dict)

        cls = load_pipeline(path)
        p = cls(*args, **kwargs)
        p.start()

        task_id = id or p.root_pipeline_id

        _TA_Task(
            id=task_id,
            root_pipeline_id=p.root_pipeline_id,
            params={
                "id": id,
                "path": path,
                "params": {
                    "args": args,
                    "kwargs": kwargs
                }
            }
        ).put()

        return self.output({
            "id": task_id
        })


class StatusHandler(LoginHandler):
    STATUS_MAP = {
        'finalizing': "WORKING",
        'retry': "WORKING",
        "waiting": "WORKING",
        'run': "WORKING",
        'done': "DONE",
        "aborted": "FAILED"
    }

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

        r = pipeline.get_status_tree(root_pipeline_id)
        assert 'pipelines' in r and root_pipeline_id in r['pipelines']

        root_pipeline = r['pipelines'][root_pipeline_id]
        outputs = root_pipeline["outputs"]
        outputs = zip(outputs.keys(), db.get(outputs.values()))
        outputs = {k[0]: k[1].value if k[1].status == pipeline_models._SlotRecord.FILLED else None for k in outputs}

        assert root_pipeline['status'] in self.STATUS_MAP

        self.output({
            "id": id,
            "status": self.STATUS_MAP[root_pipeline['status']],
            "msg": root_pipeline.get('lastRetryMessage'),
            "output": outputs
        })

class StopHandler(LoginHandler):

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

        pipeline_key = db.Key.from_path(pipeline_models._PipelineRecord.kind(), root_pipeline_id)

        taskqueue.add(
            url="/mapreduce/pipeline/abort",
            method='POST',
            params={
                "pipeline_key": pipeline_key,
                "purpose": "abort"
            }
        )

        return self.output({
            "id": id
        })

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key'
}

app = webapp2.WSGIApplication([
    (r'.*/login', LoginHandler),
    (r'.*/trigger', TriggerHandler),
    (r'.*/status', StatusHandler),
    (r'.*/stop', StopHandler),
], debug=True, config=config)
