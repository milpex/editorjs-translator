# %% [markdown]
# # EditorJS translation tool
# purpose of this script is to translate the EditorJS JSON text fields to the desired language
# we will grab the JSON from the database (with joined base table and translations table) and then translate the text field from
# input language to the desired language

"""
RUN SQL QUERIES ON THE DATABSES TO GET THE DATA NEEDED
"""

# connect to the PostgreSQL database
import json
import argparse
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from googletranslate import translate
import time
load_dotenv()


"""EDITORJS DEFINITION"""
# define the forbidden blocks that should not be translated
EDITORJS_FORBIDDEN_BLOCKS = ["toc"]
# define the mapping for blocks that have specific data fields that should be translated, else look for `text` field
EDITORJS_SPECIFIC_BLOCK_OF_DATA = {
    "warning": ["title", "message"],
}
EDITORJS_DEFAULT_BLOCK_OF_DATA = "text"


def translate_text(text, input_language, desired_language):
  print(f"Translating text: {text}")
  # sleep for 0,5 seconds to avoid the googletrans.exceptions.TranslatorError: Failed to connect. Probable cause: timeout
  time.sleep(0.5)
  return translate(dest=desired_language, src=input_language, text=text)


def editorjs_translation(input_editorjs, input_language, desired_language):

  # deep copy the input_editorjs
  output_editorjs = input_editorjs.copy()
  # iterate over the blocks
  for block in output_editorjs['blocks']:
    if 'data' not in block:
      print("Block does not have data")
      continue
    # check if the block has text
    if block['type'] in EDITORJS_FORBIDDEN_BLOCKS:
      print(f"Block {block['type']} is forbidden")
      continue
    # check if the block has specific data fields
    if block['type'] in EDITORJS_SPECIFIC_BLOCK_OF_DATA:
      print(f"Block {block['type']} has specific data fields")
      fields = EDITORJS_SPECIFIC_BLOCK_OF_DATA[block['type']]
      for field in fields:
        if field in block["data"]:
          block["data"][field] = translate_text(block["data"][field], input_language, desired_language)
    else:
      print(f"Block {block['type']} has default data field")
      # check if the block has a EDITORJS_DEFAULT_BLOCK_OF_DATA
      if EDITORJS_DEFAULT_BLOCK_OF_DATA in block["data"]:
        block["data"][EDITORJS_DEFAULT_BLOCK_OF_DATA] = translate_text(
          block["data"][EDITORJS_DEFAULT_BLOCK_OF_DATA], input_language, desired_language)

  return output_editorjs


""""SCRIPT STARTS HERE"""

parser = argparse.ArgumentParser()
parser.add_argument("--input_language", help="input language")
parser.add_argument("--desired_language", help="desired language")
parser.add_argument("--sql_query_path", help="path to the SQL query")
parser.add_argument("--column_name", help="column name to translate")
parser.add_argument("--language_column_name", help="column name with the language")

args = parser.parse_args()

if args.input_language:
  input_language = args.input_language
else:
  print("Please provide the input language")
  exit()
if args.desired_language:
  desired_language = args.desired_language
else:
  print("Please provide the desired language")
  exit()

if args.sql_query_path:
  sql_query_path = args.sql_query_path
else:
  print("Please provide the path to the SQL query")
  exit()

if args.column_name:
  column_name = args.column_name
else:
  print("Please provide the column name to translate")
  exit()

if args.language_column_name:
  language_column_name = args.language_column_name
else:
  print("Please provide the column name with the language")
  exit()


# Database connection parameters
host = os.getenv("PGHOST")
port = os.getenv("PGPORT")
database = os.getenv("PGDB")
user = os.getenv("PGUSER")
password = os.getenv("PGPASSWORD")

# Connection string
connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_string)


# get the input language and the desired language from the command line with path to the SQL query


with open(sql_query_path, 'r') as file:
  data_query = file.read()

# execute the query
data = pd.read_sql(data_query, engine)

# in the data, try to find the input language row and the desired language row
input_language_row = data[data[language_column_name] == input_language]
desired_language_row = data[data[language_column_name] == desired_language]

# find the column with the text to translate
input_editorjs = input_language_row[column_name].values[0]
desired_editorjs = desired_language_row[column_name].values[0]

# translate the text
print("Translating the text")
output_editorjs = editorjs_translation(input_editorjs, input_language, desired_language)

# save the output_editorjs to the json file
with open("output_editorjs.json", "w") as f:
  json.dump(output_editorjs, f)


# TODO: do the database save...
