# -*- coding: utf-8 -*-
"""
Get a submission with a specific ID from kobo and upload it to espocrm via the API

The script takes exactly 1 argument, which is the kObO ID of the submission
"""

import requests
import pandas as pd
from pipeline.espo_api_client import EspoAPI
import os
from dotenv import load_dotenv
import click
load_dotenv(dotenv_path="../credentials/.env")

def get_kobo_data_id(ID):
    # Get data from kobo
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    data_request = requests.get(
        f'https://kobonew.ifrc.org/api/v2/assets/{os.getenv("ASSET")}/data.json/?query={{"_id":{ID}}}',
        headers=headers)
    data = data_request.json()['results'][0]
    return data

@click.command()
@click.option('--koboid', default="", help='import the submission with the specified ID')

def main(koboid):
    # Setup EspoAPI
    client = EspoAPI(os.getenv("ESPOURL"), os.getenv("ESPOAPIKEY"))
    
    # Get latest KoBo Submission
    ID = koboid
    df = get_kobo_data_id(ID)
    
    # Create a dataframe to map the Kobo question names to the Espo Fieldnames
    mapping = pd.read_csv('../data/koboespomapping.csv', header=0, index_col=0, squeeze=True)
    
    # Create a dictionary to map the attachment filenames to their URL
    attachments = {}
    x = 0
    while x < len(df['_attachments']):
        filename = df['_attachments'][x]['filename'].split('/')[-1]
        downloadurl = df['_attachments'][x]['download_url']
        attachments[filename]=downloadurl
        x += 1
    
    
    # Create API payload body
    payload = {}
    
    x = 0
    while x < len(mapping):
        field = mapping.iat[x,0]
        try:
            # If select_multiple questions, split up string, turn into list (array in json)
            if mapping.iat[x,2] == 'select_multiple':
                PLvalue = df[mapping.iat[x,1]].split()
            # If attachment question (file, image, video), get url to attachment
            elif mapping.iat[x,2] == 'attachment':
                filename = df[mapping.iat[x,1]]
                filename = filename.replace(" ", "_") #kobo saves attachments by replacing spaces with _
                PLvalue = attachments[filename]
            # If no conditions apply, map right value
            else:
                PLvalue = df[mapping.iat[x,1]]
        # If field is not filled in in KoBo survey, pass empty string
        except KeyError:
            PLvalue = ''
        payload[field]=PLvalue
        x += 1
    
    # Create the registration by sending the request to Espo
    if 1 == 1:  # For testing purposes, set to 1 == 1 if you want to send the request
        EspoResponse = client.request('POST', 'Lead', payload)

    return payload

if __name__ == "__main__":
    main()