import threading
from faker import Faker
import multiprocessing
from faker.providers import internet
from faker.providers import phone_number
from faker.providers import company
from faker.providers import ssn
from database_connection import connect_db, close_db
from create_database import create_db
from random import Random
import math
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
import urllib.request
import urllib.parse
import re


maxThreads = 3
threadLimiter = threading.BoundedSemaphore(maxThreads)
class Job(threading.Thread):
  def __init__(self, jsonData, jobData):
    #super().__init__()
    threading.Thread.__init__(self)

    self.fake = Faker()
    self.seed = 0
    self.random = Random(self.seed)
    Faker.seed(self.seed)
    self.fake.add_provider(internet)
    self.fake.add_provider(phone_number)
    self.fake.add_provider(company)

    self.jsonData = jsonData
    self.fakeData = jsonData
    self.jobData = jobData
    self.ws = None
    self.table_count = 0
    self.row_count = 0
    self.fake_string = ""
    self.words_engineering = []
    self.row_data = {}

    #self.jobData = None
    self.error = False
    self.current_table = None
    self.last_table = None
    self.jobDB = connect_db()
    self.jobCursor = self.jobDB.cursor(dictionary=True)
    try:
      self.jobCursor.execute("use %s"%(self.jobData['database_name']))
    except Exception as e:
      #Create database     
      create_db(self.fakeData, True)
      self.jobCursor.execute("use %s"%(self.jobData['database_name']))
    self.fakerDB = connect_db()
    self.fakerCursor = self.fakerDB.cursor(dictionary=True)
    self.fakerCursor.execute("use %s"%(os.getenv("FAKER_DATABASE")))
    self.tabledata = {}
    self.sqlValues = ""
    self.valuesCount = 0
    self.sql_insert = ""
    self.newTable = True
    self.table_each_row_count_source = 0 #Each record is source table
    self.table_each_row_count_destination = 0 #Each record in destination table. There can be multiples of desination records for each source record
    try:
      from collections import OrderedDict
    except ImportError:
      OrderedDict = dict

  
  def openWebsocket(self):
    self.ws = create_connection(os.getenv("WS_URL"), on_error = self.ws_error)
    self.ws.send(json.dumps({
      "t": 1,
      "d": {"topic": 'job'}
    }))

  def ws_error(self, ws, error):
    print("web socket error")
    print(error)
    print("attempting to reopen websocket")
    self.openWebsocket()


  def wsMessage(self, message, status, message_type="log"):
    try:
      self.ws.send(json.dumps({
        "t": 7,
        "d": {
          "topic": "job",
          "event": "message",
          "data": {"database_id": self.jobData['id'], "job_id": self.jobData['job_id'], "user_id": self.jobData['user_id'], "database_name": self.jobData['database_name'], "message": str(message), "status": status, "table": self.current_table, "message_type": message_type}
        }
      }))
    except Exception as e:
      print("Websocket error")
      print(e)
      self.openWebsocket()

  def clearTable(self, table_name):
    self.jobCursor.execute("TRUNCATE TABLE %s"%(table_name))
    self.jobDB.commit()

  def generateBOM(self, table, command):
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
      aso_item = {"parent_item": "", "item": self.fake.ssn(), "level": 0 }
      self.generateData(table, 1, aso_item)
      # add this top level aso to the list
      aso_items.append(aso_item)
      #keep track of the highest level in the BOM we have reached
      max_level = 1
      for _ in range(self.random_number(10, max_children, 0)):
        #Generate a random BOM level number
        #if max_level is less than max_levels then maximum random number should be max_level + 1
        # else maximum random number should be max_levels
        level = self.random_number(1, (max_level + 1) if max_level < max_levels else max_levels, 0)
        if level > max_level:
          max_level = level
        #Get random item from ASO list
        asoListItem = self.random.choice(aso_items)
        
        newLevel = asoListItem['level'] + 1
        tryCount = 0
        while newLevel >= max_levels:
          asoListItem = self.random.choice(aso_items)
          newLevel = asoListItem['level'] + 1
          tryCount = tryCount + 1
          if(tryCount > 100):
            sys.exit("could not find a level below or equal to max_aso_levels in over 100 tries")
        item = { "parent_item": asoListItem['item'], "item": self.fake.ssn(), "level": newLevel}
        aso_items.append(item)
        self.generateData(table, 1, item)

  def const(self, value):
    return value
  
  def null(self):
    return None

  def random_number(self, start, end, prec=0):
    number = round(self.random.uniform(start,end), prec)
    if(prec == 0):
      return int(math.ceil(number))
    return number

  def engineering_words(self, numWords=3):
    if(len(self.words_engineering) == 0):
      file_eng = open('words/engineering.txt')
      self.words_engineering = [line.strip() for line in file_eng]
      file_eng.close()
    words = self.random.sample(self.words_engineering, numWords)
    return ' '.join(words)

  def getRecordFromTableStored(self, command, database_name):
    commands = command.split("|")
    table = commands[1]
    field = commands[3]
    #get all data from table and store in local variable
    if table not in self.tabledata:
      self.jobCursor.execute("SELECT * FROM %s ORDER BY RAND()"%(table))
      self.tabledata[table] = self.jobCursor.fetchall()
    if(str(commands[2]).lower() == 'random'):
      #Get a random record
      #self.jobCursor.execute("SELECT %s FROM %s ORDER BY RAND() LIMIT 1"%(field, table))
      #record = self.jobCursor.fetchone()
      record = self.random.choice(self.tabledata[table])
      if record[field] == None:
        print("record is None")
      return record[field]
    if(str(commands[2]).lower() == 'first'):
      #todo get first record in table
      pass
    if(str(commands[2]).lower() == 'last'):
      #todo get last record in table
      pass
  
  def getRecordFromTable(self, command, database_name):
    return self.getRecordFromTableStored(command, database_name)
    return
    commands = command.split("|")
    table = commands[1]
    field = commands[3]
    if(str(commands[2]).lower() == 'random'):
      #Get a random record
      self.jobCursor.execute("SELECT %s FROM %s ORDER BY RAND() LIMIT 1"%(field, table))
      record = self.jobCursor.fetchone()
      return record[field]

    if(str(commands[2]).lower() == 'first'):
      #todo get first record in table
      pass
    if(str(commands[2]).lower() == 'last'):
      #todo get last record in table
      pass

  def date_greater_than_field(self, field_name, max_date='today'):
    #@TODO If value of max_date is less than field_name return field_name value
    if(self.row_data[field_name] is None):
      return None
    start_date = datetime.strptime(self.row_data[field_name].strip('"'), "%Y-%m-%d")
    #Check if an absolute date has been given by prepending with 'date:' or a string date i.e. +1y
    
    if(str(max_date)[0:5] != 'date:'):
      end_date = self.fake.date_between(max_date, max_date)
    else:
      end_date = datetime.strptime(max_date[5:], "%Y-%m-%d")
    
    #Get the random date
    try:
      dateObj = self.fake.date_between_dates(start_date, end_date)
    except:
      #An exception will usually be caused by max_date being less than the value 
      #of field_name. In this case we just return end_date
      dateObj = end_date
    #Format the date for use in MySQL
    mysqlDate = dateObj.strftime('%Y-%m-%d')
    return str(mysqlDate)

  def get_offset_days_from_strtotime(self, offset_string):
    #offset_string should look like -1y, +1y, -2w, +1m etc 
    try:
      offset_date = self.fake.date_between(offset_string, 'today')
    except:
      offset_date = self.fake.date_between('today', offset_string)
    today = date.today()
    offset = offset_date - today
    return offset.days

  def get_offset_days_from_date(self, offset_date):
    today = date.today()
    offset = offset_date - today
    return offset.days
    
  def date_less_than_field(self, field_name, min_date='-1y'):
    if(self.row_data[field_name] is None):
      return None
    #@TODO If value of max_date is less than field_name return field_name value
    end_date = datetime.strptime(self.row_data[field_name].strip('"'), "%Y-%m-%d")
    #Check if an absolute date has been given by prepending with 'date:' or a string date i.e. +1y
    
    if(str(min_date)[0:5] != 'date:'):
      #Start date should be field_name - -1y
      offset_days = self.get_offset_days_from_strtotime(min_date)
      start_date = end_date - timedelta(days=abs(offset_days))
    else:
      start_date_ref = datetime.strptime(min_date[5:], "%Y-%m-%d").date()
    try:
      calculated_date = self.fake.date_between(start_date_ref, end_date)
    except:
      calculated_date = start_date_ref
    return calculated_date.strftime('%Y-%m-%d')

  def number_greater_than_field(self, field_name, max=100):
    field_value = self.row_data[field_name]
    if(field_value == max):
      return field_value
    if(type(field_value) is not float and type(field_value) is not int):
      try:
        field_value = float(field_value)
      except Exception as e:
        print("Error in get_number_greater_than_field: %s"%(e))
        sys.exit()
    return self.random_number(field_value, max, 0 if type(field_value) is int else 2)

  def number_less_than_field(self, field_name, min=0, allow_negative=False):
    field_value = self.row_data[field_name]
    if(field_value == min):
      return field_value
    if(type(field_value) is not float and type(field_value) is not int):
      try:
        field_value = float(field_value)
      except Exception as e:
        print("Error in get_number_greater_than_field: %s"%(e))
        sys.exit()
    number = self.random_number(min, field_value, 0 if type(field_value) is int else 2)
    #check if number is negative and allow_negative is False
    if(number < 0 and not allow_negative):
      number = 0
    return number

  def date_between(self, start_date, end_date):
    dateObj = self.fake.date_between(start_date, end_date)
    mysqlDate = dateObj.strftime('%Y-%m-%d')
    return str(mysqlDate)

  def row_count_source(self):
    return self.table_each_row_count_source

  def row_count_destination(self):
    return self.table_each_row_count_destination
  
  def getFakeData(self, fake_list, field_name, data=None):
    
    if(fake_list == None or type(fake_list) is not list or len(fake_list) == 0):
      return

    fake_commands = []
    fake_weights = []
    for cmd in fake_list:
      fake_commands.append(cmd['command'])
      fake_weights.append(cmd['percent'])
    #print(fakeCommands)
    self.fake_string = self.random.choices(fake_commands, fake_weights)[0]
    
    
    #Check if this fake command is get data from the data variable
    if(str(self.fake_string[0:4]).lower() == 'each'):
      if(data is None):
        print("Warning: Your fake command was 'each', but no data was provided")
        return ""
      else:
        #Get the field name with which holds the data to return
        self.row_data[field_name] = self.fake_string[5:]
        field = self.fake_string[5:]
        try:
          #If we can find the data field return the data
          if data[field] is None:
            self.row_data[field_name] = None
            return "null"
          else:
            self.row_data[field_name] = data[field]
            return '"' + str(data[field]) + '"'
        except Exception as e:
          self.error = True
          #If we can't find the data field, generate an error message and return an empty string
          self.wsMessage("Error: Unable to find specified field '%s' in the data provided"%(field), "error")
          print("Error: Unable to find specified field '%s' in the data provided"%(field))
          return ""

    if(str(self.fake_string[0:5]).lower() == 'table'):
      #Get data from a table
      value = self.getRecordFromTable(self.fake_string, self.jobData['database_name'])
      self.row_data[field_name] = value
      return "'" + str(value) + "'"
    #We must have a proper faker command. we use eval to generate the data
    #print(fakeString)
    try:
      value = eval(self.fake_string)
      if(type(value) is int or type(value) is float):
        self.row_data[field_name] = value
        return value
      elif type(value) is list:
        value = ' '.join(value)
        return "\"%s\""%(value)
      else:
        if value is None:
          self.row_data[field_name] = None
          return "null"
        else:
          self.row_data[field_name] = "\"%s\""%(value)
          return "\"%s\""%(value)
    except Exception as e:
      self.error = True
      self.wsMessage(e, "error")

  def generateDataExtendedInserts(self, table, qty=1, eachData=None):
    try:
      # try:
      #   if table['table_name'] != self.last_table['table_name'] and self.last_table is not None and len(self.sqlValues) > 0:
      #     self.jobDB.commit()
      #     sql = "INSERT INTO %s"%(self.last_table['table_name'])
      #     sql = sql + "("
      #     for field in self.last_table['fields']:
      #       field_def = field
      #       if(field['fake'] == None or type(field['fake']) is not list  or len(field['fake']) == 0):
      #         continue
      #       sql = sql + field['name'] + ","
      #     sql = sql[0:-1]
      #     sql = sql + ") values "   
      #     self.sql_insert = sql

      #     sqlStatement = sql + self.sqlValues[:-1]
      #     self.jobCursor.execute(sqlStatement)
      #     self.jobDB.commit()
      #     self.sqlValues = ""
      #     self.valuesCount = 0
      # except Exception as e:
      #   pass
      sql = "INSERT INTO %s"%(table['table_name'])
      sql = sql + "("
      for field in table['fields']:
        field_def = field
        if(field['fake'] == None or type(field['fake']) is not list  or len(field['fake']) == 0):
          continue
        sql = sql + field['name'] + ","
      sql = sql[0:-1]
      sql = sql + ") values "   
      self.sql_insert = sql
      self.table_each_row_count_destination = 0
      for _ in range(qty):
        self.table_each_row_count_destination = self.table_each_row_count_destination + 1
        self.row_data = {}
        self.sqlValues = self.sqlValues + "("
        for field in table['fields']:
          if(field['fake'] == None or type(field['fake']) is not list  or len(field['fake']) == 0):
            continue
          self.sqlValues = self.sqlValues + "" + str(self.getFakeData(field['fake'], field['name'], eachData)) + ","
        self.sqlValues = self.sqlValues[0:-1]
        self.sqlValues = self.sqlValues + "),"
        self.valuesCount = self.valuesCount + 1
        if(self.valuesCount >= 1500):
          sqlStatement = self.sql_insert + self.sqlValues[:-1]
          self.jobCursor.execute(sqlStatement)
          self.jobDB.commit()
          self.valuesCount = 0
          self.sqlValues = ""
        self.row_count = self.row_count + 1
      if(len(self.sqlValues) > 0):
        pass
        # sqlStatement = sql + self.sqlValues[:-1]
        # self.jobCursor.execute(sqlStatement)
        # self.valuesCount = 0
        # self.sqlValues = ""
      # self.jobDB.commit()
      self.last_table = table
      self.newTable = False
    except Exception as e:
      self.error = True
      self.wsMessage(e, "error")
      self.wsMessage(sqlStatement, 'error')

  def generateData(self, table, qty=1, eachData=None):
    self.generateDataExtendedInserts(table, qty, eachData)
    return
    try:
      #Create a file to write sql to
      sqlFile = self.jobData['database_name'] + "_" + table['table_name'] + ".sql"
      self.createSQLFile(sqlFile)
      for _ in range(qty):
        self.row_data = {}
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
          sql = sql + "" + str(self.getFakeData(field['fake'], field['name'], eachData)) + ","
        sql = sql[0:-1]
        sql = sql + ");\n"
        print(sql)
        self.row_count = self.row_count + 1
        self.jobCursor.execute(sql)
      self.jobDB.commit()
    except Exception as e:
      self.error = True
      self.wsMessage(e, "error")
      self.wsMessage(sql, 'error')


  def getTableRecordCount(self, table):
    self.jobCursor.execute("select count(*) as record_count from %s"%(table))
    result = self.jobCursor.fetchall()
    return result[0]['record_count']

  def generateTableEach(self, table):
    #Get table name
    self.jobDB.commit()
    commands = table['fake_qty'].split("|")
    table_name = commands[2]
    
    #Get number of records from table
    record_count = self.getTableRecordCount(table_name)
    itter_count = 0
    limit = 100000
    self.table_each_row_count_source = 0
    for offset in range(0, record_count-1,limit):
      self.jobCursor.execute("select * from %s limit %d offset %d"%(table_name,limit,offset))
      records = self.jobCursor.fetchall()
      
      for record in records:
        self.table_each_row_count_source = self.table_each_row_count_source + 1
        try:
          start_qty = commands[3]
        except:
          start_qty = 1
        
        try:
          end_qty = commands[4]
        except:
          end_qty = None
        
        if(end_qty is not None):
          qty = self.random_number(int(start_qty), int(end_qty), 0)
        else:
          qty = start_qty
        self.generateData(table, qty, record)

  def recordFileInDB(self, folder, export):
    try:
      database_id = export['database_id']
      export_id = export['id']
      path = os.path.join(folder, export['file_name'])
      exporttype = export['format']
      data = urllib.parse.urlencode({'database_id': database_id, 'export_id': export_id, 'path': path, 'exporttype': exporttype})
      data = data.encode('ascii')
      urllib.request.urlopen('%s/api/v1/export/file'%(os.getenv("API_URL")), data)
    except Exception as e:
      self.wsMessage("Error writing record for file %s to the database"%(export['file_name']), 'error')
      self.wsMessage(e,'error')


  def writeDatabaseRecordsToCSV(self, records, export, folder):
    self.wsMessage("Generating export file %s"%(export['file_name']),'success')
    try:
      with open(os.path.join(folder, export['file_name']), "w") as f:
        w = csv.DictWriter(f, records[0].keys())
        w.writerow(dict((fn,fn) for fn in records[0].keys()))
        w.writerows(records)
        self.recordFileInDB(folder,export)
    except Exception as e:
      self.wsMessage("Error generating file %s"%(export['file_name']), 'error')
      self.wsMessage(e,'error')

  def writeDatabaseRecordsToXML(self, records, export, folder):
    self.wsMessage("Generating export file %s"%(export['file_name']),'success')
    try:
      xml = dicttoxml(records)
      with open(os.path.join(folder, export['file_name']), "wb") as f:
        f.write(xml)
      self.recordFileInDB(folder,export)
    except Exception as e:
      self.wsMessage("Error generating file %s"%(export['file_name']), 'error')
      self.wsMessage(e,'error')

  def writeDatabaseRecordsToMySQL(self, records, export, folder):
    self.wsMessage("Generating export file %s"%(export['file_name']),'success')
    try:
      for record in records:
        values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in record.values())
        columns = ', '.join(record.keys())
        sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (export['sql_insert_table'], columns, values)
        with open(os.path.join(folder, export['file_name']), "a") as f:
          f.write(sql + "\n")
      self.recordFileInDB(folder,export)
    except Exception as e:
      self.wsMessage("Error generating file %s"%(export['file_name']), 'error')
      self.wsMessage(e,'error')

  def exportTable(self, export, folder):
    try:
      self.jobCursor.execute("use %s"%(self.jobData['database_name']))
      self.jobCursor.execute("select * from %s"%(export['table_name']))
      records = self.jobCursor.fetchall()
      if export['format'] == 'csv':
        self.writeDatabaseRecordsToCSV(records, export, folder)
      elif export['format'] == 'xml':
        self.writeDatabaseRecordsToXML(records, export, folder)
      elif export['format'] == 'mysql':
        self.writeDatabaseRecordsToMySQL(records, export, folder)
      self.wsMessage('Exported table %s to file %s'%(export['table_name'], export['file_name']), 'success')
    except Exception as e:
      self.wsMessage(e, 'error')

  def exportSQL(self, export, folder):
    try:
      self.jobCursor.execute("use %s"%(self.jobData['database_name']))
      self.jobCursor.execute(export['sql'])
      records = self.jobCursor.fetchall()
      if export['format'] == 'csv':
        self.writeDatabaseRecordsToCSV(records, export, folder)
      elif export['format'] == 'xml':
        self.writeDatabaseRecordsToXML(records, export, folder)
      elif export['format'] == 'mysql':
        self.writeDatabaseRecordsToMySQL(records, export, folder)
      self.wsMessage('Exported SQL Result to file %s'%(export['file_name']), 'success')
    except Exception as e:
      self.wsMessage(e, 'error')

  def createExportFolder(self):
    folder = os.path.join(os.getenv("EXPORT_PATH"), "export_db_%s"%(self.jobData['database_name']))
    try:
      os.mkdir(folder)
      return folder
    except Exception as e:
      return os.path.abspath(folder)

  def clearExportFolder(self, folder):
      for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
          if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
          elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
        except Exception as e:
          wsMessage("Failed to clear export folder", "error")


  def processExports(self):
    try:
      #Get the database id from the passed in job
      database_id = self.jobData['id']

      #Get exports to process for the requested database
      sql = "select e.*, t.table_name from `exports` e left join tbls t on t.id = e.tbl_id where e.database_id = %d and active = 1;"%(database_id)
      self.fakerCursor.execute(sql)
      exports = self.fakerCursor.fetchall()

      #Create a folder for the files to be put int
      folder = self.createExportFolder()
      
      #Delete any existing export files from the database
      self.fakerCursor.execute("delete from exportfiles where database_id = %d"%(database_id))
      self.fakerDB.commit()
      # Delete any existing files from the filesystem
      self.clearExportFolder(folder)

      #Process each of the exports 
      for export in exports:
        if export['tbl_id'] is not None:
          self.exportTable(export, folder)
        else:
          self.exportSQL(export, folder)
    except Exception as e:
      self.wsMessage(e, 'error')

  def run(self):
    #Connect to Database
    threadLimiter.acquire()
    try:
      self.jobRun()
    finally:
      threadLimiter.release()
    

  def jobRun(self):
    #Create database     
    create_db(self.fakeData, True)
    self.openWebsocket()
    try:
      self.wsMessage("Created database %s"%(self.fakeData['database_name']), "running")
      #Use database
      self.jobCursor.execute("USE %s"%(self.fakeData['database_name']))
      
      for table in self.fakeData['tables']:
        if len(self.sqlValues) > 0:
          sql = "INSERT INTO %s"%(self.last_table['table_name'])
          sql = sql + "("
          for field in self.last_table['fields']:
            field_def = field
            if(field['fake'] == None or type(field['fake']) is not list  or len(field['fake']) == 0):
              continue
            sql = sql + field['name'] + ","
          sql = sql[0:-1]
          sql = sql + ") values "   
          self.sql_insert = sql

          sqlStatement = sql + self.sqlValues[:-1]
          self.jobCursor.execute(sqlStatement)
          self.jobDB.commit()
          self.sqlValues = ""
          self.valuesCount = 0
          self.jobDB.commit()




        self.current_table = table['table_name']
        self.newTable = True
        if self.error == True:
          self.wsMessage("Ending job run due to error, see logs above for more details.", "error")
          self.ws.close()
          return
        self.wsMessage("Processing table %s"%(table['table_name']), "running")
        self.table_count = self.table_count + 1
        fake_qty = table['fake_qty']
        if(type(fake_qty) == int):
          self.generateData(table, fake_qty)
        elif(fake_qty[0:10] == "table|each"):
          self.generateTableEach(table)
        elif(fake_qty[0:3] == "BOM"):
          self.generateBOM(table, fake_qty)
      
      #Run the final table
      if len(self.sqlValues) > 0:
        sqlStatement = self.sql_insert + self.sqlValues[:-1]
        self.jobCursor.execute(sqlStatement)
        self.jobDB.commit()
      #Clear up
      self.tabledata = {}
      #Process exports
      self.processExports()
      self.wsMessage("Database population complete created %d tables and %d records"%(self.table_count, self.row_count), "complete")
      self.ws.close()

    except Exception as e:
      self.wsMessage(e, "error")
      self.ws.close()
