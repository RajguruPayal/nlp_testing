import configparser
import psycopg2
import re

config = configparser.ConfigParser()
config.read('config.ini')

query = """SELECT "Text", "Number" FROM {{Sprint 57.Dt with all elements dt 1}}
"""

pattern = r"\{\{.*?\.(\w+(?:\s+\w+)*).*?\}\}"

# Extract the desired part using regex and replace it in the string
modified_sql = re.sub(pattern, r"\1", query)

if not modified_sql.endswith(';'):
    modified_sql += ';'

    

def execute_query(sql):
    section = "PostgresDB_DEV"
    conn = psycopg2.connect(
        dbname=str(config.get(section,'database')),
        user=str(config.get(section,'user')),
        password=str(config.get(section,'password')),
        host=str(config.get(section,'host')),
        port=str(config.get(section,'port'))
    )
    cur = conn.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    conn.close()
    
    return result

result = execute_query(modified_sql)

print(result)