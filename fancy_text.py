#!/usr/bin/env python

#http://www.fileformat.info/info/unicode/block/mathematical_alphanumeric_symbols/list.htm

bold_unicode = {
 '0': u'\U0001d7ce',
 '1': u'\U0001d7cf',
 '2': u'\U0001d7d0',
 '3': u'\U0001d7d1',
 '4': u'\U0001d7d2',
 '5': u'\U0001d7d3',
 '6': u'\U0001d7d4',
 '7': u'\U0001d7d5',
 '8': u'\U0001d7d6',
 '9': u'\U0001d7d7',
 'A': u'\U0001d400',
 'B': u'\U0001d401',
 'C': u'\U0001d402',
 'D': u'\U0001d403',
 'E': u'\U0001d404',
 'F': u'\U0001d405',
 'G': u'\U0001d406',
 'H': u'\U0001d407',
 'I': u'\U0001d408',
 'J': u'\U0001d409',
 'K': u'\U0001d40a',
 'L': u'\U0001d40b',
 'M': u'\U0001d40c',
 'N': u'\U0001d40d',
 'O': u'\U0001d40e',
 'P': u'\U0001d40f',
 'Q': u'\U0001d410',
 'R': u'\U0001d411',
 'S': u'\U0001d412',
 'T': u'\U0001d413',
 'U': u'\U0001d414',
 'V': u'\U0001d415',
 'W': u'\U0001d416',
 'X': u'\U0001d417',
 'Y': u'\U0001d418',
 'Z': u'\U0001d419',
 'a': u'\U0001d41a',
 'b': u'\U0001d41b',
 'c': u'\U0001d41c',
 'd': u'\U0001d41d',
 'e': u'\U0001d41e',
 'f': u'\U0001d41f',
 'g': u'\U0001d420',
 'h': u'\U0001d421',
 'i': u'\U0001d422',
 'j': u'\U0001d423',
 'k': u'\U0001d424',
 'l': u'\U0001d425',
 'm': u'\U0001d426',
 'n': u'\U0001d427',
 'o': u'\U0001d428',
 'p': u'\U0001d429',
 'q': u'\U0001d42a',
 'r': u'\U0001d42b',
 's': u'\U0001d42c',
 't': u'\U0001d42d',
 'u': u'\U0001d42e',
 'v': u'\U0001d42f',
 'w': u'\U0001d430',
 'x': u'\U0001d431',
 'y': u'\U0001d432',
 'z': u'\U0001d433'}

italic_unicode = {
 'A': u'\U0001d434',
 'B': u'\U0001d435',
 'C': u'\U0001d436',
 'D': u'\U0001d437',
 'E': u'\U0001d438',
 'F': u'\U0001d439',
 'G': u'\U0001d43a',
 'H': u'\U0001d43b',
 'I': u'\U0001d43c',
 'J': u'\U0001d43d',
 'K': u'\U0001d43e',
 'L': u'\U0001d43f',
 'M': u'\U0001d440',
 'N': u'\U0001d441',
 'O': u'\U0001d442',
 'P': u'\U0001d443',
 'Q': u'\U0001d444',
 'R': u'\U0001d445',
 'S': u'\U0001d446',
 'T': u'\U0001d447',
 'U': u'\U0001d448',
 'V': u'\U0001d449',
 'W': u'\U0001d44a',
 'X': u'\U0001d44b',
 'Y': u'\U0001d44c',
 'Z': u'\U0001d44d',
 'a': u'\U0001d44e',
 'b': u'\U0001d44f',
 'c': u'\U0001d450',
 'd': u'\U0001d451',
 'e': u'\U0001d452',
 'f': u'\U0001d453',
 'g': u'\U0001d454',
 'h': u'\U0001d629', #\U0001d455 is reserved
 'i': u'\U0001d456',
 'j': u'\U0001d457',
 'k': u'\U0001d458',
 'l': u'\U0001d459',
 'm': u'\U0001d45a',
 'n': u'\U0001d45b',
 'o': u'\U0001d45c',
 'p': u'\U0001d45d',
 'q': u'\U0001d45e',
 'r': u'\U0001d45f',
 's': u'\U0001d460',
 't': u'\U0001d461',
 'u': u'\U0001d462',
 'v': u'\U0001d463',
 'w': u'\U0001d464',
 'x': u'\U0001d465',
 'y': u'\U0001d466',
 'z': u'\U0001d467'}

def italic(s):
	return ''.join([italic_unicode.get(c, c) for c in s])

def bold(s):
	return ''.join([bold_unicode.get(c, c) for c in s])

if __name__ == '__main__':
	test = 'This is a TEST string 1234' 
	print(test)
	print(italic(test))
	print(bold(test))
