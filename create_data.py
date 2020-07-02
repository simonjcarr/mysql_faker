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
import sys
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
import os
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

table_count = 0
row_count = 0
fake_string = ""

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

def generateBOM(table, command):
  # BOM|qty_ASO|min_children|max_children|min_levels|max_levels
  #Get the command values
  commands = command.split("|")
  aso_qty = int(commands[1])
  #Maximum child parts each ASO should have
  max_children = int(commands[2])
  #Maximum levels each BOM should have
  max_levels = int(commands[3])
  #Generate ASO top level parts
  for _ in range(aso_qty):
    aso_items = []
    #Generate a fake ASO part number
    aso_item = {"parent_item": "", "item": fake.ssn(), "level": 0 }
    generateData(table, 1, aso_item)
    # add this top level aso to the list
    aso_items.append(aso_item)
    #keep track of the highest level in the BOM we have reached
    max_level = 1
    for _ in range(random_number(10, max_children, 0)):
      #Generate a random BOM level number
      #if max_level is less than max_levels then maximum random number should be max_level + 1
      # else maximum random number should be max_levels
      level = random_number(1, (max_level + 1) if max_level < max_levels else max_levels, 0)
      if level > max_level:
        max_level = level
      #Get random item from ASO list
      asoListItem = random.choice(aso_items)
      
      newLevel = asoListItem['level'] + 1
      tryCount = 0
      while newLevel >= max_levels:
        asoListItem = random.choice(aso_items)
        newLevel = asoListItem['level'] + 1
        tryCount = tryCount + 1
        if(tryCount > 100):
          sys.exit("could not find a level below or equal to max_aso_levels in over 100 tries")
      item = { "parent_item": asoListItem['item'], "item": fake.ssn(), "level": newLevel}
      aso_items.append(item)
      generateData(table, 1, item)

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

def date_greater_than_field(field_name, max_date='today'):
  #@TODO If value of max_date is less than field_name return field_name value
  start_date = datetime.strptime(row_data[field_name].strip('"'), "%Y-%m-%d")
  #Check if an absolute date has been given by prepending with 'date:' or a string date i.e. +1y
  
  if(str(max_date)[0:5] != 'date:'):
    end_date = fake.date_between(max_date, max_date)
  else:
    end_date = datetime.strptime(max_date[5:], "%Y-%m-%d")
  
  #Get the random date
  try:
    dateObj = fake.date_between_dates(start_date, end_date)
  except:
    #An exception will usually be caused by max_date being less than the value 
    #of field_name. In this case we just return end_date
    dateObj = end_date
  #Format the date for use in MySQL
  mysqlDate = dateObj.strftime('%Y-%m-%d')
  return str(mysqlDate)

def get_offset_days_from_strtotime(offset_string):
  #offset_string should look like -1y, +1y, -2w, +1m etc 
  try:
    offset_date = fake.date_between(offset_string, 'today')
  except:
    offset_date = fake.date_between('today', offset_string)
  today = date.today()
  offset = offset_date - today
  return offset.days

def get_offset_days_from_date(offset_date):
  today = date.today()
  offset = offset_date - today
  return offset.days
  
def date_less_than_field(field_name, min_date='-1y'):
  
  #@TODO If value of max_date is less than field_name return field_name value
  end_date = datetime.strptime(row_data[field_name].strip('"'), "%Y-%m-%d")
  #Check if an absolute date has been given by prepending with 'date:' or a string date i.e. +1y
  
  if(str(min_date)[0:5] != 'date:'):
    #Start date should be field_name - -1y
    offset_days = get_offset_days_from_strtotime(min_date)
    start_date = end_date - timedelta(days=abs(offset_days))
  else:
    start_date_ref = datetime.strptime(min_date[5:], "%Y-%m-%d").date()
  try:
    calculated_date = fake.date_between(start_date_ref, end_date)
  except:
    calculated_date = start_date_ref
  return calculated_date.strftime('%Y-%m-%d')

def number_greater_than_field(field_name, max=100):
  field_value = row_data[field_name]
  if(field_value == max):
    return field_value
  if(type(field_value) is not float and type(field_value) is not int):
    try:
      field_value = float(field_value)
    except Exception as e:
      print("Error in get_number_greater_than_field: %s"%(e))
      sys.exit()
  return random_number(field_value, max, 0 if type(field_value) is int else 2)

def number_less_than_field(field_name, min=0, allow_negative=False):
  field_value = row_data[field_name]
  if(field_value == min):
    return field_value
  if(type(field_value) is not float and type(field_value) is not int):
    try:
      field_value = float(field_value)
    except Exception as e:
      print("Error in get_number_greater_than_field: %s"%(e))
      sys.exit()
  number = random_number(min, field_value, 0 if type(field_value) is int else 2)
  #check if number is negative and allow_negative is False
  if(number < 0 and not allow_negative):
    number = 0
  return number

def date_between(start_date, end_date):
  dateObj = fake.date_between(start_date, end_date)
  mysqlDate = dateObj.strftime('%Y-%m-%d')
  return str(mysqlDate)

def getFakeData(fake_list, field_name, data=None):
  global fake_string
  if(fake_list == None or type(fake_list) is not list):
    return

  fake_commands = []
  fake_weights = []
  for cmd in fake_list:
    fake_commands.append(cmd['command'])
    fake_weights.append(cmd['percent'])
  #print(fakeCommands)
  fake_string = random.choices(fake_commands, fake_weights)[0]
  
  
  #Check if this fake command is get data from the data variable
  if(str(fake_string[0:4]).lower() == 'each'):
    if(data is None):
      print("Warning: Your fake command was 'each', but no data was provided")
      return ""
    else:
      #Get the field name with which holds the data to return
      row_data[field_name] = fake_string[5:]
      field = fake_string[5:]
      try:
        #If we can find the data field return the data
        row_data[field_name] = data[field]
        return '"' + str(data[field]) + '"'
      except:
        #If we can't find the data field, generate an error message and return an empty string
        print("Error: Unable to find specified field '%s' in the data provided"%(field))
        return ""

  if(str(fake_string[0:5]).lower() == 'table'):
    #Get data from a table
    value = getRecordFromTable(fake_string)
    row_data[field_name] = value
    return "'" + str(value) + "'"
  #We must have a proper faker command. we use eval to generate the data
  #print(fakeString)
  value = eval(fake_string)
  if(type(value) is int or type(value) is float):
    row_data[field_name] = value
    return value
  else:
    row_data[field_name] = "\"%s\""%(value)
    return "\"%s\""%(value)

def generateData(table, qty=1, eachData=None):
  global row_data
  global row_count
  
  for _ in range(qty):
    row_data = {}
    sql = "INSERT INTO %s"%(table['name'])
    sql = sql + "("
    for field in table['fields']:
      field_def = field
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
    sql = sql + ");"
    #print(sql)
    row_count = row_count + 1
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
create_db(fakeData['database_name'], True)

#Use database
cursor.execute("USE %s"%(fakeData['database_name']))
print("Populating database with fake data")

for table in fakeData['tables']:
  print("Processing table %s"%(table['name']))
  # if(table['truncate']):
  #   cursor.execute("TRUNCATE TABLE %s"%(table['table_name']))
  #   db.commit()
  table_count = table_count + 1
  fake_qty = table['fake_qty']
  
  if(type(fake_qty) == int):
    generateData(table, fake_qty)
  elif(fake_qty[0:10] == "table|each"):
    generateTableEach(table)
  elif(fake_qty[0:3] == "BOM"):
    generateBOM(table, fake_qty)
close_db(db)
print("Database population complete created %d tables and %d records"%(table_count, row_count))
