import sys, os, time, urllib.request, json
import settings
#from create_data import run
from create_data import Job
from logData import write_log
from database_connection import connect_db, close_db
from multiprocessing import Process, Semaphore

concurrency = 3
def get_job():
  db = connect_db()
  try:
    cursor = db.cursor(dictionary=True)
    cursor.execute("USE %s;"%(os.getenv("FAKER_DATABASE")))
    
    cursor.execute("SELECT j.id as job_id, d.*  FROM `jobs` j JOIN `databases` d ON d.id = `j`.`database_id` WHERE `j`.`running` = 0 LIMIT 1")
    dbJob = cursor.fetchone()
    if dbJob:
      cursor.execute("UPDATE `jobs` SET `running` = 1 WHERE `id` = %d"%(dbJob['job_id']))
      db.commit()
      return dbJob
    else:
      return None
  except Exception as e:
    sys.exit(e)

def get_json(database_id):
  
  url = "%s/api/v1/json/%d"%(os.getenv("API_URL"), database_id)
  with urllib.request.urlopen(url) as u:
    data = json.loads(u.read())
  return data

if __name__ == "__main__":
  while True:
    time.sleep(1)  
    try:
      # number = number + 1
      # print("Looping " + str(number))
      dbJob = get_job()
      if not dbJob:
        continue
      database_id = dbJob['id']
      
      json_data = get_json(database_id)
      worker = Job(json_data, dbJob)
      worker.start()
      # sema.acquire()
      
      # worker.start()
      # worker.join()
      #Process(target=worker).start()
      
    except Exception as e:
      print("Error in server loop")
      sys.exit(e)
      


