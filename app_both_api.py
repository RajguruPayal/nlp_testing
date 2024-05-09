import streamlit as st
import json
import os
import requests
import re
import psycopg2
import configparser
import pandas as pd

# Main title
st.title("Welcome to the NLP Testing App 🚀")

config = configparser.ConfigParser()
config.read('config.ini')


if "input_text" not in st.session_state:
    st.session_state.input_text = ""


section = 'endpoint'
# Input fields for user input


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







def load_json(folder_path, selected_option, user_question):
    
    selected_file = os.path.join(folder_path, f"{selected_option}.json")
    
    if os.path.exists(selected_file):
        # Read JSON content from the selected file
        with open(selected_file) as f:
            payload = json.load(f)

        # Update the JSON payload with user question
        payload["json_data"]["text"] = user_question   

        return payload
    else:
        st.error("There should be exactly two JSON files in the selected folder.")
        return None


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







# endpoint = str(config.get(section,'endpoint'))
radio_option = st.selectbox("Select Option", ["Data Source Query", "Ad-Hoc"])
# Select option ("with_metadata" or "without_metadata")
selected_option = st.selectbox("Select Option", ["with_metadata", "without_metadata"])
user_question = st.text_input("Enter the query", key=st.session_state.input_text,value="")

if user_question != "":

    if radio_option == "Data Source Query":
        endpoint = "http://172.162.12.15:8501/data_source_query"
        folder_path = "Data_source"
        payload = load_json(folder_path, selected_option, user_question)
        # if os.path.exists(folder_path):
        #     with open(os.path.join(folder_path, "with_metadata.json")) as f:
        #         payload_download = json.load(f)
        #         metadata_download = json.dumps(payload_download)

        #     st.download_button(
        #         label="Download metadata",
        #         data = metadata_download,
        #         file_name = "Data_source\\with_metadata.json" ,
        #         mime="application/json",
        #     )
        # else:
        #     st.write("File doesn't exsist")
        
    
        headers = {'Content-Type': 'application/json'}
        response = requests.post(endpoint,json=payload,headers=headers)
        
        if response:        
            
            pattern = r"\{\{.*?\.(\w+(?:\s+\w+)*).*?\}\}"
            # print("response.text-------------------",response.text) 
            if response.text == "":
                print("enter valid prompt")
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

        if "response" not in st.session_state:
            st.session_state.response = ""  

        modified_sql = st.text_area("SQL Code", st.session_state.response, key="query")
        print("modified_sql--------",st.session_state.response)

        if st.button("Get Results"):
            results, column_names = execute_query(st.session_state.response)
            df = pd.DataFrame(results, columns=column_names)
            st.subheader("Results")
            st.dataframe(df)






    elif radio_option == "Ad-Hoc":
        endpoint = "http://172.162.12.15:9385/text_to_sql"
        folder_path = "Ad-Hoc" 
        payload = load_json(folder_path, selected_option, user_question)
        # if os.path.exists(folder_path):
        #     with open(os.path.join(folder_path, "with_metadata.json")) as f:
        #         payload_download = json.load(f)
        #         metadata_download = json.dumps(payload_download)

            
        #     st.download_button(
        #         label="Download metadata",
        #         data = metadata_download,
        #         file_name = "Data_source\\with_metadata.json" ,
        #         mime="application/json",
        #     )
        # else:
        #     st.write("File doesn't exsist")
        
        

        if payload["json_data"]["TableMetadata"]:
        
            tableid_tablename_dict = {}
            for table_json in payload["json_data"]["TableMetadata"]:
                DataTableName = table_json['DataTableName']
                DataTableId = table_json["DataTableId"]
                tableid_tablename_dict[str(DataTableId).lower()] = str(DataTableName).lower()
            
            current_dir = os.getcwd()
            # Construct folder path
            full_folder_path = os.path.join(current_dir,folder_path)
            
            # Create folder structure
            os.makedirs(full_folder_path, exist_ok=True)

            # Construct JSON file path
            json_file = os.path.join(full_folder_path, "tableid_tablename_dict.json")

            # Write JSON data to file
            try:
                with open(json_file, "w") as outfile: 
                    json.dump(tableid_tablename_dict, outfile)
                print("tableid_tablenamedict file saved")
            except Exception as e:
                print(f"Error occurred while saving file: {e}")

        current_dir = os.getcwd()
        # Construct folder path
        full_folder_path = os.path.join(current_dir,folder_path)
        
        # Create folder structure
        os.makedirs(full_folder_path, exist_ok=True)

        # Construct JSON file path
        json_file = os.path.join(full_folder_path, "tableid_tablename_dict.json") 


        try:
            with open(json_file) as infile:
                tableid_tablename_dict = json.load(infile)
            print("tableid_tablenamedict file loaded successfully")
        
        except Exception as e:
            print(f"Error occurred while loading file: {e}")

        response = None
        headers = {'Content-Type': 'application/json'}
        response = requests.post(endpoint,json=payload,headers=headers) 
        if response:
            st.subheader("SQL Query")
            if response.text == "":
                print("enter valid prompt")
            else:
                # st.write(response.json())
                response_json = response.json()        
                modified_sql = st.text_area("SQL Code",response_json["Sql_Query"])
                chart_obj = st.text_area("ChartObj",response_json["ChartObj"])                
                ids = re.findall(r'"([^"]*-\w*_[^"]*)"', modified_sql)
        
                for id in ids:
                    if id in tableid_tablename_dict:
                        sql_query = modified_sql.replace(id, tableid_tablename_dict[id])

                if st.button("Get Results"):
                    results, column_names = execute_query(sql_query)
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

