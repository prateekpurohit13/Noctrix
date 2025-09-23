import sqlite3, datetime as dt

conn = sqlite3.connect("data/app.db")
for ts, action, obj, success in conn.execute("select ts, action, object_id, success from audit order by id desc limit 10"):
    print(dt.datetime.fromtimestamp(ts).isoformat(), action, obj, success)
conn.close()
