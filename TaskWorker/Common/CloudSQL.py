from mapreduce import base_handler, mapreduce_pipeline
import mapreduce.third_party.pipeline.common as pipeline_common
import MySQLdb
# use the recommand way to connect database
# https://developers.google.com/appengine/docs/python/cloud-sql/?hl=zh-TW

class Execute(base_handler.PipelineBase):
    def run(self, instance, database, query, values=None):
        db = MySQLdb.connect(unix_socket="/cloudsql/" + instance, db=database, user="root")
        try:
            cursor = db.cursor()
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
            db.commit()
            return cursor.fetchall()
        except MySQLdb.Error, e:
            # TODO: db.rollback will raise exception while db is MyISAM
            db.rollback()
            raise
        finally:
            db.close()


class ExecuteMany(base_handler.PipelineBase):
    def run(self, instance, database, query, values):
        db = MySQLdb.connect(unix_socket="/cloudsql/" + instance, db=database, user="root")
        try:
            cursor = db.cursor()
            cursor.executemany(query, values)
            db.commit()
            return cursor.fetchall()
        except MySQLdb.Error, e:
            db.rollback()
            raise
        finally:
            db.close()


