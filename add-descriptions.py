#!/usr/bin/env python3

__author__ = "Sushain K. Cherivirala"
__version__ = "0.1.0"
__license__ = "GPLv3+"

import argparse
import json
import logging
import operator
import re
import urllib.request

from sync import DEFAULT_OAUTH_TOKEN, ORGANIZATION, list_repos

ISO_639_CODES = {'abk': 'ab', 'aar': 'aa', 'afr': 'af', 'aka': 'ak', 'sqi': 'sq', 'amh': 'am', 'ara': 'ar', 'arg': 'an', 'hye': 'hy', 'asm': 'as', 'ava': 'av', 'ave': 'ae', 'aym': 'ay', 'aze': 'az', 'bam': 'bm', 'bak': 'ba', 'eus': 'eu', 'bel': 'be', 'ben': 'bn', 'bih': 'bh', 'bis': 'bi', 'bos': 'bs', 'bre': 'br', 'bul': 'bg', 'mya': 'my', 'cat': 'ca', 'cha': 'ch', 'che': 'ce', 'nya': 'ny', 'zho': 'zh', 'chv': 'cv', 'cor': 'kw', 'cos': 'co', 'cre': 'cr', 'hrv': 'hr', 'ces': 'cs', 'dan': 'da', 'div': 'dv', 'nld': 'nl', 'dzo': 'dz', 'eng': 'en', 'epo': 'eo', 'est': 'et', 'ewe': 'ee', 'fao': 'fo', 'fij': 'fj', 'fin': 'fi', 'fra': 'fr', 'ful': 'ff', 'glg': 'gl', 'kat': 'ka', 'deu': 'de', 'ell': 'el', 'grn': 'gn', 'guj': 'gu', 'hat': 'ht', 'hau': 'ha', 'heb': 'he', 'her': 'hz', 'hin': 'hi', 'hmo': 'ho', 'hun': 'hu', 'ina': 'ia', 'ind': 'id', 'ile': 'ie', 'gle': 'ga', 'ibo': 'ig', 'ipk': 'ik', 'ido': 'io', 'isl': 'is', 'ita': 'it', 'iku': 'iu', 'jpn': 'ja', 'jav': 'jv', 'kal': 'kl', 'kan': 'kn', 'kau': 'kr', 'kas': 'ks', 'kaz': 'kk', 'khm': 'km', 'kik': 'ki', 'kin': 'rw', 'kir': 'ky', 'kom': 'kv', 'kon': 'kg', 'kor': 'ko', 'kur': 'ku', 'kua': 'kj', 'lat': 'la', 'ltz': 'lb', 'lug': 'lg', 'lim': 'li', 'lin': 'ln', 'lao': 'lo', 'lit': 'lt', 'lub': 'lu', 'lav': 'lv', 'glv': 'gv', 'mkd': 'mk', 'mlg': 'mg', 'msa': 'ms', 'mal': 'ml', 'mlt': 'mt', 'mri': 'mi', 'mar': 'mr', 'mah': 'mh', 'mon': 'mn', 'nau': 'na', 'nav': 'nv', 'nob': 'nb', 'nde': 'nd', 'nep': 'ne', 'ndo': 'ng', 'nno': 'nn', 'nor': 'no', 'iii': 'ii', 'nbl': 'nr', 'oci': 'oc', 'oji': 'oj', 'chu': 'cu', 'orm': 'om', 'ori': 'or', 'oss': 'os', 'pan': 'pa', 'pli': 'pi', 'fas': 'fa', 'pol': 'pl', 'pus': 'ps', 'por': 'pt', 'que': 'qu', 'roh': 'rm', 'run': 'rn', 'ron': 'ro', 'rus': 'ru', 'san': 'sa', 'srd': 'sc', 'snd': 'sd', 'sme': 'se', 'smo': 'sm', 'sag': 'sg', 'srp': 'sr', 'gla': 'gd', 'sna': 'sn', 'sin': 'si', 'slk': 'sk', 'slv': 'sl', 'som': 'so', 'sot': 'st', 'azb': 'az', 'spa': 'es', 'sun': 'su', 'swa': 'sw', 'ssw': 'ss', 'swe': 'sv', 'tam': 'ta', 'tel': 'te', 'tgk': 'tg', 'tha': 'th', 'tir': 'ti', 'bod': 'bo', 'tuk': 'tk', 'tgl': 'tl', 'tsn': 'tn', 'ton': 'to', 'tur': 'tr', 'tso': 'ts', 'tat': 'tt', 'twi': 'tw', 'tah': 'ty', 'uig': 'ug', 'ukr': 'uk', 'urd': 'ur', 'uzb': 'uz', 'ven': 've', 'vie': 'vi', 'vol': 'vo', 'wln': 'wa', 'cym': 'cy', 'wol': 'wo', 'fry': 'fy', 'xho': 'xh', 'yid': 'yi', 'yor': 'yo', 'zha': 'za', 'zul': 'zu',  'hbs': 'sh',  'pes': 'fa'}  # noqa: E501
DEFAULT_APY_URL = 'https://beta.apertium.org/apy'
GITHUB_API = 'https://api.github.com'


