import boto3
import os
import json


def upload_to_s3(syllabus: dict, dept: str):
    """
    Upload the syllabus info of the department to s3
    :param syllabus: dictionary representation of the syllabus info
    :param dept: abbr of the department. e.g. "PSE"
    :return: dict :=
        {
            'Expiration': 'string',
            'ETag': 'string',
            'ServerSideEncryption': 'AES256'|'aws:kms',
            'VersionId': 'string',
            'SSECustomerAlgorithm': 'string',
            'SSECustomerKeyMD5': 'string',
            'SSEKMSKeyId': 'string',
            'SSEKMSEncryptionContext': 'string',
            'RequestCharged': 'requester'
        }
    """
    s3 = boto3.resource('s3', region_name="ap-northeast-1")
    syllabus_object = s3.Object(os.getenv('BUCKET_NAME'), os.getenv('OBJECT_PATH') + dept + '.json')
    resp = syllabus_object.put(
        ACL='public-read',
        Body=bytes(json.dumps(syllabus).encode('UTF-8')),
        ContentType='application/json',
        CacheControl='max-age=86400, must-revalidate'
    )
    return resp
