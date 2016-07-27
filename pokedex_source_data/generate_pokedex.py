#!/usr/bin/env python

# cvs data from https://github.com/veekun/pokedex

from __future__ import print_function
import logging
import csv
from pprint import pprint

def readCSV(filename):
	with open(filename) as f:
		return list(csv.DictReader(f))

def fetch(list_of_dicts, search_id):
	return next((item for item in list_of_dicts if int(item['id']) == int(search_id)), None)

def get_flavor_texts(flavor_list, id, languages):
	ft_for_p = [ft for ft in flavor_list if int(ft['species_id']) == int(id)]
	flavors = {}
	for ft in ft_for_p:
		language_code = fetch(languages, ft['language_id'])['iso639']
		text = ft['flavor_text'].replace('\n', ' ').decode('utf-8')
		selected = {'text': text, 'version_ids': [ft['version_id']]}
		if flavors.get(language_code) is None:
			flavors[language_code] = [selected]
		else:
			appended = False
			for f in flavors[language_code]:
				if f['text'] == text:
					f['version_ids'].append(ft['version_id'])
					appended = True
					break
			if not appended:
				flavors[language_code].append(selected)
	return flavors

def get_names_and_genus(name_list, id, languages):
	names_for_p = [n for n in name_list if int(n['pokemon_species_id']) == int(id)]
	names = {}
	genus = {}
	for n in names_for_p:
		language_code = fetch(languages, n['local_language_id'])['iso639']
		names[language_code] = n['name'].decode('utf-8')
		genus[language_code] = n['genus'].decode('utf-8')
	return names, genus

if __name__ == '__main__':
	# logging.basicConfig(level=logging.INFO)
	logging.basicConfig(level=logging.DEBUG)
	logging.debug('Started!')
	pokemon = readCSV('pokemon.csv')
	species_names = readCSV('pokemon_species_names.csv')
	flavor_texts = readCSV('pokemon_species_flavor_text.csv')
	languages = readCSV('languages.csv')

	pokedex = []
	for pocket_monster in pokemon:
		if int(pocket_monster['id']) <= 151:
			logging.debug(pocket_monster['id'] + ' ' + pocket_monster['identifier'])
			names, genus = get_names_and_genus(species_names, pocket_monster['id'], languages)
			pokedex.append({
				'names': names,
				'genus': genus,
				'weight': pocket_monster['weight'],
				'height': pocket_monster['height'],
				'flavor_texts': get_flavor_texts(flavor_texts, pocket_monster['id'], languages),
				'id': pocket_monster['id']
			})

	pprint(pokedex)


	# first_gen = [p for p in pokemon if int(p['id']) <= 151]
	# print(pokemon['identifier'], pokemon['weight'])
	# print(first_gen)
