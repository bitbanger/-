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

	json = ll.json(ll.soup(ll.sel(f'https://www.sportscardspro.com/consoles-autocomplete/{sport}-cards')).find_all('pre')[0].text)
	with open(fn, 'w+') as f:
		f.write(ll.csv(('label', 'value')) + '\n')
		for row in json:
			f.write(ll.csv((row['label'], row['value'])) + '\n')

	return json # it's the same as the parsed CSV, so...

@ll.cache(stale=STALE)
def get_sets(sport, year, brand, set_words):
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

		sets.append((label, cid))

	return sets

def ready_set_downloads(sport, sets, token):
	base_url = 'https://www.pricecharting.com'

	for set_name, cid in sets:
		url = dl_url(cid, token)

		# TODO: put set code back in?
		csv_name = ll.alphanums(set_name, also=' ').replace(' ', '_').lower() + '.csv'
		csv_name = f'{sport}_{csv_name}'

		yield csv_name, url

	return


def verify_sets(sport, dl_sets):
	print(f'{len(dl_sets)} sets to download ([bold yellow3]{sport}[/bold yellow3]):')
	for x in dl_sets:
		print(f'\t{x[0]}')
	print('')
	return ll.yn(f'Download the above {len(dl_sets)} [bold yellow3]{sport}[/bold yellow3] sets?')


def download_sets(sport, dl_sets, token, outp_dir):
	os.makedirs(outp_dir, exist_ok=True)

	it = ready_set_downloads(sport, dl_sets, token)

	it = ll.track(it, total=len(dl_sets), title=f'Downloading [blue]{sport}[/blue]:')
	for csv_name, csv_url in it:
		@ll.cache(stale=STALE)
		def _dl(url, odir, cname):
			ll.sleep(3)
			ll.sel_dl(
				csv_url,
				dst_dir=outp_dir,
				dst_name=csv_name,
				clobber=True,
				headless=True,
				cookies='.COOKIE',
			)

		_dl(csv_url, outp_dir, csv_name)


def coordinate(sport, year, brand, set_words, token, force, outp_dir):
	# Get the set names to download
	dl_sets = get_sets(sport, year, brand, set_words)
	if (not force) and (not verify_sets(sport, dl_sets)):
		return

	# Download them
	download_sets(sport, dl_sets, token, outp_dir)


def main():
	ap = ArgumentParser()

	ap.add_argument('-s', '--sport', type=str, required=True)
	ap.add_argument('-y', '--year', type=int, required=True)
	ap.add_argument('-b', '--brand', type=str, default='panini')
	ap.add_argument('-f', '--force', action='store_true')
	ap.add_argument('-o', '--output-dir', default='scp_csvs')

	ap.add_argument('words', type=str, nargs='*')

	args = ap.parse_args()

	sport = args.sport
	year = args.year
	brand = args.brand
	set_words = [x.strip().lower() for x in args.words]
	force = args.force

	token = ll.env('SCP_API_TOKEN')

	# Do it!
	# def coordinate(sport, year, brand, set_words, token, force, outp_dir):
	coordinate(sport, year, brand, set_words, token, force, args.output_dir)


if __name__ == '__main__':
	main()
