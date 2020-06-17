# Introduction
Relational Faker has been designed to
* Create databases based on a structure described in a JSON file
* Populate the database with relational data
* Allow each field to include specific percentages of anomalies, so the data reflects the real life issues business face.
* Be easily customizable, so the library can be extended to meet your own business requirements.

# Installation
1. Clone this git repo
2. pip install -r requirements.txt (at the time of writing, the only dependency was the Python Faker library)


# Limitations
Currently only supports MySQL. However MySQL is ubiquitous. If you want data for any other database product, there are lots of tools available to clone a MySQL database. 

There is also far more support for MySQL in programming languages such as Python and Node. Being able to programmatically interact with the database and generate CSV, XML, JSON ...... files from the same data set was an important requirement.

# Requirements
* Python 3.x
* MySQL

# Running
To use the scripts with the built in capabilities, you only need to alter two files.



1. database_connection.py
2. tables.json

## database_connections.py
Alter this file to provide the database connection details for your server.

```python
db = mysql.connector.connect (
      host="127.0.0.1",
      user="root",
      passwd="",
    )
```
## tables.json
This file contains all the information required to generate the database, the tables and the data.


# Editing tables.json

The most simple example of the json structure that tables.json needs to contain is shown below. Further more complex examples are given further below.

```json
{
  "database_name": "web_site",
  "drop": true,
  "tables": [
    {
      "name": "users",
      "fake_qty": 100,
      "fields": [
        {
          "name": "id",
          "type": "int",
          "size": null,
          "ai": true,
          "null": false,
          "pk": true,
          "index": false,
          "default": "",
          "fake": null
        },
        {
          "name": "email",
          "type": "varchar",
          "size": 100,
          "ai": false,
          "null": false,
          "pk": false,
          "index": true,
          "default": "",
          "fake":[
              {"command": "fake.email()", "percent": 0.5},
              {"command": "fake.name()", "percent": 0.4},
              {"command": "fake.first_name()", "percent": 0.1}
            ]
        },
        {
          "name": "username",
          "type": "varchar",
          "size": 100,
          "ai": false,
          "null": false,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "fake.name()", "percent": 1}
          ]
        },
        {
          "name": "password",
          "type": "varchar",
          "size": 60,
          "ai": false,
          "null": false,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "fake.password()", "percent": 1}
          ]
        },
        {
          "name": "first_name",
          "type": "varchar",
          "size": 50,
          "ai": false,
          "null": true,
          "pk": false,
          "index": false,
          "default": "Simon",
          "fake": [
            {"command": "fake.first_name()", "percent": 1}
          ]
        },
        {
          "name": "last_name",
          "type": "varchar",
          "size": 50,
          "ai": false,
          "null": true,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "fake.last_name()", "percent": 1}
          ]
        }
      ]
    }
  ]
}
```

Details of each section of the JSON

1. A database called ```web_site``` (database_name) that will be dropped (drop) if it already exists.
2. An array of tables is defined. In this example a single table called ```users``` (name) will be generated.
3. 300 records will be generated using fake data (fake_qty)
4. An array of objects representing fields is provided. 
   - **name**: Name of the field. `String`
   - **type**: Uses mysql names i.e. INT, VARCHAR, DATE etc. `String`
   - **size**: This can be entered as a Integer i.e. `100` or as a string i.e. `"(6,2)"` for float's `String` or `Integer`
   - **ai**: (Auto Increment) is a boolean field `Boolean`
   - **null**: Can this field be nullable. `Boolean` 
   - **pk**: Is this a Primary Key field field. `Boolean`
   - **index**: Should this field be index.`Boolean`
   - **default**: What should the default value of this field be. `String` value
   - **fake**: Takes an array of commands. Each command is a JSON object, containing
      - **command**: The command to be run. `String`
      - **percent**: Weighting of this command. `1` is 100% `0.5` is 50%. This allows you vary the data that is generated in each field.

# Fake commands
Relational Faker uses a combination of the `Python Faker` library as well as custom functions. It is these custom functions that allow both relational tables to created but also extends the capabilities of the Faker library.

nb. All Python Faker commands start with `fake`. i.e. `fake.name()`

For more information on the commands available in the Faker library please visit

https://faker.readthedocs.io/en/master/

This tutorial will not cover the details of the specific commands available from the faker library, but the link above and some of the examples below will demonstrate it nicely.

The fake commands used both from the Faker library and the custom Relational Faker commands are entered as an array. In a lot of cases, you may only have one command, but this freedom to add multiple commands, get us closer to how data in the real world looks. Some data is correct, but a portion is wrong, perhaps in multiple different ways. i.e. Null value provided instead of a string or a missing relationship etc

The structure of the fake commands looks like this

```
"fake":[
          {"command": "fake.email()", "percent": 0.5},
          {"command": "fake.name()", "percent": 0.4},
          {"command": "fake.first_name()", "percent": 0.1}
        ]
```
in this example. 3 commands will be chosen randomly based on the weighting provided in the `percent` field. 
- 50% email (sarah_ellis@xyz_industry.com)
- 40% name (John Smith)
- 10% first_name (Lisa)

## Faker vs Custom commands
Some fake commands are evaluated directly

`fake.first_name()` or `random_number(1,100,0)`

While others are used as control commands to get random data or create relationships.

`table|vendors|random|id`

# List of custom commands

