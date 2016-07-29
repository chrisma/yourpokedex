#!/usr/bin/env python

from __future__ import print_function
from twython import Twython
from credentials import *
from pokedex_data import pokedex
from pprint import pprint
from fancy_text import italic, bold
import itertools
import random
import logging
import sys

TWEET_LENGTH = 140
LENGTH_MEDIA_URL = 24
MEDIA_TWEET_LENGTH = TWEET_LENGTH - LENGTH_MEDIA_URL
STEP = 15
LANGUAGES = ['de','en','es','fr','it','ja','ko','zh']
PICTURE_PATH_TEMPLATE = 'pokemon-sugimori/{id}.png'
TWITTER_STATUS_URL_TEMPLATE = 'https://twitter.com/{screen_name}/status/{id}'
TWITTER_ACCOUNT_NAME = 'yourpokedex'

def verify_credentials(account):
	# https://dev.twitter.com/rest/reference/get/account/verify_credentials
	info = account.verify_credentials(include_entities=False, skip_status=True, include_email=False)
	name = info.get('name', None)
	if name is None:
		logging.error('Could not verify credentials')
	else:
		logging.info('Logged in as @{name}, tweets: {tweets}, followers: {followers}'.format(
			name = name.encode('utf-8'),
			tweets = info['statuses_count'],
			followers = info['followers_count']))
	return info

def fetch_from_pokedex(pokedex, name):
	return next((p for p in pokedex if name in p['names'].values()), None)

def _should_respond(tweet):
	# https://dev.twitter.com/overview/api/tweets
	# Shouldn't have interacted with tweet previously
	if tweet['favorited']:
		return False
	# Shouldn't be a retweet
	if tweet.get('retweeted_status') is not None:
		return False
	# Should be in supported language, can be 'und' if unknown
	if tweet['lang'] not in LANGUAGES:
		return False
	# Should not be a quote of another tweet
	if tweet.get('quoted_status_id', False):
		return False
	# Should not have been retweeted yet
	if int(tweet['retweet_count']) > 0:
		return False
	# Should not have too many favorites yet
	if int(tweet['favorite_count']) > 1:
		return False
	# Should not include possibly sensitive URLs
	if tweet.get('possibly_sensitive'):
		return False
	return True

def find_tweet(account, query_list_OR):
	counter = 0
	while counter <= len(query_list_OR):
		current_query = query_list_OR[counter:counter+STEP]
		logging.debug("Searching for '{}'".format(', '.join(current_query)))
		statuses = account.search(q=' OR '.join(current_query), count=50)['statuses']
		rate_limit = account.get_lastfunction_header('x-rate-limit-remaining')
		logging.info('Rate limit remaining: {}'.format(rate_limit))
		logging.info("Found {} matching tweets".format(len(statuses)))
		counter += STEP
		for status in statuses:
			# Should be able to identify which part of the query list was mentioned
			text = status['text'].lower().encode('utf-8')
			found = None
			for query_item in current_query:
				if text.rfind(query_item.lower()) > -1:
					found = query_item
			if found is None:
				continue
			# Identified query part should not be part of user's name
			if status['user']['screen_name'].lower().find(found.lower()) > -1:
				continue
			# Identified query part should not be part of a mentioned user's name
			mentions = status['entities'].get('user_mentions')
			for m in mentions:
				if found.lower() in m['screen_name'].lower():
					continue
			if not _should_respond(status):
				continue
			return (status, found)
	return None, None

