#-*- coding: utf-8 -*-
import boto3

#
#Code here taken from documentation 
#You can change server, keys, buckets to change storage
#

AWS_SERVER_PUBLIC_KEY = 'WW_aDw3b4sixD3fQa3cs'
AWS_SERVER_SECRET_KEY = 'q-wPXCPIF5lyHX9rZRuLGSw6v5zv_hwDLmSKYyTR'

class CloudConnectionFailed(Exception):
    def __init__(self, text):
        self.txt = text

class CloudUploadFailed(Exception):
    def __init__(self, text):
        self.txt = text

def createConnection(public_key, secret_key):
    try:
        session = boto3.Session(
            aws_access_key_id=public_key,
            aws_secret_access_key=secret_key,
        )
        s3 = session.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net'
        )
    except Exception as e:
        raise CloudConnectionFailed('[ERR] Соединение с облаком не установлено: ' + str(e))
    return s3

def uploadFile(session, file_name, bucket):
    try:
        session.upload_file(file_name, bucket, file_name)
    except Exception as e:
        raise CloudUploadFailed('[ERR] Ошибка при загрузке файла в облако: ' + str(e))

def clearBucket(session, bucket):
    forDeletion = []
    for key in session.list_objects(Bucket='video-analytics')['Contents']:
        element = {'Key': str(key['Key'])}
        forDeletion.append(element)
    response = session.delete_objects(Bucket=bucket, Delete={'Objects': forDeletion})
    print(response)


#session = createConnection(AWS_SERVER_PUBLIC_KEY, AWS_SERVER_SECRET_KEY)
#uploadFile(session, 'output/ter_1/ch_0/main_door/main_door_1579869012.avi', 'video-analytics')
#clearBucket(session, 'video-analytics')

