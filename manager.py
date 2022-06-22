import os
import pandas as pd
import helpers as hl


COL_STANDARD = ['mallUrl', 'cats', 'catLink', 'productUrl', 'productLabel', 'productDesc',
            'productPrice', 'productSpec', 'productImages', 'productRating']


def combine_feather(local_path, big_feathername):
    BIG_FEATHER_NAME = big_feathername

    # Check if local_path ends with /
    if '/' not in local_path[-1]:
        local_path = local_path + '/'

    dfs = pd.concat([pd.read_feather(local_path+f)[COL_STANDARD] for f in os.listdir(local_path)])
    dfs.reset_index(drop=True).to_feather(BIG_FEATHER_NAME)
    return


def bucket_dld(local_path, bucketname, folder_key, feathername=None, client=None):

    # Check if we're provided with a client
    if client is None:
        client = hl.start_boto_session(service_name='s3')
    else:
        # Check if our client is S3
        if 's3' not in str(client._endpoint):
            print('Client is not an S3 service:')
            return

    # Check if folder_key ends with /
    if '/' not in folder_key[-1]:
        folder_key = folder_key + '/'

    # Check if local_path ends with /
    if '/' not in local_path[-1]:
        local_path = local_path + '/'

    # If feathername given, we download just one
    if feathername is not None:
        client.download_file(Bucket=bucketname, Key=folder_key+feathername, Filename=local_path+feathername)

    # If no feathername given, we download everything.
    if feathername is None:

        # Get list of all objects in bucket and folder_key
        for key in client.list_objects_v2(Bucket=bucketname, Prefix=folder_key)['Contents']:
            feathername = key['Key'].replace(folder_key, '')
            print('Getting file:', feathername)
            client.download_file(Bucket=bucketname, Key=folder_key + feathername, Filename=local_path + feathername)