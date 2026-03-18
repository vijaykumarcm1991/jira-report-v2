import time
import psycopg2
import os

DB_HOST = "db"
DB_NAME = "jira_reports"
DB_USER = "jira_user"
DB_PASSWORD = "jira_pass"

while True:
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.close()
        print("✅ Database is ready!")
        break
    except Exception as e:
        print("⏳ Waiting for DB...", e)
        time.sleep(2)