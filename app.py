import streamlit as st
import json
import os
import requests
import re
import psycopg2
import configparser
import pandas as pd

# Main title
st.title("Data Source Query")

config = configparser.ConfigParser()
config.read('config.ini')

if "input_text" not in st.session_state:
    st.session_state.input_text = 1

# if "Sql_query" not in st.session_state:
#     st.session_state.Sql_query = ""

# if "button_pressed" not in st.session_state:
#     st.session_state["button_pressed"] = False

if "response" not in st.session_state:
    st.session_state.response = ""

if "valid_response" not in st.session_state:
    st.session_state.valid_response = False


endpoint = "http://172.162.12.15:8501/data_source_query"
# endpoint = "http://172.162.13.82:8505/data_source_query"

# Select option ("with_metadata" or "without_metadata")
# selected_model = st.selectbox("Select Option", ["OPENAI", "Llama3"])

# Get path to the folder based on the selected option
folder_path = "Data_source"

download_file = os.path.join(folder_path, "schema.txt")
if os.path.exists(download_file):
    
    with open(os.path.join(folder_path, "schema.txt")) as f:


        btn = st.download_button(
            label="Download Schema",
            data = f,
            file_name = download_file,
            mime="text",
        )

else:
    st.write("File doesn't exsist")

selected_option = st.selectbox("Select Option", ["with_metadata", "without_metadata"])
user_question = st.text_input("Enter the query", key=st.session_state.input_text,value="")

selected_file = os.path.join(folder_path, f"{selected_option}.json")

# Check if there are exactly two JSON files in the folder
if os.path.exists(selected_file):
    # Read JSON content from the selected file
    with open(selected_file) as f:
        payload = json.load(f)

        # payload_download = json.dumps(payload)
    
    
    payload["json_data"]["text"] = user_question   

    # print(payload)    

else:
    st.error("There should be exactly two JSON files in the selected folder.")


def execute_query(query):
    section = "PostgresDB_DEV"
    conn = psycopg2.connect(
        dbname=str(config.get(section,'database')),
        user=str(config.get(section,'user')),
        password=str(config.get(section,'password')),
        host=str(config.get(section,'host')),
        port=str(config.get(section,'port'))
    )
    cur = conn.cursor()
    cur.execute(query)
    column_names = [description[0] for description in cur.description]
    result = cur.fetchall()
    conn.close()
    
    return result,column_names


# Button to trigger the request
# st.session_state["button_pressed"] = st.button("Send Request")

if user_question != "":
        # Sending request
    if not st.session_state.valid_response:
        # if selected_model == 'OPENAI':
            response = None
            response = requests.post(endpoint,json=payload)
            # Handle other request methods similarly

            # print(type(response))
            # Display response
            if response:
                
                pattern = r"\{\{.*?\.(\w+(?:\s+\w+)*).*?\}\}"

                if response.text == "":
                    st.text("enter valid prompt")
                # Extract the desired part using regex and replace it in the string
                
                else:
                    st.subheader("SQL Query")
                    sql = re.sub(pattern, r"\1", response.text)

                    if not sql.endswith(';'):
                        sql += ';'
                    
                    st.session_state.valid_response = True
                    st.session_state.response = sql
            
            else:
                st.error("Failed to get response")
                
    modified_sql = st.text_area("SQL Code", st.session_state.response, key="query")
        
        
    if st.button("Get Results"):
        results, column_names = execute_query(modified_sql)
        df = pd.DataFrame(results, columns=column_names)
        st.subheader("Results")
        st.dataframe(df)

st.write("")
st.write("")
if st.button('Test New Query'):
    st.session_state.input_text+=1
    # st.session_state["button_pressed"] = False
    st.session_state.valid_response = False
    st.session_state.response = ""

    st.rerun()

