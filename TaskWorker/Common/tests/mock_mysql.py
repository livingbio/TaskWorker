# http://legacy.python.org/dev/peps/pep-0249/

import sqlite3
import os

mock_db = set()
MOCK_PATH = "./mock_db/"

def connect(**kwargs):
	if not os.path.isdir(MOCK_PATH):
		os.makedirs(MOCK_PATH)

	db = kwargs.get("db")
	instance = kwargs.get("instance")

	db_name = "{}/mock_{}x{}.db".format(MOCK_PATH, instance, db)
	
	mock_db.add(db_name)
	return sqlite3.connect(db_name)


class Error(Exception):
	pass

def clean():
	for db in mock_db:
		os.remove(db)

	mock_db.clear()