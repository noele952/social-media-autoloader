import boto3
import json
import requests
from authlib.integrations.requests_client import OAuth1Auth
import os
import time
import sys

DYNAMODB_TABLE_RECORDS = os.getenv('DYNAMODB_TABLE_RECORDS')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
PARAMETER_NAME_TWITTER = os.getenv('PARAMETER_NAME_TWITTER')
MEDIA_URL = os.getenv('MEDIA_URL')

TWITTER_MEDIA_ENDPOINT = 'https://upload.twitter.com/1.1/media/upload.json'
TWITTER_ENDPOINT = 'https://api.twitter.com/1.1/statuses/update.json'


class Tweet:

    def __init__(self, text):
        self.text = self.check_tweet_length(text)
        self.media = None
        self.media_id = None
        self.media_ids = []
        self.aws_parameter_name = PARAMETER_NAME_TWITTER
        self.api_key = TWITTER_API_KEY
        self.api_secret = TWITTER_API_SECRET
        self.auth = self.authenticate()
        self.post_receipt = None
        self.processing_info = None
        self.total_bytes = 0

    def authenticate(self):
        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(Name=self.aws_parameter_name, WithDecryption=True)
        token = json.loads(parameter['Parameter']['Value'])
        auth = OAuth1Auth(
            client_id=self.api_key,
            client_secret=self.api_secret,
            token=token['oauth_token'],
            token_secret=token['oauth_token_secret'],
        )
        return auth

    def check_tweet_length(self, text):
        if len(text) > 270:
            return text[:270]
        return text

    def tweet_video(self):
        response = requests.get(MEDIA_URL + self.media[0])
        print(f"response: {response}")
        open('/tmp/' + self.media[0], "wb").write(response.content)
        self.total_bytes = os.path.getsize('/tmp/' + self.media[0])
        self.upload_init()
        self.upload_append()
        self.upload_finalize()

        # Publishes Tweet with attached video
        request_data = {
            'status': self.text,
            'media_ids': self.media_id
        }
        response = requests.post(url=TWITTER_ENDPOINT, data=request_data, auth=self.auth).json()
        self.post_receipt = response

    def tweet_photo(self):
        for media in self.media:
            response = requests.get(MEDIA_URL + media)
            print(f"response: {response}")
            open('/tmp/' + media, "wb").write(response.content)
            with open('/tmp/' + media, 'rb') as file:
                data = file.read()
            payload = {
                "media": data,
                "media_category": "tweet_image"
            }
            response = requests.post('https://upload.twitter.com/1.1/media/upload.json', auth=self.auth,
                                     files=payload).json()
            self.media_ids.append(str(response['media_id']))
        payload = {
            "text": self.text,
            "media": {
                "media_ids": self.media_ids
            }
        }
        response = requests.post('https://api.twitter.com/2/tweets', auth=self.auth, json=payload).json()
        self.post_receipt = response

    def record_post(self):
        dynamodb = boto3.client('dynamodb')
        item = {
            "site": {"S": 'Twitter'},
            "epochtime": {"N": str(round(time.time()))},
            "post_receipt": {"S": str(self.post_receipt)},
            "text": {"S": self.text},
            "media": {"S": str(self.media)},
        }
        response = dynamodb.put_item(
            TableName=DYNAMODB_TABLE_RECORDS,
            Item=item
        )
        print(response)
        response_code = response['ResponseMetadata']['HTTPStatusCode']
        if response_code != 200:
            print(f"{self.post_receipt} Twitter post receipt failed to post")
        else:
            print(f"{self.post_receipt} Twitter post receipt POSTED")

    def tweet(self):
        print(self.media)
        print(self.media[0][-3:].lower())
        if self.media is None:
            response = requests.post('https://api.twitter.com/2/tweets',
                                     auth=self.auth,
                                     json={"text": self.text}).json()
            print(response)
            self.post_receipt = response
        elif (len(self.media) == 1) and (self.media[0][-3:].lower() == 'mp4'):
            self.tweet_video()
        else:
            self.tweet_photo()
        self.record_post()

    def upload_init(self):
        # Initializes Upload
        print('INIT')
        request_data = {
            'command': 'INIT',
            'media_type': 'video/mp4',
            'total_bytes': self.total_bytes,
            'media_category': 'tweet_video'
        }
        req = requests.post(url=TWITTER_MEDIA_ENDPOINT, data=request_data, auth=self.auth)
        print(req.json())
        media_id = req.json()['media_id']
        self.media_id = media_id
        print('Media ID: %s' % str(media_id))

    def upload_append(self):
        # Uploads media in chunks and appends to chunks uploaded
        segment_id = 0
        bytes_sent = 0
        file = open('/tmp/' + self.media[0], 'rb')
        print(f"total_bytes:{self.total_bytes}")
        while bytes_sent < self.total_bytes:
            chunk = file.read(4 * 1024 * 1024)
            print('APPEND')
            request_data = {
                'command': 'APPEND',
                'media_id': self.media_id,
                'segment_index': segment_id
            }
            files = {
                'media': chunk
            }
            req = requests.post(url=TWITTER_MEDIA_ENDPOINT, data=request_data, files=files, auth=self.auth)
            if req.status_code < 200 or req.status_code > 299:
                print(req.status_code)
                print(req.text)
                sys.exit(0)
            segment_id = segment_id + 1
            bytes_sent = file.tell()
            print('%s of %s bytes uploaded' % (str(bytes_sent), str(self.total_bytes)))
        print('Upload chunks complete.')

    def upload_finalize(self):
        # Finalizes uploads and starts video processing
        print('FINALIZE')
        request_data = {
            'command': 'FINALIZE',
            'media_id': self.media_id
        }
        req = requests.post(url=TWITTER_MEDIA_ENDPOINT, data=request_data, auth=self.auth)
        self.processing_info = req.json().get('processing_info', None)
        self.check_status()

    def check_status(self):
        # Checks video processing status
        if self.processing_info is None:
            return
        state = self.processing_info['state']
        print('Media processing status is %s ' % state)
        if state == u'succeeded':
            return
        if state == u'failed':
            print(self.processing_info)
            sys.exit(0)
        check_after_secs = self.processing_info['check_after_secs']
        print('Checking after %s seconds' % str(check_after_secs))
        time.sleep(check_after_secs)
        print('STATUS')
        request_params = {
            'command': 'STATUS',
            'media_id': self.media_id
        }
        req = requests.get(url=TWITTER_MEDIA_ENDPOINT, params=request_params, auth=self.auth)
        self.processing_info = req.json().get('processing_info', None)
        self.check_status()
