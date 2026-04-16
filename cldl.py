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
	payload = {k: str(v) for k, v in payload.items()}

	resp = post(url, headers=headers, payload=payload)
	return ll.map(ll.vals, ll.json(resp)['data'])




# def list(sport, year, brand, set):
	# return req(


sets = {}


def cards(sport, year, brand, program, csv=False):
	url, headers = curl2url('chkl.curl'), curl2headers('chkl.curl')
	data = {
		'activity': str(sport_id(sport)),
		'year': str(year),
		'brand': brand,
		'program': str(program_id(sport, year, brand, program)),
		'card_set': '',
		'card': '',
		'replace_wo_inventory': '1',
		'from_frontend': '0',
	}

	resp = post(url, headers=headers, payload=data)
	return resp if csv else ll.csv(resp)


@ll.memcache
def sport_id(x):
	for sport, sport_id in req():
		if str(x).lower() == str(sport).lower():
			return sport_id


@ll.memcache
def program_id(s,y,b,p):
	s = str(s).lower()
	y = str(y).lower()
	b = str(b).lower()
	p = str(p).lower()

	for sport, sport_id in req():
		sport = str(sport).lower()
		if sport != s:
			continue
		for yeartup in req(sport=sport_id):
			if type(yeartup) in (list, tuple):
				year = str(yeartup[0])
			if year != y:
				continue
			for brand, brand_id in req(sport=sport_id, year=year):
				brand = str(brand).lower()
				if brand != b:
					continue
				for program, _, program_id, _ in req(sport=sport_id, year=year, brand=brand):
					program = str(program).lower()
					if program == p:
						return program_id


def sets(sports=None, years=None, brands=None, programs=None):
	def _fix(x):
		if x is None:
			return []
		elif isinstance(x, str):
			return [x]
		else:
			return x

	hier = ll.dd(lambda: ll.dd(lambda: ll.dd(list)))

	sport_tups = req()
	for sport, sport_id in ll.track(sport_tups, title='Indexing sets: '):
		for (year, _) in req(sport=sport_id):
			for brand, brand_id in req(activity=sport_id, year=str(year)):
				for program, nyear, program_id, release_date in req(activity=sport_id, year=str(year), brand=brand, from_frontend='2'):
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

		for yeartup in req(sport=sport_id):
			if type(yeartup) in (list, tuple):
				year = yeartup[0]
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


def download_all(sports=None, years=None, brands=None, programs=None, force=False):
	sports = ll.map(ll.lower, sports) if sports else None
	years = ll.map(int, years) if years else None
	brands = ll.map(ll.lower, brands) if brands else None
	programs = ll.map(ll.lower, programs) if programs else None
	for (s,y,b,p) in ll.track(flat_sets(), title='Downloading: '):
		if sports and s.lower() not in sports:
			continue
		if years and int(y) not in years:
			continue
		if brands and b.lower() not in brands:
			continue
		if programs and p.lower() not in programs:
			continue
		os.makedirs((d:=f'panini_checklists/{s}/{y}/{b}'.lower()), exist_ok=True)
		path = os.path.join(d, mkfn(p))
		if (not force) and (ll.fexists(path) and len(ll.lines(ll.read(path).strip()))>1):
			continue
		with open(path, 'w+') as f:
			f.write(cards(s,y,b,p,csv=True))


def main():
	ap = ArgumentParser()
	ap.add_argument('-s', '--sports', nargs='*')
	ap.add_argument('-y', '--years', type=int, nargs='*')
	ap.add_argument('-b', '--brands', nargs='*')
	ap.add_argument('-p', '--programs', nargs='*')
	ap.add_argument('-f', '--force', action='store_true')
	args = ap.parse_args()

	# print(next(get_all(sports='football')))

	download_all(sports=args.sports, years=args.years, brands=args.brands, programs=args.programs, force=args.force)

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
