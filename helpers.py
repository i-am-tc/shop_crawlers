import pandas as pd
import os
import boto3
import undetected_chromedriver as uc


def feather_it(data=None, filename=None):

    """
    data: expected to be list of dict. Each dict is a product' data
    """

    # Get keys from 1st entry in data
    productKeys = list(data[0])

    # Convert data into a list of list, each list holds just the values
    listOfProductValues = [[*i.values()] for i in data]

    # Empty placeholder for later
    dataToSave = {}

    # Create featherfile using Pandas to save data
    if len(data) != 0:
        for i, p in enumerate(listOfProductValues):
            dataToSave[i] = p
            df = pd.DataFrame.from_dict(
                dataToSave, orient='index', columns=productKeys)
        if os.path.exists(filename):
            df0 = pd.read_feather(filename)
            df = df0.reset_index(drop=True).append(df).reset_index(drop=True)
            df.to_feather(filename)
        else:
            df.to_feather(filename)

    if len(data) == 0:
        print('>>> No feather saved: 0 products')


def check_feather(local_path, feathername):
    df = pd.read_feather(local_path + feathername)
    print(df.head(n=10))
# check_feather(local_path='C:/Users/sar02/Desktop/shop_crawlers/parknshop/data/', feathername='20220505parknshop.ft')


def start_boto_session(service_name):
    session = boto3.session.Session()

    if service_name == 's3':
        client = session.client('s3',
                                region_name='REDACTED',
                                endpoint_url='REDACTED',
                                aws_access_key_id='REDACTED',
                                aws_secret_access_key='REDACTED')
        return client


def bucket_it(local_path, bucketname, folder_key, feathername, client=None):

    # Check if we're provided with a client
    if client is None:
        client = start_boto_session(service_name='s3')
    else:
        # Check if our client is S3
        if 's3' in str(client._endpoint):
            pass
        else:
            print('Client is not an S3 service:')
            return

    # Check if local_path ends with /
    if '/' not in local_path[-1]:
        local_path = local_path + '/'

    # UPLOAD SHOP DATA FILES
    client.upload_file(local_path + feathername,  # Path to local file
                       bucketname,  # Bucket name
                       folder_key+feathername, ExtraArgs={'ACL': 'public-read'})


def start_driver(url, isSetWindow=False, pos=(0, -1350)):
    # Start engine
    driver = uc.Chrome()
    if isSetWindow:
        # Position properly, https://is.gd/O8498h
        driver.set_window_position(*pos)
        driver.maximize_window()
    driver.get(url)
    print('Driver started ... ')
    return driver


def start_driver_persist(url, isSetWindow=False, pos=(0, -1350)):

    # Try until we get killed!
    while True:
        try:
            driver = start_driver(url, isSetWindow, pos)
            return driver
        except:
            print('Driver start fail. Trying again until you kill me ...')
