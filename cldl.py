import ll

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

# You can pass activity, activity+year, activity+year+brand, and activity+year+brand+program
# Passing all 4 gets you the card list, but passing fewer gets you the list of IDs for the next
# field
def req(**extra_payload):
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

	resp = ll.post(url, headers=headers, payload=payload)
	return ll.map(ll.vals, ll.json(resp)['data'])




# def list(sport, year, brand, set):
	# return req(


sets = {}

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


					url, headers = curl2url('chkl.curl'), curl2headers('chkl.curl')
					data = {
						'activity': activity_id,
						'year': year,
						'brand': brand,
						'program': program_id,
						'card_set': '',
						'card': '',
						'replace_wo_inventory': 1,
						'from_frontend': 0,
					}
					rows = ll.csv(ll.post(url, headers=headers, payload=data))
					for card in rows:
						yield card

ap = ArgumentParser()
ap.add_argument('-s', '--sports', nargs='*')
ap.add_argument('-y', '--years', type=int, nargs='*')
ap.add_argument('-p', '--programs', nargs='*')
args = ap.parse_args()

rows = []
for i, card in enumerate(tqdm(get_all(sports=args.sports, years=args.years, programs=args.programs))):
	# print(card)
	rows.append(card)
print(ll.csv(rows))
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
