#!/usr/bin/env python

from twython import Twython
import itertools
import logging

log = logging.getLogger(__name__)

TWITTER_STATUS_URL_TEMPLATE = 'https://twitter.com/i/web/status/{id}'

class TweetBot:
	def __init__(self, app_key, app_secret, oauth_token, oauth_token_secret):
		self.account = Twython(app_key, app_secret, oauth_token, oauth_token_secret)
		self.step = 15 

	def verify_credentials(self):
		# https://dev.twitter.com/rest/reference/get/account/verify_credentials
		info = self.account.verify_credentials(include_entities=False, skip_status=True, include_email=False)
		name = info.get('name', None)
		if name is None:
			log.error('Could not verify credentials')
		else:
			log.info('Logged in as @{name}, tweets: {tweets}, followers: {followers}'.format(
				name = name,
				tweets = info['statuses_count'],
				followers = info['followers_count']))
		return info

	def upload_twitter_picture(self, picture_path):
		photo = open(picture_path, 'rb')
		log.debug("Uploading '{}'".format(picture_path))
		response = self.account.upload_media(media=photo)
		return response['media_id']

	def reply_media_tweet(self, status, reply_id, media_path):
		media_id = self.upload_twitter_picture(media_path)
		tweet = self.account.update_status(status=status, media_ids=[media_id], in_reply_to_status_id=reply_id)
		return tweet

	def reply_text_tweet(self, status, reply_id):
		tweet = self.account.update_status(status=status, in_reply_to_status_id=reply_id)
		log.info('Responded with text to {}'.format(reply_id))
		return tweet

	def rate_limit_remaining(self):
		rate_limit = self.account.get_lastfunction_header('x-rate-limit-remaining')
		log.info('Rate limit remaining: {}'.format(rate_limit))
		return rate_limit

	def favorite(self, status_id):
		tweet = self.account.create_favorite(id=status_id)
		log.debug('Favorited tweet {}'.format(status_id))
		return tweet

	# Find first tweet mentioning any element of query_list_OR
	# in the tweet text (excluding user names).
	# Only tweets for which predicate_func(tweet) is truthy are returned.
	# Returns a tuple of the found status/tweet and what element of
	# the query_list_OR was identified.
	# Returns (None, None) if no matching tweets were found.
	def find_single_tweet(self, query_list_OR, predicate_func):
		counter = 0
		while counter <= len(query_list_OR):
			current_query = query_list_OR[counter:counter+self.step]
			log.debug("Searching for '{}'".format(', '.join(current_query)))
			statuses = self.account.search(q=' OR '.join(current_query), count=50)['statuses']
			log.debug("Found {} matching tweets".format(len(statuses)))
			self.rate_limit_remaining()
			counter += self.step
			for status in statuses:
				# Should be able to identify which part of the query list was mentioned
				text = status['text'].lower()
				found = None
				for query_item in current_query:
					if text.rfind(query_item.lower()) > -1:
						found = query_item
						break
				if found is None:
					continue
				# Identified query part should not be part of tweeting user's name
				if found.lower() in status['user']['screen_name'].lower():
					continue
				# Identified query part should not be part of a mentioned user's name
				mentions = status['entities'].get('user_mentions')
				for m in mentions:
					if found.lower() in m['screen_name'].lower():
						continue
				# Identified query part should not be in user name being replied to
				if found.lower() in (status['in_reply_to_screen_name'] or '').lower():
					continue
				# Should return True for the passed predicate_func
				if not predicate_func(status):
					continue
				log.info(TWITTER_STATUS_URL_TEMPLATE.format(id=status['id']))
				log.info(status['text'].replace('\n',' '))
				return (status, found)
		log.warn("No tweets matching '{}' were found".format(query_list_OR))
		return (None, None)

# Attempt to fill format_str with sentences from text
# (in the order returned by create_sentence_combinations)
# to produce a result shorter or equal to length.
# For every sentence combination, it is attempted to fit optional as well.
# format_str must have placeholders {optionl} and {text}.
# Makes sure the result has a full stop at the end
# Returns None if no sentences could be fitted
def fit_sentences(format_str, optional, text, length):
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

	for combination in create_sentence_combinations(text):
		# First try to fit optional, then try without
		for opt in [optional, '']:
			fitted = format_str.format(optional=opt, text='. '.join(combination))
			fitted = fitted + '.' if not fitted.endswith('.') else fitted
			if len(fitted) <= length:
				log.debug('Fit {} / {} sentences, {} / {} chars, included optional: "{}"'.format(
					len(combination), len(text.split('. ')), len(fitted), length, opt))
				return fitted
	# No sentence could be fitted
	log.warn("No sentence of '{}' could be fitted".format(text))
	return None