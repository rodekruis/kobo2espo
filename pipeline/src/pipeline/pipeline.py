# -*- coding: utf-8 -*-
"""
Get a submission with a specific ID from kobo and upload it to 121 via the API
The script takes the KoBo ID of the submission as input argument
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv
import json
from datetime import datetime, date
import click
load_dotenv(dotenv_path="../credentials/.env")

def get_kobo_data_id(ID):
    # Get data from kobo
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    data_request = requests.get(
        f'{os.getenv("KOBOURL")}/api/v2/assets/{os.getenv("ASSET")}/data.json/?query={{"_id":{ID}}}',
        headers=headers)
    data = data_request.json()['results'][0]
    return data

def get_121_cookie():
    # Retrieve the values
    with open("../data/cookie.json", "r") as file:
        data = json.load(file)
    timeNow = datetime.utcnow()
    lastUpdated = datetime.strptime(data["date"], "%Y-%m-%d")
    delta = timeNow - lastUpdated
    
    if delta.days > 10:
        body = {'username': f'{os.getenv("121USER")}','password': f'{os.getenv("121PASS")}'}
        url = f'{os.getenv("121URL")}/api/user/login'
        data_request = requests.post(url,data=body)
        value = data_request.json()['access_token_general']
        with open("../data/cookie.json", "w") as file:
            json.dump({"date": datetime.utcnow().strftime('%Y-%m-%d'), "token": value}, file)

    with open("../data/cookie.json", "r") as file:
        data = json.load(file)
    cookie = data["token"]

    return cookie

def upload_registration_121(data,programid):
    cookie = get_121_cookie()
    url = f'{os.getenv("121URL")}/api/programs/{programid}/registrations/import'
    header = {'Cookie': f'access_token_general={cookie}'}
    data_request = requests.post(url,json=data,headers=header)
    return data_request


@click.command()
@click.option('--koboid', default="", help='ID of the KoBo submission')
@click.option('--verbose', '-v', is_flag=True, default=False, help="Print more output.")
def main(koboid, verbose): 
    # Get latest KoBo Submission
    df = get_kobo_data_id(koboid)
    if verbose:
        print('kobourl: ',f'{os.getenv("KOBOURL")}/api/v2/assets/{os.getenv("ASSET")}/data.json/?query={{"_id":{koboid}}}')
    # remove group names
    for key in list(df.keys()):
        new_key = key.split('/')[-1]
        df[new_key] = df.pop(key)
    if verbose:
        print('KoBo data:')
        print(df)

    # Create a dataframe to map the Kobo question names to the Espo Fieldnames
    mapping = pd.read_csv('../data/kobo121mapping.csv', header=0, index_col=0, squeeze=True)

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
            # If phone question, create link to attachment
            elif question_type == 'phone':
                payload_value = '+254' + df[question][1:]
            # If no conditions apply, map right value
            else:
                payload_value = df[question]
        # If field is not filled in KoBo survey, pass empty string
        except KeyError:
            payload_value = ''
        payload[field] = payload_value

    payload['fspName'] = 'Safaricom'

    if payload['county'] == 'Turkana':
        programid = 2
        payload['maxPayments'] = 6
    elif payload['county'] == 'Baringo':
        programid = 2
        payload['maxPayments'] = 6
    else:
        programid = 2
        payload['maxPayments'] = 3

    #create list
    data = []
    data.append(payload)

    if verbose:
        print('121 entity payload:')
        print(data)

    response = upload_registration_121(data,programid)
    if verbose:
        print(payload['county'],programid)
        print(response)
        print(response.content)

    if verbose:
        if (response.status_code == 200 or response.status_code == 201):
            print("The request was a success!")
        else:
            print("failed request")
    
    return(response)

if __name__ == "__main__":
    main()