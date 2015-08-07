# -*- coding: utf-8 -*-
#!/usr/bin/python


# Based on https://github.com/peterwalker78/twitterbot


import tweepy
import datetime
import time
from os import environ
import pymongo

# Twitter parameters
try:
    consumer_key = environ['TWITTER_CONSUMER_KEY']
    consumer_secret = environ['TWITTER_CONSUMER_SECRET']
    access_token = environ['TWITTER_ACCESS_TOKEN_KEY']
    access_token_secret = environ['TWITTER_ACCESS_TOKEN_SECRET']
    twitter_account = environ['TWITTER_ACCOUNT']
except KeyError, e:
    raise Exception('Please define TWITTER_ACCOUNT, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN_KEY and TWITTER_ACCESS_TOKEN_SECRET as environment variables')

# Connect with Twitter
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
user = twitter_account


# Mongo parameters
try:
    MONGODB_URI = 'mongodb://%s:%s@%s:%d/%s' % (
    environ['MONGO_DBUSER'], environ['MONGO_DBPASSWORD'], environ['MONGO_URL'], int(environ['MONGO_PORT']),
    environ['MONGO_DBNAME'])
except KeyError, e:
    raise Exception('Please define MONGO_DBUSER, MONGO_DBPASSWORD, MONGO_URL, MONGO_PORT and MONGO_DBNAME as environment variables')

# Connect with mongo
client = pymongo.MongoClient(MONGODB_URI)
db = client.get_default_database()

pelitweets_db = db['movies']
responded_tweets_db = db['responded_tweets']

# Get last 100 mentions of my timeline
mymentions = api.mentions_timeline()
for mention in mymentions:
    tweet_time = mention.created_at
    since = datetime.datetime(2014, 03, 15)

    # Avoid old tweets
    if tweet_time < since:
        continue

    # Check if the mention has been already responded
    query = {'mention_id': mention.id}
    doc = responded_tweets_db.find_one(query)

    # Not responded
    if not doc:
        tweet_text = unicode(mention.text)
        movie_name = tweet_text[tweet_text.find(u'@pelitweets') + 12:]

        # Get Movie with the required title
        query = {'movie_title': movie_name}
        movie = pelitweets_db.find_one(query)

        # Reply with ratings
        reply_text = "@%s %s ratings: IMDB: %s, Filmaffinity: %s, Twitter: %s" % (mention.author.screen_name, movie_name, movie['movie_rating_imdb'], movie['movie_rating_fa'], movie['movie_rating_average'])
        print reply_text
        api.update_status(reply_text, mention.id)
        time.sleep(1)

        # Avoid response again
        json_tweet_data = {
            'mention_id': mention.id
        }

        responded_tweets_db.insert(json_tweet_data)


