import unittest
import webtest
import webapp2
from mock import patch, MagicMock
import sqlite3
from google.appengine.ext import testbed
import test_shared
import util_test
import testutil

class CloudSQLTest(test_shared.TaskRunningMixin, unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()
        self.cookies = {}

        # testutil.setup_for_testing()
        super(CloudSQLTest, self).setUp()

    def testExecute(self):
        with patch('MySQLdb.connect') as s:
            s.return_value = sqlite3.connect('test.db')
            from TaskWorker.Common.CloudSQL import Execute
            p = Execute('test_instance', 'test_db', "insert into test_table values(?, ?)", (1,2))
            self.assertEqual(2, self.run_pipeline(p).default.value)

