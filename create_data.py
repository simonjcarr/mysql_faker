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
import os, shutil
from websocket import create_connection
import csv
from dicttoxml import dicttoxml

ws = None


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

jobData = None
error = False
current_table = None

def openWebsocket():
  global ws
  ws = create_connection("ws://localhost:3333/adonis-ws")
  ws.send(json.dumps({
    "t": 1,
    "d": {"topic": 'job'}
  }))


def wsMessage(message, status):
  global current_table
  ws.send(json.dumps({
    "t": 7,
    "d": {
      "topic": "job",
      "event": "message",
      "data": {"database_id": jobData['id'], "job_id": jobData['job_id'], "user_id": jobData['user_id'], "database_name": jobData['database_name'], "message": str(message), "status": status, "table": current_table}
    }
  }))

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
  global error
  if(fake_list == None or type(fake_list) is not list or len(fake_list) == 0):
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
      except Exception as e:
        error = True
        #If we can't find the data field, generate an error message and return an empty string
        wsMessage("Error: Unable to find specified field '%s' in the data provided"%(field), "error")
        print("Error: Unable to find specified field '%s' in the data provided"%(field))
        return ""

  if(str(fake_string[0:5]).lower() == 'table'):
    #Get data from a table
    value = getRecordFromTable(fake_string)
    row_data[field_name] = value
    return "'" + str(value) + "'"
  #We must have a proper faker command. we use eval to generate the data
  #print(fakeString)
  try:
    value = eval(fake_string)
    if(type(value) is int or type(value) is float):
      row_data[field_name] = value
      return value
    elif type(value) is list:
      value = ' '.join(value)
      return "\"%s\""%(value)
    else:
      row_data[field_name] = "\"%s\""%(value)
      return "\"%s\""%(value)
  except Exception as e:
    error = True
    wsMessage(e, "error")

def generateData(table, qty=1, eachData=None):
  global row_data
  global row_count
  global error
  try:
    for _ in range(qty):
      row_data = {}
      sql = "INSERT INTO %s"%(table['table_name'])
      sql = sql + "("
      for field in table['fields']:
        field_def = field
        if(field['fake'] == None or type(field['fake']) is not list  or len(field['fake']) == 0):
          continue
        sql = sql + field['name'] + ","
      sql = sql[0:-1]
      sql = sql + ") values ("
      for field in table['fields']:
        if(field['fake'] == None or type(field['fake']) is not list  or len(field['fake']) == 0):
          continue
        sql = sql + "" + str(getFakeData(field['fake'], field['name'], eachData)) + ","
      sql = sql[0:-1]
      sql = sql + ");"
      row_count = row_count + 1
      cursor.execute(sql)
    db.commit()
  except Exception as e:
    error = True
    wsMessage(e, "error")

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


def writeDatabaseRecordsToCSV(records, export, folder):
  wsMessage("Generating export file %s"%(export['file_name']),'success')
  try:
    with open(os.path.join(folder, export['file_name']), "w") as f:
      w = csv.DictWriter(f, records[0].keys())
      w.writerow(dict((fn,fn) for fn in records[0].keys()))
      w.writerows(records)
  except Exception as e:
    wsMessage("Error generating file %s"%(export['file_name']), 'error')
    wsMessage(e,'error')

def writeDatabaseRecordsToXML(records, export, folder):
  wsMessage("Generating export file %s"%(export['file_name']),'success')
  try:
    xml = dicttoxml(records)
    with open(os.path.join(folder, export['file_name']), "wb") as f:
      f.write(xml)
  except Exception as e:
    wsMessage("Error generating file %s"%(export['file_name']), 'error')
    wsMessage(e,'error')

def writeDatabaseRecordsToMySQL(records, export, folder):
  wsMessage("Generating export file %s"%(export['file_name']),'success')
  try:
    for record in records:
      values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in record.values())
      columns = ', '.join(record.keys())
      sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (export['sql_insert_table'], columns, values)
      with open(os.path.join(folder, export['file_name']), "a") as f:
        f.write(sql + "\n")
  except Exception as e:
    wsMessage("Error generating file %s"%(export['file_name']), 'error')
    wsMessage(e,'error')

def exportTable(export, job, folder):
  try:
    cursor.execute("use %s"%(job['database_name']))
    cursor.execute("select * from %s"%(export['table_name']))
    records = cursor.fetchall()
    if export['format'] == 'csv':
      writeDatabaseRecordsToCSV(records, export, folder)
    elif export['format'] == 'xml':
      writeDatabaseRecordsToXML(records, export, folder)
    elif export['format'] == 'mysql':
      writeDatabaseRecordsToMySQL(records, export, folder)
    wsMessage('Exported table %s to file %s'%(export['table_name'], export['file_name']), 'success')
  except Exception as e:
    wsMessage(e, 'error')

def exportSQL(export, job, folder):
  try:
    cursor.execute("use %s"%(job['database_name']))
    cursor.execute(export['sql'])
    records = cursor.fetchall()
    if export['format'] == 'csv':
      writeDatabaseRecordsToCSV(records, export, folder)
    elif export['format'] == 'xml':
      writeDatabaseRecordsToXML(records, export, folder)
    elif export['format'] == 'mysql':
      writeDatabaseRecordsToMySQL(records, export, folder)
    wsMessage('Exported SQL Result to file %s'%(export['file_name']), 'success')
  except Exception as e:
    wsMessage(e, 'error')

def createExportFolder(job):
  folder = "export_db_%s"%(job['database_name'])
  try:
    os.mkdir(folder)
    return folder
  except Exception as e:
    return folder

def clearExportFolder(folder):
    for filename in os.listdir(folder):
      file_path = os.path.join(folder, filename)
      try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
          os.unlink(file_path)
        elif os.path.isdir(file_path):
          shutil.rmtree(file_path)
      except Exception as e:
        wsMessage("Failed to clear export folder", "error")


def processExports(job):
  try:
    database_id = job['id']
    cursor.execute("use faker;")
    cursor.execute("select * from `exports` e left join tbls t on t.id = e.tbl_id where e.database_id = %d;"%(database_id))
    exports = cursor.fetchall()
    folder = createExportFolder(job)
    clearExportFolder(folder)
    for export in exports:
      if export['tbl_id'] is not None:
        exportTable(export, job, folder)
      else:
        pass
        #exportSQL(export, job, folder)
  except Exception as e:
    wsMessage(e, 'error')

def run(fakeData, job, sema):
  openWebsocket()
  global jobData
  jobData = job
  global table_count
  global row_count
  global error
  global current_table

  try:
    #Create database
    create_db(fakeData, True)
    wsMessage("Created database %s"%(fakeData['database_name']), "running")
    #Use database
    cursor.execute("USE %s"%(fakeData['database_name']))
    
    for table in fakeData['tables']:
      current_table = table['table_name']
      if error == True:
        wsMessage("Ending job run due to error, see logs above for more details.", "error")
        ws.close()
        sema.release()
        return
      wsMessage("Processing table %s"%(table['table_name']), "running")
      table_count = table_count + 1
      fake_qty = table['fake_qty']
      if(type(fake_qty) == int):
        generateData(table, fake_qty)
      elif(fake_qty[0:10] == "table|each"):
        generateTableEach(table)
      elif(fake_qty[0:3] == "BOM"):
        generateBOM(table, fake_qty)
    
    #Process exports
    processExports(job)
    cursor.execute("use faker;")
    db.commit()
    wsMessage("Database population complete created %d tables and %d records"%(table_count, row_count), "complete")
    ws.close()
    sema.release()

  except Exception as e:
    wsMessage(e, "error")
    ws.close()
    sema.release()
  