def construct_tweet_text(screen_name, pokemon, language):
	# Return different options of text shortening
	def create_text_options(text):
		sentences = text.split('. ')
		options = []
		for i in range(len(sentences), 0, -1):
			for subset in itertools.combinations(sentences, i):
				options.append(subset)
		return options

	def create_fitting_text(prefix, text, length):
		for option in create_text_options(text):
			fitted = prefix + '. '.join(option)
			fitted = fitted + '.' if not fitted.endswith('.') else fitted
			if len(fitted) <= length:
				logging.debug('Managed to fit {} / {} sentences: {} / {} chars'.format(
					len(option), len(text.split('. ')), len(fitted), length))
				return fitted
		# No sentence could be fitted
		return None

	name = pokemon['names'][language]
	logging.debug("Constructing tweet '{}' in '{}'".format(name, language))
	name = bold(name)
	genus = ', ' + italic(pokemon['genus'][language])
	sep = ': '
	flavor_texts = pokemon['flavor_texts'][language]
	flavor_text = random.choice(flavor_texts)['text']
	logging.debug('Chose one flavor text from {}'.format(len(flavor_texts)))

	screen_name = '@' + screen_name if not screen_name.startswith('@') else screen_name
	screen_name += ' '

	status = screen_name + name + genus + sep + flavor_text
	if len(status) <= MEDIA_TWEET_LENGTH:
		logging.debug('Can include genus: {} / {} chars'.format(len(status), MEDIA_TWEET_LENGTH))
		return (status, True)

	logging.debug('Cannot include genus: {} / {} chars'.format(len(status), MEDIA_TWEET_LENGTH))
	fitted_status = create_fitting_text(screen_name + name + sep, flavor_text, MEDIA_TWEET_LENGTH)
	if fitted_status is not None:
		logging.debug('Can use media tweet')
		return (fitted_status, True)
	else:
		logging.info('Cannot fit any sentence into media tweet. Dropping media.')
		fitted_status = create_fitting_text(screen_name + name + sep, flavor_text, TWEET_LENGTH)
		return (fitted_status, False)

def upload_twitter_picture(account, picture_path):
	photo = open(picture_path, 'rb')
	logging.debug("Uploading '{}'".format(picture_path))
	response = account.upload_media(media=photo)
	return response['media_id']

def reply_media_tweet(account, status, reply_id, media_path):
	media_id = upload_twitter_picture(account, media_path)
	tweet = account.update_status(status=status, media_ids=[media_id], in_reply_to_status_id=reply_id)
	logging.debug('Responded with media to {}'.format(reply_id))
	return tweet

def reply_text_tweet(account, status, reply_id):
	tweet = account.update_status(status=status, in_reply_to_status_id=reply_id)
	logging.debug('Responded with text to {}'.format(reply_id))
	return tweet

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	logging.getLogger('requests').setLevel(logging.WARN)
	logging.getLogger('requests_oauthlib').setLevel(logging.WARN)
	logging.getLogger('oauthlib').setLevel(logging.WARN)
	
	logging.debug('Started!')
	account = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

	random.shuffle(pokedex)
	poke_names = [p['names']['en'].encode('utf-8') for p in pokedex]

	poke_tweet, pokemon_name = find_tweet(account, poke_names)
	if poke_tweet is None:
		logging.warn('No pokemon tweets found :(')
		sys.exit()

	tweet_lang = poke_tweet['lang']
	screen_name = poke_tweet['user']['screen_name']
	reply_id = poke_tweet['id']
	logging.info(TWITTER_STATUS_URL_TEMPLATE.format(screen_name=screen_name, id=reply_id))

	logging.info('user: @{user}, lang: {lang}, mentioned: {poke}'.format(
		user=screen_name, lang=tweet_lang, poke=pokemon_name))
	logging.debug("text: '{}'".format(poke_tweet['text'].encode('utf-8')))

	pokemon = fetch_from_pokedex(pokedex, pokemon_name)
	status, is_media_tweet = construct_tweet_text(screen_name, pokemon, tweet_lang)
	logging.info(status)

	if status is None:
		logging.debug('Could not construct tweet')
		sys.exit()

	if is_media_tweet:
		picture_path = PICTURE_PATH_TEMPLATE.format(id=pokemon['id'])
		tweet = reply_media_tweet(account, status, reply_id, picture_path)
	else:
		tweet = reply_text_tweet(account, status, reply_id)
	logging.info(TWITTER_STATUS_URL_TEMPLATE.format(screen_name=TWITTER_ACCOUNT_NAME, id=tweet['id']))
	
	# Tweets that are favorited are not replied to again
	account.create_favorite(id=reply_id)
	logging.debug('Favorited tweet {}'.format(reply_id))
