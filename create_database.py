import json
from database_connection import connect_db, close_db
db = connect_db()
cursor = db.cursor()

with open("./tables.json") as f:
  tables = json.load(f)

def formatDefault(field):
  if(field['default'] == "" or field['type'].upper() == "TEXT"):
    return ""
  if(type(field['default']) is int or type(field['default']) is float):
    return "DEFAULT " + str(field['default'])
  elif(type(field['default']) is str):
    return "DEFAULT '" + str(field['default']) + "'"
  else:
    print("Check default values in table. Something went wrong")
    return ""

def formatNull(field):
  if(field['ai']== True):
    return ""
  if(field['null'] == True):
    return ""
  else:
    return "NOT NULL"

def formatAI(field):
  if(field['ai']):
    return "AUTO_INCREMENT"
  else:
    return ""

def formatPK(field):
  if(field['pk']):
    return "PRIMARY KEY"
  else:
    return ""

def formatType(field):
  if((type(field['size']) is str and len(field['size']) > 0) or type(field['size']) is int ):
    addSize = True
  else:
    addSize = False

  strType = field['type']

  if(field['type'].upper() == 'VARCHAR'):
    strType = "VARCHAR"

  if(field['type'].upper() == 'TEXT'):
    strType = "TEXT"

  if( field['type'].upper() == 'INT'):
    strType = "INT"

  if(field['type'].upper() == 'FLOAT'):
    strType = "FLOAT"

  if(addSize):
    strType = strType + " (%s)"%(field['size'])

  return strType

def create_db(db_name, drop=False):

  #Drop the database if drop == True
  if(drop):
    cursor.execute("DROP DATABASE IF EXISTS %s"%(db_name))
    db.commit()

  #Create the database
  try:
    cursor.execute("CREATE DATABASE IF NOT EXISTS " + db_name)
    db.commit()
    print("Database %s created" % (db_name))
  except Exception as e:
    print("Error creating database: " + str(e))
    return False

  #Switch to the new database
  cursor.execute("use " + db_name)
  print("Switching to databse %s " % (db_name))

  for table in tables['tables']:
    name = table["name"]
    fields = table["fields"]
    sql = "CREATE TABLE IF NOT EXISTS " + table["name"] + "("
    for field in table["fields"]:
      sql = sql + "\n"
      sql = sql + field["name"] + " "
      sql = sql + formatType(field) + " "
      sql = sql + formatNull(field)+ " "
      sql = sql + formatAI(field) + " "
      sql = sql + formatPK(field) + " "
      sql = sql + formatDefault(field)
      sql = sql + ","
    sql = sql[0:-1]
    sql = sql + ");"
    cursor.execute(sql)
    db.commit()

create_db(tables['database_name'], drop=tables['drop'])
close_db(db)
