#!/usr/bin/env python

from credentials import *
from tweeter import Tweeter
from pokedex import Pokedex
from fancy_text import italic, bold
import itertools
import random
import logging
import sys

TWEET_LENGTH = 140
LENGTH_MEDIA_URL = 24
MEDIA_TWEET_LENGTH = TWEET_LENGTH - LENGTH_MEDIA_URL
TWITTER_STATUS_URL_TEMPLATE = 'https://twitter.com/{screen_name}/status/{id}'
TWITTER_ACCOUNT_NAME = 'yourpokedex'
PICTURE_PATH_TEMPLATE = 'pokemon-sugimori/{id}.png'

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
	if tweet['lang'] not in Pokedex.supported_languages:
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
	tweeter = Tweeter(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
	poke_names = Pokedex.all_names(lang='en', random_order=True)

	poke_tweet, pokemon_name = tweeter.find_tweet(poke_names, _should_respond)
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

	pokemon = Pokedex.entry(pokemon_name)
	status, is_media_tweet = construct_pokedex_tweet(screen_name, pokemon, tweet_lang)
	logging.info(status)

	if status is None:
		logging.debug('Could not construct tweet')
		sys.exit()

	if is_media_tweet:
		picture_path = PICTURE_PATH_TEMPLATE.format(id=pokemon['id'])
		tweet = tweeter.reply_media_tweet(status, reply_id, picture_path)
	else:
		tweet = tweeter.reply_text_tweet(status, reply_id)
	logging.info(TWITTER_STATUS_URL_TEMPLATE.format(screen_name=TWITTER_ACCOUNT_NAME, id=tweet['id']))
	
	# Tweets that are favorited are not replied to again
	tweeter.favorite(reply_id)
