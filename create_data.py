from faker import Faker
from faker.providers import internet
from faker.providers import phone_number
from faker.providers import company
from faker.providers import ssn
from database_connection import connect_db, close_db
from create_database import create_db
import random
import json
import collections
import time
from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

fake = Faker()
seed = 0
Faker.seed(seed)
random.seed(0)
fake.add_provider(internet)
fake.add_provider(phone_number)
fake.add_provider(company)

db = connect_db()
cursor = db.cursor(dictionary=True)

words_engineering = []
row_data = {}
def clearTable(table_name):
  cursor.execute("TRUNCATE TABLE %s"%(table_name))
  db.commit()

def random_number(start, end, prec=0):
  number = round(random.uniform(start,end),prec)
  if(prec == 0):
    return int(number)
  return number

def engineering_words(numWords=3):
  global words_engineering
  if(len(words_engineering) == 0):
    file_eng = open('words/engineering.txt')
    words_engineering = [line.strip() for line in file_eng]
    file_eng.close()
  words = random.sample(words_engineering, numWords)
  return ' '.join(words)

def getRecordFromTable(command):
  commands = command.split("|")
  table = commands[1]
  field = commands[3]

  if(str(commands[2]).lower() == 'random'):
    #Get a random record
    cursor.execute("SELECT %s FROM %s ORDER BY RAND() LIMIT 1"%(field, table))
    record = cursor.fetchone()
    return record[field]

  if(str(commands[2]).lower() == 'first'):
    #todo get first record in table
    pass
  if(str(commands[2]).lower() == 'last'):
    #todo get last record in table
    pass

def date_greater_than_field(field_name):
  startDate = datetime.strptime(row_data[field_name].strip('"'), "%Y-%m-%d")
  startDays = abs((startDate - datetime.now()).days)
  dateObj = fake.date_between(start_date="-"+str(startDays)+"days", end_date='today')
  mysqlDate = dateObj.strftime('%Y-%m-%d')
  return str(mysqlDate)


def date_between(start_date, end_date):
  dateObj = fake.date_between(start_date, end_date)
  mysqlDate = dateObj.strftime('%Y-%m-%d')
  return str(mysqlDate)

def getFakeData(fakeList, fieldName, data=None):
  if(fakeList == None or type(fakeList) is not list):
    return

  fakeCommands = []
  fakeWeights = []
  for cmd in fakeList:
    fakeCommands.append(cmd['command'])
    fakeWeights.append(cmd['percent'])
  print(fakeCommands)
  fakeString = random.choices(fakeCommands, fakeWeights)[0]
  
  
  #Check if this fake command is get data from the data variable
  if(str(fakeString[0:4]).lower() == 'each'):
    if(data is None):
      print("Warning: Your fake command was 'each', but no data was provided")
      return ""
    else:
      #Get the field name with which holds the data to return
      row_data[fieldName] = fakeString[5:]
      field = fakeString[5:]
      try:
        #If we can find the data field return the data
        row_data[fieldName] = data[field]
        return '"' + str(data[field]) + '"'
      except:
        #If we can't find the data field, generate an error message and return an empty string
        print("Error: Unable to find specified field '%s' in the data provided"%(field))
        return ""

  if(str(fakeString[0:5]).lower() == 'table'):
    #Get data from a table
    value = getRecordFromTable(fakeString)
    row_data[fieldName] = value
    return "'" + str(value) + "'"
  #We must have a proper faker command. we use eval to generate the data
  print(fakeString)
  value = eval(fakeString)
  if(type(value) is int or type(value) is float):
    row_data[fieldName] = value
    return value
  else:
    row_data[fieldName] = "\"%s\""%(value)
    return "\"%s\""%(value)

def generateData(table, qty=1, eachData=None):
  global row_data
  for _ in range(qty):
    row_data = {}
    sql = "INSERT INTO %s"%(table['name'])
    sql = sql + "("

    for field in table['fields']:
      if(field['fake'] == None or type(field['fake']) is not list):
        continue
      sql = sql + field['name'] + ","
    sql = sql[0:-1]
    sql = sql + ") values ("
    for field in table['fields']:
      if(field['fake'] == None or type(field['fake']) is not list):
        continue
      sql = sql + "" + str(getFakeData(field['fake'], field['name'], eachData)) + ","
    sql = sql[0:-1]
    sql = sql + ")"
    print(sql)
    cursor.execute(sql)
  db.commit()

def getTableRecordCount(table):
  cursor.execute("select count(*) as record_count from %s"%(table))
  result = cursor.fetchall()
  return result[0]['record_count']


def generateTableEach(table):
  #Get table name
  commands = table['fake_qty'].split("|")
  table_name = commands[2]
  
  #Get number of records from table
  record_count = getTableRecordCount(table_name)
  itter_count = 0
  limit = 500
  for offset in range(0, record_count-1,limit):
    cursor.execute("select * from %s limit %d offset %d"%(table_name,limit,offset))
    records = cursor.fetchall()
    for record in records:
      try:
        start_qty = commands[3]
      except:
        start_qty = 1
      
      try:
        end_qty = commands[4]
      except:
        end_qty = None
      
      if(end_qty is not None):
        qty = random_number(int(start_qty), int(end_qty), 0)
      else:
        qty = start_qty
      generateData(table, qty, record)

#populate the database tables with data using faker

with open("./tables.json") as f:
  fakeData = json.load(f)

#Create database
create_db(fakeData['database_name'])

#Use database
cursor.execute("USE %s"%(fakeData['database_name']))

for table in fakeData['tables']:
  # if(table['truncate']):
  #   cursor.execute("TRUNCATE TABLE %s"%(table['table_name']))
  #   db.commit()
  fake_qty = table['fake_qty']
  if(type(fake_qty) == int):
    generateData(table, fake_qty)
  elif(fake_qty[0:10] == "table|each"):
    generateTableEach(table)
close_db(db)
print("Data creation complete")
