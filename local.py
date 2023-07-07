#ToDo
#Map enum options as well?
#Change programID from env variable to function input

import requests
import pandas as pd
import os
from dotenv import load_dotenv
import json
from datetime import datetime, date
load_dotenv(dotenv_path="./credentials/.env")

def get_kobo_data_id(ID):
    # Get data from kobo
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    data_request = requests.get(
        f'https://kobonew.ifrc.org/api/v2/assets/{os.getenv("ASSET")}/data.json/?query={{"_id":{ID}}}',
        headers=headers)
    data = data_request.json()['results'][0]
    return data

def mock_get_kobo_data_id(ID):
    # Get data from kobo
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    data_request = requests.get("http://127.0.0.1:8000/kobomock/kenyaReg",
        headers=headers)
    data = data_request.json()['results'][0]
    return data

def get_121_cookie():
    # Retrieve the values
    with open("cookie.json", "r") as file:
        data = json.load(file)
    timeNow = datetime.utcnow()
    lastUpdated = datetime.strptime(data["date"], "%Y-%m-%d")
    delta = timeNow - lastUpdated
    
    if delta.days > 10:
        body = {'username': f'{os.getenv("121USER")}','password': f'{os.getenv("121PASS")}'}
        url = f'{os.getenv("121URL")}/api/user/login'
        data_request = requests.post(url,data=body)
        value = data_request.json()['acces_token_general']
        with open("cookie.json", "w") as file:
            json.dump({"date": datetime.utcnow().strftime('%Y-%m-%d'), "token": value}, file)

    with open("cookie.json", "r") as file:
        data = json.load(file)
    cookie = data["token"]

    return cookie

def upload_registration_121(data):
    cookie = get_121_cookie()
    url = f'{os.getenv("121URL")}/api/programs/{os.getenv("121PROGRAMID")}/registrations/import'
    header = {'Cookie': f'access_token_general={cookie}'}
    data_request = requests.post(url,json=data,headers=header)
    return data_request

# Get latest KoBo Submission
df = get_kobo_data_id(1321669)

# remove group names
for key in list(df.keys()):
    new_key = key.split('/')[-1]
    df[new_key] = df.pop(key)

if 1 == 0:
    print('KoBo data:')
    print(df)


# Create a dataframe to map the Kobo question names to the 121 Fieldnames
mapping = pd.read_csv('./data/kobo121mapping.csv', header=0, index_col=0)

if 1 == 0:
    print(mapping)

# Create a dictionary to map the attachment filenames to their URL
attachments = {}
x = 0
while x < len(df['_attachments']):
    filename = df['_attachments'][x]['filename'].split('/')[-1]
    downloadurl = df['_attachments'][x]['download_url']
    mimetype = df['_attachments'][x]['mimetype']
    attachments[filename] = {'url': downloadurl, 'mimetype': mimetype}
    x += 1

# Create API payload body
payload = {}

for ix, row in mapping.iterrows():
    field = row['121name']  # field in 121
    question = row['koboname']  # question in kobo
    question_type = row['type']  # question type in kobo
    try:
        # If select_multiple questions, replace " " by " | "
        if question_type == 'select_multiple':
            payload_value = df[question].replace(" ", " | ")
        # If attachment question, create link to attachment
        elif question_type == 'attachment':
            filename = df[question]
            filename = filename.replace(" ", "_")  # kobo saves attachments by replacing spaces with _
            file_url = attachments[filename]['url']
            payload_value = file_url
        # If no conditions apply, map right value
        else:
            payload_value = df[question]
    # If field is not filled in KoBo survey, pass empty string
    except KeyError:
        payload_value = ''
    payload[field] = payload_value

payload['fspName'] = 'BelCash'
payload['phoneNumber'] = '+31631552867'
payload['MpesaNumberRegistered'] = '+31631552867'

#create list
data = []
data.append(payload)

if 1 == 1:
    print('121 payload:')
    print(data)

#post to 121
if 1 == 1:
    response = upload_registration_121(data)
    print(response)
    print(response.content)