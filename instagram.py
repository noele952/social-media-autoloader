import requests
import time
import os
import boto3

DYNAMODB_TABLE_RECORDS = os.getenv('DYNAMODB_TABLE_RECORDS')
DYNAMODB_TABLE_HASHTAGS = os.getenv('DYNAMODB_TABLE_HASHTAGS')
IG_ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
IG_BUSINESS_ACCOUNT = os.getenv('IG_BUSINESS_ACCOUNT')
MEDIA_URL = os.getenv('MEDIA_URL')

API_URL = 'https://graph.facebook.com/v15.0/'


class Instagram:

    def __init__(self, text, media):
        self.password = ''
        self.access_token = IG_ACCESS_TOKEN
        self.ig_business_account = IG_BUSINESS_ACCOUNT
        self.api_url = API_URL
        self.media_url = MEDIA_URL
        self.media_endpoint = API_URL + self.ig_business_account + '/media'
        self.media_publish_endpoint = API_URL + self.ig_business_account + '/media_publish'
        self.text = text
        self.media = media
        self.post_id = None
        self.hashtags = None
        self.post_receipt = None

    def record_post(self):
        dynamodb = boto3.client('dynamodb')
        item = {
            "site": {"S": 'Instagram'},
            "epochtime": {"N": str(round(time.time()))},
            "post_receipt": {"S": str(self.post_receipt)},
            "post_id": {"S": self.post_id},
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
            print(f"{self.post_id} Instagram post receipt failed to post")
        else:
            print(f"{self.post_id} Instagram post receipt POSTED")
        print(self.post_receipt)

    def post(self):
        if len(self.media) > 1:
            self.post_carousel()
        elif self.media[0][-3:].lower() == 'mp4':
            self.post_video()
        else:
            self.post_image()
        self.post_hashtags()
        self.record_post()

    def post_image(self):
        payload = {
            "image_url": self.media_url + self.media[0],
            "caption": self.text,
            "access_token": IG_ACCESS_TOKEN,
        }
        response = requests.post(self.media_endpoint, params=payload).json()
        print(response)
        payload = {
            "creation_id": response['id'],
            "access_token": IG_ACCESS_TOKEN
        }
        response = requests.post(self.media_publish_endpoint, params=payload).json()
        self.post_receipt = response
        try:
            self.post_id = response['id']
        except Exception as e:
            print(e)

    def post_video(self):
        # post media
        payload = {
            "media_type": "VIDEO",
            "video_url": self.media_url + self.media[0],
            "caption": self.text,
            "access_token": self.access_token
        }
        response = requests.post(self.media_endpoint, params=payload).json()
        print(response)
        active = True
        loop_count = 0
        while active:
            loop_count += 1
            # wait until video processed before trying to post
            time.sleep(30)
            response = requests.get(f"{self.api_url}{response['id']}?fields=status_code",
                                    params={"access_token": self.access_token}).json()
            print(response)
            if response['status_code'] == 'FINISHED':
                active = False
            elif response['status_code'] == 'ERROR':
                active = False
            elif loop_count == 5:
                active = False
        payload = {
            "creation_id": response['id'],
            "access_token": self.access_token
        }
        response = requests.post(self.media_publish_endpoint, params=payload).json()
        print(response)
        self.post_receipt = response
        try:
            self.post_id = response['id']
        except Exception as e:
            print(e)

    def post_carousel(self):
        carousel_list = []
        for item in self.media:
            payload = {
                "image_url": self.media_url + item,
                "is_carousel_item": True,
                "access_token": self.access_token,
            }
            response = requests.post(self.media_endpoint, params=payload).json()
            carousel_list.append(response['id'])
        payload = {
            "caption": self.text,
            "media_type": "CAROUSEL",
            "children": ','.join(carousel_list),
            "access_token": self.access_token
        }
        response = requests.post(self.media_endpoint, params=payload).json()
        payload = {
            "creation_id": response['id'],
            "access_token": self.access_token
        }
        response = requests.post(self.media_publish_endpoint, params=payload).json()
        self.post_receipt = response
        try:
            self.post_id = response['id']
        except Exception as e:
            print(e)

    def post_hashtags(self):
        if self.hashtags is not None:
            payload = {
                "message": self.get_hashtags(),
                "access_token": self.access_token
            }
            requests.post(f"{self.api_url}{self.post_id}/comments", params=payload).json()

    def get_hashtag_lists(self):
        hashtag_lists = []
        # turn hashtag string into a list
        for hashtag in self.hashtags.replace(',', '').split():
            dynamodb = boto3.client('dynamodb')
            response = dynamodb.get_item(
                TableName=DYNAMODB_TABLE_HASHTAGS,
                Key={'name': {"S": hashtag}}
            )
            print(response)
            try:
                hashtag_list = (response['Item']['hashtags']['S']).split()
                hashtag_lists.append(hashtag_list)
            except Exception as e:
                print(e)
        return hashtag_lists

    def get_top_hashtags(self, hashtag_lists, num_allowed=25):
        tags_final = []
        num = round(num_allowed / len(hashtag_lists))
        total_tags = 0
        for a_list in hashtag_lists:
            total_tags += len(a_list)
            if len(a_list) < num:
                for number in range(len(a_list)):
                    tags_final.append(a_list.pop(0))
            else:
                for number in range(num):
                    tags_final.append(a_list.pop(0))
        print(f"total tags:{total_tags}")
        if (len(tags_final) < num_allowed) or (len(tags_final) == total_tags):
            for a_list in hashtag_lists:
                if len(a_list) > 0:
                    tags_final.append(a_list.pop(0))
        return tags_final

    def get_hashtags(self):
        hashtag_lists = self.get_hashtag_lists()
        top_hashtags = self.get_top_hashtags(hashtag_lists)
        return ' '.join(top_hashtags)
