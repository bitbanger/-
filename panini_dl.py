import ll

from tqdm import tqdm

url = 'https://support.paniniamerica.net/replacement-card-selection'

HEADERS = {
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

# You can pass activity, activity+year, activity+year+brand, and activity+year+brand+program
# Passing all 4 gets you the card list, but passing fewer gets you the list of IDs for the next
# field
@ll.cache()
def req(raw=False, **extra_payload):
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

	def _raw_req(url, headers, payload):
		return ll.post(url, headers=headers, payload=payload)

	resp = _raw_req(url, HEADERS, payload)

	# print(j:=ll.json(ll.post(url, headers=headers, payload=payload))['data'])
	if raw:
		return ll.json(resp)['data']
	else:
		return ll.map(ll.vals, ll.json(resp)['data'])




# def list(sport, year, brand, set):
	# return req(


def _fix(x):
	if x is None:
		return []
	elif isinstance(x, str):
		return [x]
	else:
		return x

sets = {}

def get_sets(sports=None, years=None, brands=None, programs=None):
	sports = _fix(sports)
	years = _fix(years)
	brands = _fix(brands)
	programs = _fix(programs)
	for activity, activity_id in req():
		if sports and activity not in sports:
			continue

		for (year,) in req(activity=activity_id):
			if years and year not in years:
				continue

			for brand, _ in req(activity=activity_id, year=str(year)):
				if brands and brand not in brands:
					continue

				for program, _, program_id, _ in req(activity=activity_id, year=str(year), brand=brand):
					if programs and program not in programs:
						continue

					for set_name, set_id in req(activity=activity_id, year=str(year), brand=brand, program=str(program_id)):
						# yield set_name, set_id
						# for card in req(activity=activity_id, year=str(year), brand=brand, program=str(program_id), card_set=str(set_id), save=True):
						sn = f"{activity} {year} {brand} {program} {set_name}"
						for bn in ('Donruss', 'Score', 'Playoff'):
							sn = sn.replace(f'{bn} {bn}', f'Panini {bn}')
							if f'{bn}' in sn and f'Panini' not in sn:
								sn = sn.replace(f'{bn}', f'Panini {bn}')
							yield (sn, set_id, {
								'sports': [activity_id],
								'years': [str(year)],
								'brands': [brand],
								'programs': [str(program_id)],
								'sets': [str(set_id)],
							})

def get_cards(set_results):
	# for set_name, set_id in req(activity=activity_id, year=str(year), brand=brand, program=str(program_id)):
	for set_name, set_id, kwargs in set_results:
		if sets and set_name not in sets:
			continue
		print(set_name)
		continue

		cards = req(raw=True, card_set=str(set_id), **kwargs)

		id, _, pos, team, cnum, pname, snum = card
		yield {
			'card_num': cnum,
			'name': pname,
			'id': id,
			'pos': pos,
			'seq_num': snum,
			'team': team,
			'sport': activity,
			'year': year,
			'brand': brand,
			'program': program,
			'set': set_name,
		}

haves = []
for fn in ll.ls('new_scp_csvs', rel=True):
	if not fn.endswith('.csv'):
		continue
	set = next(ll.csv(fn, stream=True))['console-name']
	set = set.replace('Cards ', '')
	set = set.replace('&', 'and')
	year = ll.regf('[0-9]'*4)(set)
	if 'Topps' in set:
		continue
	if 'Leaf' in set:
		continue

	brand = 'Panini'
	for br in ('Donruss ', 'Playoff ', 'Score '):
		if br in set:
			brand = br.strip()
		rest = set.split(brand)[-1].strip()

	if rest.startswith('Contenders '):
		rest = 'Playoff ' + rest

	haves.append((year, brand, rest))


have_programs = []
have_alls = []
sethier = ll.json('hierarchy_of_sports_sets.json')
for sport, l1 in sethier.items():
	q = [l1]
	pref = ''
	while len(q) > 0:
		if not isinstance(q[0], dict):
			q = q[1:]
			continue
		for x, v in q[0].items():
			print(x)
			q.append(v)
		q = q[1:]
	for e in l1:
		if 'Panini' in e:
			brand = 'Panini'
			set = e.split('Panini ')[-1]
			year = e.split(' ')[0]
			have_programs.append(set)
			# have_alls.append((year, brand, set))

for set_result in get_sets(sports='Football', years=[2025]):
	sn = set_result[0]
	year = sn.split(' ')[1]
	brand = sn.split(' ')[2]
	rest = ' '.join(sn.split(' ')[3:])

	pf = max(['']+[pf for pf in have_programs if rest.startswith(pf)], key=len)
	if not pf:
		continue
	program = pf
	rest = rest.replace(f'{program} ', '')
	print((year, brand, program, rest))
	print('\t', end='')
	print(have_alls[0])

	if (year, brand, rest) in have_programs:
		print((year, brand, rest))
	# print(type(set_result[0]))
	# Football Cards 2015 Panini Contenders Draft Picks Old School Colors
	# for card in get_cards([set_result]):
		# print(card)
		# quit()
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
