# Script to read an Excel template (refer to sample-data/edit-app-from-excel-template.csv) and create fields in a Clappia app using the Clappia API

# pip install -r requirements.txt
# python src/edit-app-from-excel-template.py --workplace_id DE04924 --api_key de<REDACTED>  --app_id UNT439473 --file_path sample-data/edit-app-from-excel-template.csv --requesting_user_email_address s@clappia.com
import pandas as pd
import networkx as nx
import re
import requests
import argparse
import time
import traceback

# Function to parse formula and extract labels
def extract_labels(formula):
    # print (formula)
    # handle valid strings only, if input is empty/null/etc, don't run findall
    if formula is None:
        return []
    # Find patterns like {1}, {2}, etc. in the formula and add them as dependencies
    dependencies = re.findall(r'\{(\d+)\}', formula)
    # print('here', formula, dependencies)
    # return dependencies
    # convert dependencies to integers and subtract 1
    dependencies = [int(dep) - 2 for dep in dependencies]
    return dependencies

# Function to create fields using API
# TODO: Reduce number of args by accepting a field details dictionary
def create_field(section_index, field_index, label, field_type, options, formula, required='', display_condition='', allowed_file_types=''):
    print('Creating field:', label, field_type)
    api_endpoint = "https://api-public-v3.clappia.com/appdefinitionv2/addField"
    payload = {
        "appId": app_id,
        "workplaceId": workplace_id,
        "requestingUserEmailAddress": requesting_user_email_address,
        "sectionIndex": int(section_index),
        "fieldIndex": int(field_index),
        "fieldType": field_type,
        "label": label,
    }
    if formula:
        payload["formula"] = formula
    if options:
        options = options.split(',')
        options = [option.strip() for option in options]
        payload["options"] = options
    if display_condition:
        payload["displayCondition"] = display_condition
    if allowed_file_types:
        payload["allowedFileTypes"] = allowed_file_types.split(',')
    if required:
        payload["required"] = True

    # print(payload)
    headers = {'Content-Type': 'application/json', 'x-api-key': api_key}
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers)
    except:
        print(traceback.format_exc())
        print('Timeout occurred, retrying after 10 seconds...', )
        time.sleep(10)
        response = requests.post(api_endpoint, json=payload, headers=headers)
    # print(response)
    if response.status_code == 200:
        field_name = response.json()['fieldName']
        print('Field created:', field_name)
        return field_name
    else:
        print (response)
        return None
    
def update_field(field_name, label, options, formula, required='', display_condition='', allowed_file_types=''):
    print('Updating field:', label)
    api_endpoint = "https://api-public-v3.clappia.com/appdefinitionv2/updateField"
    payload = {
        "appId": app_id,
        "workplaceId": workplace_id,
        "requestingUserEmailAddress": requesting_user_email_address,
        "fieldName": field_name,
        "label": label,
    }
    if formula:
        payload["formula"] = formula
    if options:
        options = options.split(',')
        options = [option.strip() for option in options]
        payload["options"] = options
    if display_condition:
        payload["displayCondition"] = display_condition
    if allowed_file_types:
        payload["allowedFileTypes"] = allowed_file_types.split(',')
    if required:
        payload["required"] = True

    # print(payload)
    headers = {'Content-Type': 'application/json', 'x-api-key': api_key}
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers)
    except:
        print(traceback.format_exc())
        print('Timeout occurred, retrying after 10 seconds...', )
        time.sleep(10)
        response = requests.post(api_endpoint, json=payload, headers=headers)
    if response.status_code == 200:
        print('Field updated')   
    else:
        print (response)
        return None
def main():
    # Read CSV file
    df = pd.read_csv(file_path, na_filter=False)
    for index, row in df.iterrows():
        section_index = row['sectionIndex']
        field_index = row['fieldIndex']
        field_type = row['fieldType']
        options = row['options']
        formula = row['formula']
        label = row['label']
        required = row['required']
        display_condition = row['display_condition']
        allowed_file_types = row['allowed_file_types']
        field_name = create_field(section_index-1, field_index-1, label, field_type, options, formula, required, display_condition, allowed_file_types)
    
        df.at[index, 'field_name'] = field_name
        if field_name:
            # Replace references to fields in formulas
            df['formula'] = df['formula'].apply(lambda x: str(x).replace('{' + str(index+2) + '}', '{' + field_name + '}'))
            df['display_condition'] = df['display_condition'].apply(lambda x: str(x).replace('{' + str(index+2) + '}', '{' + field_name + '}') if x and type(x) == str else '')
    
    # iterate through the df and call updateField API for all
    for index, row in df.iterrows():
        field_name = row['field_name']
        field_type = row['fieldType']
        options = row['options']
        formula = row['formula']
        label = row['label']
        required = row['required']
        display_condition = row['display_condition']
        allowed_file_types = row['allowed_file_types']
        update_field(field_name, label, options, formula, required, display_condition, allowed_file_types)
    

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workplace_id', help='Clappia Workplace ID')
    parser.add_argument('--api_key', help='Clappia API Key')
    parser.add_argument('--app_id', help='App ID')
    parser.add_argument('--file_path', help='file path on the local system')
    parser.add_argument('--requesting_user_email_address', help='Requesting User Email Address')

    args = parser.parse_args()
    return args.workplace_id, args.api_key, args.app_id, args.file_path, args.requesting_user_email_address

# Global variables
workplace_id = None
api_key = None
app_id = None
file_path = None
requesting_user_email_address = None

if __name__ == "__main__":
    workplace_id, api_key, app_id, file_path, requesting_user_email_address = parse_arguments()
    main()