def describe(token, repo_name, description):
    headers = {
        'Authorization': 'bearer {}'.format(token),
    }
    request_data = json.dumps({
        'name': repo_name,
        'description': description,
    }).encode("utf-8")
    url = '{}/repos/{}/{}'.format(GITHUB_API, ORGANIZATION, repo_name)
    request = urllib.request.Request(url, data=request_data, headers=headers, method='PATCH')
    try:
        urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        logging.error('Describing %s failed: %s', repo_name, error.read(), exc_info=True)


def main():
    parser = argparse.ArgumentParser(description='Add descriptions to Apertium repositories.')
    parser.add_argument('--token', '-t', help='GitHub OAuth token', required=(DEFAULT_OAUTH_TOKEN is None), default=DEFAULT_OAUTH_TOKEN)
    parser.add_argument('--apy-url', '-a', help='Apertium APy URL', default=DEFAULT_APY_URL)
    parser.add_argument('--verbose', '-v', action='count', help='add verbosity (maximum -vv)', default=0)
    args = parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        level=levels[min(len(levels) - 1, args.verbose)],
    )

    lang_names = json.loads(urllib.request.urlopen(DEFAULT_APY_URL + '/listLanguageNames?locale=eng').read().decode('utf-8'))

    repos = list(map(operator.itemgetter('node'), list_repos(args.token, extra_nodes=['description'])))
    for repo in repos:
        topics = set(map(lambda repo: repo['topic']['name'], repo['repositoryTopics']['nodes']))
        repo_name = repo['name']
        if repo['description'] is None and not ({'apertium-tools', 'apertium-core'} & topics):
            module_code = re.match('^apertium-(\w{2,3}(_\w+)?)$', repo_name)
            pair_codes = re.match('^apertium-(\w{2,3}(_\w+)?)-(\w{2,3}(_\w+)?)$', repo_name)
            if module_code:
                code = module_code.group(1)
                name = lang_names.get(ISO_639_CODES.get(code, code))
                if name:
                    description = "Apertium linguistic data for {}".format(name)
                    logging.info('Describing %s as %s', repo_name, repr(description))
                    describe(args.token, repo_name, description)
                else:
                    logging.warn('Unable to describe language module %s, have %s=%s', repo_name, code, repr(name))
            elif pair_codes:
                code1, _, code2, _ = pair_codes.groups()
                name1, name2 = lang_names.get(ISO_639_CODES.get(code1, code1)), lang_names.get(ISO_639_CODES.get(code2, code2))
                if name1 and name2:
                    description = "Apertium translation pair for {} and {}".format(name1, name2)
                    logging.info('Describing %s as %s', repo_name, repr(description))
                    describe(args.token, repo_name, description)
                else:
                    logging.warn('Unable to describe pair %s, have %s=%s and %s=%s', repo_name, code1, repr(name1), code2, repr(name2))


if __name__ == '__main__':
    main()
