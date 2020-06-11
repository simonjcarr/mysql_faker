import mysql.connector


def connect_db():
  try:
    db = mysql.connector.connect (
      host="127.0.0.1",
      user="root",
      passwd="password",
      # database="bae_faker"
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

