
# %%
import argparse
import os
argparser = argparse.ArgumentParser()
argparser.add_argument('-i','--input', type=str, help='input manifest file')
argparser.add_argument('-o','--output', type=str, help='output directory folder')
argparser.add_argument('-v','--verbose', action='store_false', help='verbose')
args = argparser.parse_args()
inputdirectory = args.input
outputdirectory = args.output
verb = args.verbose
import pandas as pd
manifest = pd.read_csv(inputdirectory, sep = '\t')
# %%
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from tqdm import tqdm
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
paginator = s3.get_paginator('list_objects_v2')
response_iterator = paginator.paginate(Bucket='human-microbiome-project')
KeyList = []
if verb:
    print('Getting FileList in S3 human-microbiome-project')
for response in tqdm(response_iterator, desc='Getting file List (page in s3)',unit='page'):
    for obj in response.get('Contents', []):
        KeyList.append(obj.get('Key'))
# %%
if verb:
    print('Matching Files in Manifest')
manifest['filename'] = manifest['urls'].apply(lambda x: os.path.basename(x))
fileList = [os.path.basename(x) for x in KeyList]
def searchfile(x):
    try:
        return KeyList[fileList.index(x)]
    except:
        return None
manifest['retrieveUrl'] = manifest['filename'].apply(searchfile)
failed_manifest = manifest[manifest['retrieveUrl'].isnull()]
failed_manifest.to_csv(os.path.join(outputdirectory,'failed_manifest.tsv'), sep = '\t', index = False)
if verb:
    print('Failed Manifests are saved in ',os.path.join(outputdirectory,'failed_manifest.tsv'))
successful_manifest = manifest[manifest['retrieveUrl'].notnull()]
successful_manifest.to_csv(os.path.join(outputdirectory,'successful_manifest.tsv'), sep = '\t', index = False)
if verb:
    print('Successful Manifests are saved in ',os.path.join(outputdirectory,'successful_manifest.tsv'))
# %%
if os.path.exists(outputdirectory) == False:
    if verb:
        print(f'Creating Output Directory {outputdirectory}')
    os.mkdir(outputdirectory)
if verb:
    print('Downloading Files')
for index, row in tqdm(manifest.iterrows()):
    if row['retrieveUrl'] is not None:
        s3.download_file('human-microbiome-project', row['retrieveUrl'], os.path.join(outputdirectory,row['filename']))
# %%
print('Download Complete')
exit(0)