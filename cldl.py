import ll
import os

from argparse import ArgumentParser
from lbin.curl2py import curl2url, curl2headers, curl2any
from tqdm import tqdm

url = 'https://support.paniniamerica.net/replacement-card-selection'

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en',
    'content-type': 'application/json',
    'origin': 'https://www.paniniamerica.net',
    'priority': 'u=1, i',
    'referer': 'https://www.paniniamerica.net/checklist.html',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
}


@ll.cache()
def post(*a, **kw):
	return ll.post(*a, **kw)


# You can pass activity, activity+year, activity+year+brand, and activity+year+brand+program
# Passing all 4 gets you the card list, but passing fewer gets you the list of IDs for the next
# field
def req(**extra_payload):
	if 'sport' in extra_payload:
		extra_payload['activity'] = extra_payload['sport']
		del extra_payload['sport']

	payload = {
		'activity': '',
		'year': '',
		'brand': '',
		'program': '',
		'card_set': '',
		'card': '',
		'replace_wo_inventory': '1',
		'from_frontend': '0',
	}
	payload.update(extra_payload)

	resp = post(url, headers=headers, payload=payload)
	return ll.map(ll.vals, ll.json(resp)['data'])




# def list(sport, year, brand, set):
	# return req(


sets = {}


@ll.cache()
def cards(sport, year, brand, program, csv=False):
	url, headers = curl2url('chkl.curl'), curl2headers('chkl.curl')
	data = {
		'activity': id(sport),
		'year': str(year),
		'brand': brand,
		'program': id(program),
		'card_set': '',
		'card': '',
		'replace_wo_inventory': 1,
		'from_frontend': 0,
	}

	resp = post(url, headers=headers, payload=data)
	return resp if csv else ll.csv(resp)


@ll.memcache
def id(x):
	if isinstance(x, int) or x.isnumeric():
		return x
	for sport, sport_id in req():
		if x==sport:
			return sport_id
	for sport, sport_id in req():
		for (year,) in req(sport=sport_id):
			for brand, _ in req(activity=sport_id, year=str(year)):
				if brand==x:
					return x # save ourselves any more trouble, but don't pass this pls
				for program, _, program_id, _ in req(activity=sport_id, year=str(year), brand=brand):
					if program==x:
						return program_id


@ll.memcache
def sets(sports=None, years=None, brands=None, programs=None):
	def _fix(x):
		if x is None:
			return []
		elif isinstance(x, str):
			return [x]
		else:
			return x

	hier = ll.dd(lambda: ll.dd(lambda: ll.dd(list)))

	for sport, sport_id in req():
		for (year,) in req(sport=sport_id):
			for brand, brand_id in req(activity=sport_id, year=str(year)):
				for program, nyear, program_id, release_date in req(activity=sport_id, year=str(year), brand=brand):
					hier[sport][year][brand].append(program)
					# print(f'{nyear} {brand} {program} {sport} [grey50]({release_date})[/grey50]')

	return ll.recdict(hier)


@ll.memcache
def flat_sets():
	def _():
		ss = sets()
		for s in ss:
			for y in ss[s]:
				for b in ss[s][y]:
					for p in ss[s][y][b]:
						yield (s,y,b,p)
	return list(_())


def get_all(sports=None, years=None, brands=None, programs=None, sets=None):

	def _fix(x):
		if x is None:
			return []
		elif isinstance(x, str):
			return [x]
		else:
			return x

	sports = _fix(sports)
	years = _fix(years)
	brands = _fix(brands)
	programs = _fix(programs)
	sets = _fix(sets)

	for activity, activity_id in req():
		if sports and activity.lower() not in ll.map(ll.lower, sports):
			continue

		for (year,) in req(activity=activity_id):
			if years and year not in years:
				continue

			for brand, brand_id in req(activity=activity_id, year=str(year)):
				if brands and brand.lower() not in ll.map(ll.lower, brands):
					continue

				for program, _, program_id, _ in req(activity=activity_id, year=str(year), brand=brand):
					if programs and program.lower() not in ll.map(ll.lower, programs):
						continue




def cli(args):
	rows = []
	for i, card in enumerate(tqdm(get_all(sports=args.sports, years=args.years, programs=args.programs))):
		# print(card)
		rows.append(card)

	print(ll.csv(rows))


def mkfn(p):
	fn = p.strip().lower().replace('&', 'and').replace(' ', '_') + '.csv'
	ok = ll.alpha+ll.digits+'._+-'
	fn = ''.join([c for c in fn if c in ok])
	return fn


def main():
	ap = ArgumentParser()
	ap.add_argument('-s', '--sports', nargs='*')
	ap.add_argument('-y', '--years', type=int, nargs='*')
	ap.add_argument('-p', '--programs', nargs='*')
	args = ap.parse_args()

	# print(next(get_all(sports='football')))

	for (s,y,b,p) in ll.track(flat_sets(), title='Downloading: '):
		os.makedirs((d:=f'panini_checklists/{s}/{y}/{b}'.lower()), exist_ok=True)
		with open(mkfn(p), 'w+') as f:
			f.write(cards(s,y,b,p,csv=True))


	quit()

	with open('football.csv', 'w+') as f:
		f.write(','.join(['card_num', 'name', 'id', 'pos', 'seq_num', 'team', 'sport', 'year', 'brand', 'program', 'set']) + '\n')
		try:
			for i, card in enumerate(tqdm(get_all(sports='Football'))):
				if i>0:
					f.write('\n')
				f.write(ll.csv(card))
		except KeyboardInterrupt:
			pass


	quit()


if __name__ == '__main__':
	main()
