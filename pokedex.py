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

#
# TWITTER
#

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

def upload_twitter_picture(account, picture_path):
	photo = open(picture_path, 'rb')
	logging.debug("Uploading '{}'".format(picture_path))
	response = account.upload_media(media=photo)
	return response['media_id']

def reply_media_tweet(account, status, reply_id, media_path):
	media_id = upload_twitter_picture(account, media_path)
	tweet = account.update_status(status=status, media_ids=[media_id], in_reply_to_status_id=reply_id)
	logging.info('Responded with media to {}'.format(reply_id))
	return tweet

def reply_text_tweet(account, status, reply_id):
	tweet = account.update_status(status=status, in_reply_to_status_id=reply_id)
	logging.info('Responded with text to {}'.format(reply_id))
	return tweet

# Find first tweet mentioning any element of query_list_OR
# in the tweet text (excluding user names).
# Only tweets for which predicate_func(tweet) is truthy are returned.
# Returns a tuple of the found status/tweet and what element of
# the query_list_OR was identified.
# Returns (None, None) if no matching tweets were found.
def find_tweet(account, query_list_OR, predicate_func):
	counter = 0
	while counter <= len(query_list_OR):
		current_query = query_list_OR[counter:counter+STEP]
		logging.debug("Searching for '{}'".format(', '.join(current_query)))
		statuses = account.search(q=' OR '.join(current_query), count=50)['statuses']
		rate_limit = account.get_lastfunction_header('x-rate-limit-remaining')
		logging.info('Rate limit remaining: {}'.format(rate_limit))
		logging.debug("Found {} matching tweets".format(len(statuses)))
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
			if not predicate_func(status):
				continue
			return (status, found)
	return (None, None)

#
# UTILS
#

# Return a list of ordered sentence combinations
# create_sentence_combinations('First. Second. Third.') == [
#	('First', 'Second', 'Third.'),
#	('First', 'Second'),
#	('First', 'Third.'),
#	('Second', 'Third.'),
#	('First',),
#	('Second',),
#	('Third.',)
# ]
def create_sentence_combinations(text):
	sentences = text.split('. ')
	options = []
	for i in range(len(sentences), 0, -1):
		for subset in itertools.combinations(sentences, i):
			options.append(subset)
	return options

# Attempt to fill format_str with sentences from text
# (in the order returned by create_sentence_combinations)
# to produce a result shorter or equal to length.
# For every sentence combination, it is attempted to fit optional as well.
# format_str must have placeholders {optionl} and {text}.
# Makes sure the result has a full stop at the end
# Returns None if no sentences could be fitted
def fit_sentences(format_str, optional, text, length):
	for combination in create_sentence_combinations(text):
		# First try to fit optional, then try without
		for opt in [optional, '']:
			fitted = format_str.format(optional=opt, text='. '.join(combination))
			fitted = fitted + '.' if not fitted.endswith('.') else fitted
			if len(fitted) <= length:
				logging.debug("Including '{}'".format(opt.encode('utf-8')))
				logging.info('Managed to fit {} / {} sentences: {} / {} chars'.format(
					len(combination), len(text.split('. ')), len(fitted), length))
				return fitted
	# No sentence could be fitted
	return None

#
# POKEDEX
#

# predicate function, returns whether a found pokemon
# tweet should be responded to
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

def fetch_from_pokedex(pokedex, name):
	return next((p for p in pokedex if name in p['names'].values()), None)

def construct_pokedex_tweet(screen_name, pokemon, language):
	name = pokemon['names'][language]
	logging.debug("Building Pokedex tweet: '{}' in '{}'".format(name, language))
	genus = ', ' + italic(pokemon['genus'][language])

	flavor_texts = pokemon['flavor_texts'][language]
	flavor_text = random.choice(flavor_texts)['text']
	logging.debug('Chose one flavor text from {}'.format(len(flavor_texts)))

	format_str = '@' + screen_name + ' ' + bold(name) + '{optional}' + ': ' + '{text}'

	fitted_status = fit_sentences(format_str, genus, flavor_text, MEDIA_TWEET_LENGTH)
	if fitted_status is not None:
		is_media_tweet = True
		logging.debug('Can use media tweet')
	else:
		is_media_tweet = False
		logging.debug('Cannot fit any sentence into media tweet. Dropping media.')
		fitted_status = fit_sentences(format_str, genus, flavor_text, TWEET_LENGTH)
	return (fitted_status, is_media_tweet)


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	logging.getLogger('requests').setLevel(logging.WARN)
	logging.getLogger('requests_oauthlib').setLevel(logging.WARN)
	logging.getLogger('oauthlib').setLevel(logging.WARN)
	
	logging.debug('Started!')
	account = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

	random.shuffle(pokedex)
	poke_names = [p['names']['en'].encode('utf-8') for p in pokedex]

	poke_tweet, pokemon_name = find_tweet(account, poke_names, _should_respond)
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
	status, is_media_tweet = construct_pokedex_tweet(screen_name, pokemon, tweet_lang)
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
