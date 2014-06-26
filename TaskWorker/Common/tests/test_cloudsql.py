# use pymysql to mock mysqldb
import unittest
import webtest
import webapp2
from mock import patch, MagicMock
from google.appengine.ext import testbed
import test_shared
import util_test
import testutil
import mock_mysql

def mock_mysqldb():
    import sys
    sys.modules["MySQLdb"] = sys.modules["_mysql"] = sys.modules["mock_mysql"]

class CloudSQLTest(test_shared.TaskRunningMixin, unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_all_stubs()
        self.cookies = {}

        mock_mysqldb()
        super(CloudSQLTest, self).setUp()

    def tearDown(self):
        mock_mysql.clean()

    def testExecute(self):
        from TaskWorker.Common.CloudSQL import *

        p = Execute('instance', 'db', """create table test_table(a text, b text)""")
        self.run_pipeline(p)
        p = Execute('instance', 'db', "insert into test_table values(?, ?)", (1,2))
        self.assertEqual([], self.run_pipeline(p).default.value)

        p = ExecuteMany('instance', 'db', "insert into test_table values(?, ?)", [(1,2), (3,4)])
        self.assertEqual([], self.run_pipeline(p).default.value)

        p = Execute('instance', 'db', 'select count(*) from test_table')
        self.assertEqual([[3]], self.run_pipeline(p).default.value)

        p = Execute('instance', 'db', 'select a, b from test_table order by a')
        self.assertEqual([['1','2'], ['1','2'], ['3','4']], self.run_pipeline(p).default.value)



