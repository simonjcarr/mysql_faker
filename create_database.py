import json
from database_connection import connect_db, close_db
#print("Creating database")
db = connect_db()
cursor = db.cursor()

# with open("./tables.json") as f:
#   tables = json.load(f)

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

  strType = field['data_type']

  if(field['data_type'].upper() == 'VARCHAR'):
    strType = "VARCHAR"

  if(field['data_type'].upper() == 'TEXT'):
    strType = "TEXT"

  if( field['data_type'].upper() == 'INT'):
    strType = "INT"

  if(field['data_type'].upper() == 'FLOAT'):
    strType = "FLOAT"

  if(field['data_type'].upper() == 'DATETIME'):
    strType = 'DATETIME'

  if(addSize):
    strType = strType + " (%s)"%(field['size'])

  return strType

def addIndexes(fields):
  indexCount = 0
  indexStr = "INDEX ("
  for field in fields:
    if field['index'] == True:
      indexCount = indexCount + 1
      indexStr = indexStr + field['name'] + ","
  if indexCount > 0:
    indexStr = ", " + indexStr[:-1] + ")"
  else:
    indexStr = ""
  return indexStr

def create_db(fake_data, drop=True):
  db_name = fake_data['database_name']
  #Drop the database if drop == True
  try:
    if(drop):
      cursor.execute("DROP DATABASE IF EXISTS %s"%(db_name))
      db.commit()
  except Exception as e:
    print("error droping database")
    print(e)
  #Create the database
  try:
    cursor.execute("CREATE DATABASE IF NOT EXISTS " + db_name)
    db.commit()
  except Exception as e:
    print("Error creating database: " + str(e))
    return False

  #Switch to the new database
  cursor.execute("use " + db_name)
  for table in fake_data['tables']:
    name = table["table_name"]
    fields = table["fields"]
    sql = "CREATE TABLE IF NOT EXISTS " + table["table_name"] + "("
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
    sql = sql + addIndexes(table["fields"])
    sql = sql + ");"
    cursor.execute(sql)
    db.commit()

#create_db(tables['database_name'], drop=tables['drop'])

