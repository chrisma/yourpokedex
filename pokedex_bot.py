#!/usr/bin/env python

from credentials import *
from tweeter import TweetBot, fit_sentences
from pokedex import Pokedex
from fancy_text import italic, bold
import random
import logging
import sys
import os
import argparse
import re


TWEET_LENGTH = 140
TWITTER_ACCOUNT_NAME = 'yourpokedex'
PICTURE_PATH_TEMPLATE = os.path.dirname(os.path.realpath(__file__)) + '/pokemon-sugimori/{id}.png'

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
	# Should not be a Pokemon GO alert bot, that automatically
	# posts expiry times in the format 'until 13:00:00AM'
	if re.search('\d+:\d+:\d+', tweet['text'].lower()):
		logging.debug("Skipped Pokemon GO bot: \"{}\"".format(tweet['text'].replace('\n', ' ')))
		return False
	return True

def poke_reply(screen_name, poke_name, lang="en"):
	logging.debug("@{user} ({lang}) Pokemon: '{poke}'".format(
		user=screen_name,
		lang=lang,
		poke=poke_name))
	pokemon = Pokedex.entry(poke_name, lang)
	if pokemon is None:
		logging.debug('No Pokedex entry in {} found for "{}"'.format(lang, poke_name))
		return (None, None)
	genus = ', ' + italic(pokemon['genus'])
	flavor_text = random.choice(pokemon['flavor_texts'])['text']
	reply_start = '@' + screen_name + ' ' + bold(pokemon['names'])
	format_str = reply_start + '{optional}' + ': ' + '{text}'
	text = fit_sentences(format_str, genus, flavor_text, TWEET_LENGTH)
	logging.debug(text)
	picture_path = PICTURE_PATH_TEMPLATE.format(id=pokemon['id'])
	return (text, picture_path)


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	logging.getLogger('requests').setLevel(logging.WARN)
	logging.getLogger('requests_oauthlib').setLevel(logging.WARN)
	logging.getLogger('oauthlib').setLevel(logging.WARN)
	
	logging.debug('Started!')

	parser = argparse.ArgumentParser(description='Twitter bot that replies with Pokemon info to users who mention Pokemon.')
	parser.add_argument('-d', '--dry-run', action='store_true', help="print tweet without actually posting it.")
	parser.add_argument('-m', nargs=3, metavar=('n', 'p', 'l'),
		help="pass info '<screen_name> <poke_name> <lang>' manually. Implies '-d'")
	args = parser.parse_args()

	tweet = None
	if args.m:
		text, pic_path = poke_reply(args.m[0], args.m[1], args.m[2])
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
		if args.dry_run or args.m:
			logging.info('DRY RUN! Not posting anything.')
		else:
			tweet_id = tweet['id']
			poke_bot.reply_media_tweet(text, tweet_id, picture_path)
			# Tweets that are favorited are not replied to again
			poke_bot.favorite(tweet_id)

	# https://dev.twitter.com/rest/reference/get/statuses/retweets_of_me
	# https://dev.twitter.com/rest/reference/get/statuses/mentions_timeline