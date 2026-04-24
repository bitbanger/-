import ll
import os
import re as _re
import time

from rich import print

from argparse import ArgumentParser


STALE = ll.days(7)


def dl_url(uid, token):
	return f'https://www.sportscardspro.com/price-guide/download-custom?t={token}&console-uids={uid}'

@ll.cache(stale=STALE)
def set_list(sport):
	# if ll.fexists(fn:=f'sets/scp-sets-{sport}.csv'):
		# return ll.csv(fn)
	fn = f'sets/scp-sets-{sport}.csv'
	if ll.fexists(fn) and ll.age(fn)<STALE:
		return ll.csv(fn)

	json = ll.json(ll.soup(ll.sel(f'https://www.sportscardspro.com/consoles-autocomplete/{sport}-cards')).find_all('pre')[0].text)
	with open(fn, 'w+') as f:
		f.write(ll.csv(('label', 'value')) + '\n')
		for row in json:
			f.write(ll.csv((row['label'], row['value'])) + '\n')

	return json # it's the same as the parsed CSV, so...


@ll.memcache
def set_lists():
	sport2rows = ll.dd()
	for sport in ('football', 'basketball', 'baseball', 'star-wars'):
		sport2rows[sport].extend(set_list(sport))
	return sport2rows


@ll.memcache
def cid2pids(cid, stream=False):
	def _it():
		for sport, rows in set_lists().items():
			for row in rows:
				if str(row['value']) == str(cid):
					csvfn = 'new_scp_csvs/' + setname2csvname(sport, row['label'])
					for crow in ll.csv(csvfn, stream=True):
						yield crow['id']
					return

	return _it() if stream else list(_it())


@ll.cache(stale=STALE)
def get_sets(sport, year, brand, set_words, exclude_words=None):
	if exclude_words is None:
		exclude_words = []

	sets = []
	for row in set_list(sport):
		label, cid = row['label'], row['value']

		if ll.regf('(\d\d\d\d)')(label) != str(year):
			continue
		rest = label[label.index(str(year))+4:].strip()
		if not rest.startswith(brand):
			continue
		rest = rest[rest.index(brand)+len(brand):].strip()
		if not all(w.lower() in rest.lower() for w in set_words):
			continue
		if any(w.lower() in rest.lower() for w in exclude_words):
			continue

		sets.append((label, cid))

	return sets


def setname2csvname(sport, setname):
	csvname = ll.alphanums(setname, also=' ').replace(' ', '_').lower() + '.csv'
	csvname = f'{sport}_{csvname}'
	return csvname


def ready_set_downloads(sport, sets, token):
	base_url = 'https://www.pricecharting.com'

	for set_name, cid in sets:
		url = dl_url(cid, token)

		# TODO: put set code back in?
		csv_name = setname2csvname(sport, set_name)

		yield csv_name, url

	return


def verify_sets(sport, dl_sets):
	print(f'{len(dl_sets)} sets to download ([bold yellow3]{sport}[/bold yellow3]):')
	for x in dl_sets:
		print(f'\t{x[0]}')
	print('')
	return ll.yn(f'Download the above {len(dl_sets)} [bold yellow3]{sport}[/bold yellow3] sets?')

last_dl = None
def download_sets(sport, dl_sets, token, outp_dir, courtesy_wait=1):
	global last_dl

	os.makedirs(outp_dir, exist_ok=True)

	it = ready_set_downloads(sport, dl_sets, token)

	emojis = {
		'baseball': '⚾️',
		'basketball': '🏀',
		'football': '🏈',
		'star-wars': '🚀',
	}
	if sport in emojis:
		it = ll.track(it, total=len(dl_sets), title=f'{emojis[sport]}:')
	else:
		it = ll.track(it, total=len(dl_sets), title=f'[blue]{sport}[/blue]:')
	for csv_name, csv_url in it:
		@ll.cache(stale=STALE)
		def _dl(url, odir, cname):
			global last_dl

			if last_dl is None:
				last_dl = time.time()
			elif (gap:=((now:=time.time())-last_dl)) <= courtesy_wait:
				time.sleep(courtesy_wait-gap)

			# ll.sleep(1)
			ll.sel_dl(
				csv_url,
				cookies='.COOKIE',

				dst_dir=outp_dir,
				dst_name=csv_name,
				clobber=True,
				headless=True,

				backoff_after=2,
				wait=3,
				max_wait=30,
			)

		_dl(csv_url, outp_dir, csv_name)


def coordinate(sport, year, brand, set_words, token, force, args):
	# Get the set names to download
	dl_sets = get_sets(sport, year, brand, set_words)
	if args.minimal:
		dl_sets = [min(dl_sets, key=lambda t: len(t[0]))]

	if (not force) and (not verify_sets(sport, dl_sets)):
		return

	# Download them
	download_sets(sport, dl_sets, token, args.output_dir)


def main():
	ap = ArgumentParser()

	ap.add_argument('-s', '--sport', type=str, required=True)
	ap.add_argument('-y', '--year', type=int, required=True)
	ap.add_argument('-b', '--brand', type=str, default='panini')
	ap.add_argument('-f', '--force', action='store_true')
	ap.add_argument('-o', '--output-dir', default='new_scp_csvs')
	ap.add_argument('-m', '--minimal', action='store_true')

	ap.add_argument('words', type=str, nargs='*')

	args = ap.parse_args()

	sport = args.sport
	year = args.year
	brand = args.brand
	set_words = ' '.join([x.strip().lower().replace('-', ' ') for x in args.words]).split()
	force = args.force

	token = ll.env('SCP_API_TOKEN')

	# Do it!
	# def coordinate(sport, year, brand, set_words, token, force, outp_dir):
	coordinate(sport, year, brand, set_words, token, force, args)


if __name__ == '__main__':
	main()
