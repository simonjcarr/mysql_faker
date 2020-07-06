import mysql.connector


def connect_db():
  try:
    db = mysql.connector.connect (
      host="192.168.10.3",
      user="root",
      passwd="Pr35t0nTh30",
    )
    #print("Connected to database server")
    return db
  except:
    return False

def close_db(db):
  try:
    
    db.close()
    #print("Database server connection closed")
    return True
  except:
    return False

