import psycopg2
import os

def init_db():
    conn = psycopg2.connect(
        dbname="certwatch",
        user="certuser",
        password=os.getenv("POSTGRES_PASSWORD"),
        host="cert-db"
    )
    cursor = conn.cursor()
    cursor.execute(open("/db/init.sql", "r").read())
    conn.commit()
    cursor.close()
    conn.close()