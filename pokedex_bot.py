#!/usr/bin/env python

from tweeter import TweetBot, fit_sentences
from pokedex import Pokedex
from fancy_text import italic, bold
import random
import logging
import sys
import os
import argparse
import re

log = logging.getLogger('poke_bot')

TWEET_LENGTH = 280
TWITTER_ACCOUNT_NAME = 'yourpokedex'
PICTURE_PATH_TEMPLATE = os.path.dirname(os.path.realpath(__file__)) + '/pokemon-sugimori/{id}.png'

# Try to import the variables defined in credentials.py
# If that does not exist (e.g. on Heroku), fall back to environment variables
try:
	from credentials import APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
except ImportError as error:
	print('Info: {e}'.format(e=error))
	print('Info: Cannot load credentials.py. Will use environment variables.')
	try:
		APP_KEY = os.environ['APP_KEY']
		APP_SECRET = os.environ['APP_SECRET']
		OAUTH_TOKEN = os.environ['OAUTH_TOKEN']
		OAUTH_TOKEN_SECRET = os.environ['OAUTH_TOKEN_SECRET']
	except KeyError as error:
		print('Error: {e} not found in environment variables'.format(e=error))
		print('Error: Could not retrieve credentials from either credentials.py or environment variables. Make sure either is set.')
		# can't do anything without credentials, so quit
		sys.exit()

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
	# Should not be a manual retweet, "RT ..."
	if tweet['text'].lower().startswith("rt "):
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
	# Should not contain "pokemon" in Twitter handle, i.e. be a Pokémon account
	banned_handles = ['Pokemon', 'Pokémon', 'Poke', 'Poké', 'Pkmn', 'Bot', 'Trainer']
	for word in banned_handles:
		if word.lower() in tweet['user']['screen_name'].lower():
			return False
	# Should not mention user with pokémon name as Twitter handle
	for mention in tweet['entities']['user_mentions']:
		for poke_name in [name.lower() for name in Pokedex.all_names_all_lang()]:
			if poke_name in mention['screen_name'].lower():
				log.debug("Skipping Pokémon Twitter handle mention: \"{}\"".format(mention['screen_name']))
				return False
	# Should not be a Pokemon GO alert bot, that automatically
	# posts expiry times in the format 'until 13:00:00AM'
	if re.search(r'\d+:\d+:\d+', tweet['text'].lower()):
		log.debug("Skipped Pokemon GO bot: \"{}\"".format(tweet['text'].replace('\n', ' ')))
		return False
	return True

def poke_reply(screen_name, poke_name, lang="en"):
	log.debug("@{user} ({lang}) Pokemon: '{poke}'".format(
		user=screen_name,
		lang=lang,
		poke=poke_name))
	pokemon = Pokedex.entry(poke_name, lang)
	if pokemon is None:
		log.debug('No Pokedex entry in {} found for "{}"'.format(lang, poke_name))
		return (None, None)
	genus = ', ' + italic(pokemon['genus'])
	flavor_text = random.choice(pokemon['flavor_texts'])['text']
	reply_start = '@' + screen_name + ' ' + bold(pokemon['names'])
	format_str = reply_start + '{optional}' + ': ' + '{text}'
	text = fit_sentences(format_str, genus, flavor_text, TWEET_LENGTH)
	log.debug(text)
	picture_path = PICTURE_PATH_TEMPLATE.format(id=pokemon['id'])
	return (text, picture_path)


def run(manual_info=None, dry_run=False):
	tweet = None
	if manual_info:
		text, pic_path = poke_reply(manual_info[0], manual_info[1], manual_info[2])
		print(text)
		print(pic_path)
	else:
		poke_names = Pokedex.all_names(lang='en', random_order=True)
		poke_bot = TweetBot(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
		tweet, poke_name = poke_bot.find_single_tweet(poke_names, _should_respond)

	text = None
	if tweet is not None:
		text, pic_path = poke_reply(
			screen_name = tweet['user']['screen_name'],
			poke_name = poke_name,
			lang = tweet['lang'])
	
	if text is not None:
		if dry_run or manual_info:
			log.info('DRY RUN! Not posting anything.')
			print(text)
			print(pic_path)
		else:
			tweet_id = tweet['id']
			poke_bot.reply_media_tweet(text, tweet_id, pic_path)
			# Tweets that are favorited are not replied to again
			poke_bot.favorite(tweet_id)


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	logging.getLogger('requests').setLevel(logging.WARN)
	logging.getLogger('requests_oauthlib').setLevel(logging.WARN)
	logging.getLogger('oauthlib').setLevel(logging.WARN)
	
	log.debug('Started!')

	parser = argparse.ArgumentParser(description='Twitter bot that replies with Pokemon info to users who mention Pokemon.')
	parser.add_argument('-d', '--dry-run', action='store_true', help="print tweet without actually posting it.")
	parser.add_argument('-m', nargs=3, metavar=('n', 'p', 'l'),
		help="pass info '<screen_name> <poke_name> <lang>' manually. Implies '-d'")
	args = parser.parse_args()

	run(manual_info=args.m, dry_run=args.dry_run)

	# https://dev.twitter.com/rest/reference/get/statuses/retweets_of_me
	# https://dev.twitter.com/rest/reference/get/statuses/mentions_timeline
