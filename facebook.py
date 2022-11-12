import requests
import os
import boto3
import time

FB_PAGEID = os.getenv('FB_PAGEID')
FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')
MEDIA_URL = os.getenv('MEDIA_URL')
DYNAMODB_TABLE_RECORDS = os.getenv('DYNAMODB_TABLE_RECORDS')
API_URL = 'https://graph.facebook.com/v15.0/'


class Facebook:

    def __init__(self, text, media):

        self.text = text
        self.media = media
        self.page_id = FB_PAGEID
        self.access_token = FB_ACCESS_TOKEN
        self.media_url = MEDIA_URL
        self.api_url = API_URL
        self.photos_endpoint = self.api_url + self.page_id + '/photos'
        self.videos_endpoint = self.api_url + self.page_id + '/videos'
        self.post_receipt = None

    def post_image(self):
        payload = {
            "message": self.text,
            "url": self.media_url + self.media[0],
            "access_token": FB_ACCESS_TOKEN,
        }
        print(payload)
        response = requests.post(self.photos_endpoint, params=payload).json()
        self.post_receipt = response

    def post_video(self):
        payload = {
            "description": self.text,
            "file_url": self.media_url + self.media[0],
            "access_token": self.access_token,
        }
        print(payload)
        response = requests.post(self.videos_endpoint, params=payload).json()
        self.post_receipt = response

    def post_album(self):
        while len(self.media) > 1:
            payload = {
                "url": self.media_url + self.media.pop(),
                "access_token": FB_ACCESS_TOKEN,
            }
            requests.post(self.photos_endpoint, params=payload).json()
            print(payload)
        payload = {
            "message": self.text,
            "url": self.media_url + self.media[0],
            "access_token": FB_ACCESS_TOKEN,
        }
        print(payload)
        response = requests.post(self.photos_endpoint, params=payload).json()
        print(response)
        self.post_receipt = response

    def record_post(self):
        dynamodb = boto3.client('dynamodb')
        item = {
            "site": {"S": 'Facebook'},
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
            print(f"{self.post_receipt} Facebook post receipt failed to post")
        else:
            print(f"{self.post_receipt} Facebook post receipt POSTED")

    def post(self):
        if len(self.media) > 1:
            print("post album")
            self.post_album()
        elif self.media[0][-3:].lower() == 'mp4':
            print("post video")
            self.post_video()
        else:
            print("post image")
            self.post_image()
        self.record_post()
