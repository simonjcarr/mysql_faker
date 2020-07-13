from database_connection import connect_db, close_db

def writedb(job_id, message):
  db = connect_db()
  cursor = db.cursor(dictionary=True)
  cursor.execute("USE %s;"%(os.getenv("FAKER_DATABASE")))
  cursor.execute("insert into joblogs (%d, %s)"%(job_id, message))
  db.commit()
  db.close()



def write_log(job_id, message):
  writedb(job_id, message)
  




