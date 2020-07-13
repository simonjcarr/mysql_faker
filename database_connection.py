import mysql.connector
import os

def connect_db():
  try:
    db = mysql.connector.connect (
      host=os.getenv("DB_HOST"),
      user=os.getenv("DB_USER"),
      passwd=os.getenv("DB_PASSWORD"),
      port=os.getenv("DB_PORT")
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

