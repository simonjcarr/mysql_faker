import sys, os, time, urllib.request, json
from create_data import run
from logData import write_log
from database_connection import connect_db, close_db
from multiprocessing import Process, Semaphore

concurrency = 3


def get_job():
  db = connect_db()
  try:
    cursor = db.cursor(dictionary=True)
    cursor.execute("USE faker;")
    
    cursor.execute("SELECT j.id as job_id, d.*  FROM `jobs` j JOIN `databases` d ON d.id = `j`.`database_id` WHERE `j`.`running` = 0 LIMIT 1")
    job = cursor.fetchone()
    if job:
      cursor.execute("UPDATE `jobs` SET `running` = 1 WHERE `id` = %d"%(job['job_id']))
      db.commit()
      return job
    else:
      return None
  except Exception as e:
    sys.exit(e)

def get_json(database_id):
  
  url = "http://localhost:3333/api/v1/json/%d"%(database_id)
  with urllib.request.urlopen(url) as u:
    data = json.loads(u.read())
  return data

if __name__ == "__main__":
  sema = Semaphore(concurrency)
  while True:
    time.sleep(1)  
    try:
      job = get_job()
      if not job:
        continue
      print(job)
      print(job['job_id'])
      database_id = job['id']
      json_data = get_json(database_id)
      sema.acquire()
      Process(target=run, args=(json_data, job, sema)).start()
    except Exception as e:
      print("Error in server loop")
      sys.exit(e)

      pass
      


