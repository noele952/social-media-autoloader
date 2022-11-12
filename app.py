from instagram import Instagram
from facebook import Facebook
from twitter import Tweet
import json
from datetime import datetime
import boto3
import os

DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')


def post_dynamodb(item):
    dynamodb = boto3.client('dynamodb')

    response = dynamodb.put_item(
        TableName=DYNAMODB_TABLE,
        Item=item
    )
    print(response)


def schedule_repost(post_record):
    try:
        repost = post_record['repost']['S'].lower()
        if repost == 'y':
            posttime = post_record['posttime']['S']
            next_year = int(posttime[:4]) + 1
            new_posttime = str(next_year) + posttime[4:]
            post_record['posttime']['S'] = new_posttime
            posttime_epoch = post_record['posttime_epoch']['N']
            new_posttime_epoch = str(int(posttime_epoch) + 31536000)
            post_record['posttime_epoch']['N'] = new_posttime_epoch
            post_dynamodb(post_record)
    except Exception as e:
        print("no repost")
        print(e)


def make_fb_post(post_record):
    try:
        fb = Facebook(
            text=post_record['text']['S'],
            media=list(post_record['media']['S'].split(', '))
        )
        fb.post()

    except KeyError:
        print(f"Facebook Post: Invalid data\n{post_record}")


def make_ig_post(post_record):
    try:
        ig = Instagram(
            text=post_record['text']['S'],
            media=list(post_record['media']['S'].split(', '))
        )
    except KeyError:
        print(f"IG post: Invalid data\n {post_record}")
        return 0
    try:
        ig.hashtags = post_record['hashtags']['S']
    except KeyError:
        pass
    ig.post()


def make_tw_post(post_record):
    tw = Tweet(
        text=post_record['text']['S']
    )
    try:
        tw.media = list(post_record['media']['S'].split(', '))
    except Exception as e:
        print(e)
    tw.tweet()


def make_post(post_record):
    post_to = post_record['post_to']['S']
    if post_to == 'Facebook':
        make_fb_post(post_record)
    elif post_to == 'Instagram':
        make_ig_post(post_record)
    elif post_to == 'Twitter':
        make_tw_post(post_record)
    else:
        print(f"Post Site Not Recognized: {post_to}")


def lambda_handler(event, context):
    print(event)
    for record in event['Records']:
        print(record)
        try:
            post_record = record['dynamodb']['OldImage']
            print(f"post_record: {post_record}")
            make_post(post_record)
            schedule_repost(post_record)
        except Exception as e:
            print(e)
    return {
        'statusCode': 200,
        'body': json.dumps(f'post schedule checked: {datetime.now()}')
    }
