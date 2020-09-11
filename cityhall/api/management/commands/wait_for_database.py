from django.core.management.base import BaseCommand, CommandError
import os
import psycopg2
import time


class Command(BaseCommand):
    help = 'Check to see that the database is up'

    def handle(self, *args, **kwargs):
        while True:
            try:
                user =  os.environ['POSTGRES_USER']
                password = os.environ['POSTGRES_PASS']
                db = os.environ['POSTGRES_DBNAME']
                host = 'cityhall-db'
                port = 5432

                print(f"Attempting to connect user={user}, password={password}, db={db}, host={host}, port={port}")
                connection = psycopg2.connect(user = user, password = password, host = host, port = port, database = db)
                print ("Connected to database")
                return
            except Exception as e:
                print(f"Unable to connect: {e}, sleeping and will try again.")
                time.sleep(1)