### `random_number(start_date, end_date, prec=0)`
Produces a random number between two numbers and to a certain decimal place.
- random_number(start, end, prec=0)
   - [start] The minimum value i.e. 10
   - [end] The maximum value i.e. 100
   - [prec] (Precision) (Default: 0) the number of decimal places. i.e. `2` =>  `67.34`, `3` => `67.342`, `0` => `67`

Returns: `Int` or `Float`

### `engineering_words(numWords=3)`
Produces random engineering words.
- engineering_words(numWords=3)
   - [numWords] (Default: 3) The number of words to return

Returns: `String`

### `date_greater_than_field(field_name, max_date="today")`
Produces a date greater than that contained in another field, in the same record. This command requires that the other field has already been defined before the field that contains this command.
- date_greater_than_field(field_name, max_date)
   - [field_name] The other field, that this date should be greater than
   - [max_date] (Default: 'today'). The date generated will be less than or equal to this date. 
   
   The value of `max_date` should either be parsable by strtotime i.e. "-1y" for minus 1 year, or an absolute date can be given, in which case it should be prepended with `date:` i.e. `date:2020-12-22` and the date format should be in ISO 8601 format (%Y-%m-%d)
   
   If `max_date` is less than the date held in `field_name`, the value of `max_date` will be returned. 

### `date_less_than_field(field_name, min_date="-1y")`
Produces a date less than that contained in another field, in the same record. This command requires that the other field has already been defined before the field that contains this command.
- date_less_than_field(field_name, min_date)
   - [field_name] The other field, that this date should be less than
   - [min_date] (Default: '-1y'). The date generated will be greater than or equal to the value of `field_name` minus this date. The value of `min_date` should be parsable by strtotime i.e. ('today', '+1y', '-2m' etc)

### `date_between(start_date, end_date)`
Produces a date between `start_date` and `end_date`
- [start_date]

### `number_greater_than_field(field_name, max=100)`
Produces a number that is greater than the value of the number held in `field_name` and less than the value of `field_name` plus `max`
- number_greater_than_field(field_name, max)
   - [field_name] The other field, that this number should be greater than
   - [max] (Default: 100) The number generated will be less than or equal to the value of `field_name` plus the value of `max`

### `number_less_than_field(field_name, min=100, allow_negative=False)`
Produces a number that is greater than the value of the number held in `field_name` and less than the value of `field_name` plus `max`
- number_greater_than_field(field_name, max)
   - [field_name] The other field, that this number should be greater than
   - [min] (Default: 100) The number generated will be less than or equal to the value of `field_name` minus the value of `min`
   - [allow_negative] (Default: False) If True negative values will be allowed. If False (Default) the minimum value returned will be 0

# List of control commands

Control commands, allow data to be fetched from any other table (see note i. below) or to be used in conjunction with the relational commands provided in the `fake_qty` definition of the table.

>i. _When using a control command to pull data from another table, the other table must have already been created, so it's important to think about how you design your data definition. I'm looking to remove this restriction at a later date._

## Example
It is much easier to explain the use of control commands through an example.

Lets assume we already have a `purchase_orders` table and we want to create a `purchase_order_lines` table. Each purchase order could have multiple purchase order lines. 

In this scenario, we want to create a random number of purchase order lines (say between 1 and 20). Each purchase order line should have a reference to the `purchase_order` number of it's parent related record. Each line should also have a reference to a random part number from an `items` table.

Here is the JSON for the `purchase_order_lines` table

```
{
      "name": "purchase_order_lines",
      "fake_qty": "table|each|purchase_orders|1|20",
      "fields": [
        {
          "name": "id",
          "type": "int",
          "size": 11,
          "ai": true,
          "null": false,
          "pk": true,
          "index": false,
          "default": "",
          "fake": null
        },
        {
          "name": "purchase_order",
          "type": "varchar",
          "size": 11,
          "ai": false,
          "null": false,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "each|purchase_order", "percent": 1}
          ]
        },
        {
          "name": "item",
          "type": "varchar",
          "size": 200,
          "ai": false,
          "null": false,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "table|items|random|part_number", "percent": 1}
          ]
        },
        {
          "name": "qty",
          "type": "int",
          "size": 6,
          "ai": false,
          "null": false,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "random_number(1,200,0)", "percent": 1}
          ]
        }
```


### fake_qty
#### table|each|purchase_orders|1|20

`"fake_qty": "table|each|purchase_orders|1|20"`
Rather than specifying a specific number of records, we want to take each record from the `purchase_orders` table and generate a random qty of records (between `1` and `20` in this case) in the `purchase_order_lines` table. This gives us a one to many relationship

If we only wanted to generate a single row for each row in `purchase_orders` we just remove the min and max records like this `table|each|purchase_orders`. This would give us a one to one relationship.

### command

#### each|purchase_order
```
{
          "name": "purchase_order",
          "type": "varchar",
          "size": 11,
          "ai": false,
          "null": false,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "each|purchase_order", "percent": 1}
          ]
        }
```
In the `purchase_order` field definition we use the `each` control command. This will take the value of field provided after the `|` from the table that we are looping over. In this case the `purchase_order` field in the `purchase_order` table, and will use that as the value for the `purchase_order` field in the table we are generating (`purchase_order_lines`). This will give us a relationship between the data in the two tables.

#### table|items|random|part_number

```
{
          "name": "item",
          "type": "varchar",
          "size": 200,
          "ai": false,
          "null": false,
          "pk": false,
          "index": false,
          "default": "",
          "fake": [
            {"command": "table|items|random|part_number", "percent": 1}
          ]
        }
```
In the `item` table we get a random `part_number` from the `items` table. This is a new random `part_number` for each row in `purchase_order_lines`