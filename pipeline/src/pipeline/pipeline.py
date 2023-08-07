# -*- coding: utf-8 -*-
"""
Get a submission with a specific ID from kobo and upload it to espocrm via the API
The script takes the KoBo ID of the submission as input argument
"""

import requests
import pandas as pd
from pipeline.espo_api_client import EspoAPI
import os
import base64
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


def get_kobo_attachment(URL):
    # Get attachment from kobo
    headers = {'Authorization': f'Token {os.getenv("TOKEN")}'}
    data_request = requests.get(URL, headers=headers)
    data = data_request.content
    return data


@click.command()
@click.option('--koboid', default="", help='ID of the KoBo submission')
@click.option('--verbose', '-v', is_flag=True, default=False, help="Print more output.")
def main(koboid, verbose):
    # Setup EspoAPI
    client = EspoAPI(os.getenv("ESPOURL"), os.getenv("ESPOAPIKEY"))
    
    # Get latest KoBo Submission
    df = get_kobo_data_id(koboid)
    # remove group names
    for key in list(df.keys()):
        new_key = key.split('/')[-1]
        df[new_key] = df.pop(key)
    if verbose:
        print('KoBo data:')
        print(df)

    # Create a dataframe to map the Kobo question names to the Espo Fieldnames
    mapping = pd.read_csv('../data/koboespomapping.csv', header=0, index_col=0, squeeze=True)
    
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
        field = row['esponame']  # field in espo
        question = row['koboname']  # question in kobo
        question_type = row['type']  # question type in kobo
        try:
            # If select_multiple questions, split up string, turn into list (array in json)
            if question_type == 'select_multiple':
                payload_value = df[question].split()
            # If attachment question, upload attachment to espo
            elif question_type == 'attachment':
                filename = df[question]
                filename = filename.replace(" ", "_")  # kobo saves attachments by replacing spaces with _
                file_url = attachments[filename]['url']
                # encode image in base64
                file = get_kobo_attachment(file_url)
                file_b64 = base64.b64encode(file).decode("utf8")
                # upload attachment to espo
                attachment_payload = {
                    "name": filename,
                    "type": attachments[filename]['mimetype'],
                    "role": "Attachment",
                    "relatedType": os.getenv("ESPOENTITY"),
                    "field": field,
                    "file": f"data:{attachments[filename]['mimetype']};base64,{file_b64}"
                }
                if verbose:
                    print('Espo attachment payload (excluding file):')
                    for key in attachment_payload.keys():
                        if key != "file":
                            print(key, ':', attachment_payload[key])
                attachment_record = client.request('POST', 'Attachment', attachment_payload)
                # link field to attachment
                field = f"{field}Id"
                payload_value = attachment_record['id']
            # If no conditions apply, map right value
            else:
                payload_value = df[question]
        # If field is not filled in KoBo survey, pass empty string
        except KeyError:
            payload_value = ''
        payload[field] = payload_value
    if verbose:
        print('Espo entity payload:')
        print(payload)
    # Create the registration by sending the request to Espo
    espo_response = client.request('POST', os.getenv("ESPOENTITY"), payload)
    return espo_response


if __name__ == "__main__":
    main()