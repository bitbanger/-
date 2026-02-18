import ll
import os
import re as _re
import time

from rich import print

from argparse import ArgumentParser


def dl_url(uid, token):
	return f'https://www.pricecharting.com/price-guide/download-custom?t={token}&console-uids={uid}'


def get_sets(sport, year, brand, set_words):
	first_url = f'https://www.pricecharting.com/consoles-autocomplete/{sport}-cards'
	sets = []
	for row in ll.json(first_url):
		if row is None:
			continue
		label, cid = row['label'], row['value']
		_year = ll.regf('(\d\d\d\d)')(label)
		if _year is None:
			continue
		if int(_year) != int(year):
			continue
		rest = label[label.index(year)+4:].strip()
		if not rest.startswith(brand):
			continue
		rest = rest[rest.index(brand)+len(brand):].strip()
		if not all(w.lower() in rest.lower() for w in set_words):
			continue
		print(rest)
		# urls.append(f"https://www.pricecharting.com/console/{label.replace(' ', '-')}")
		sets.append(label)
	# url = base_url + f'/brand/{sport}-cards/{brand}'

	return sets

	urls = []

	sets = []
	while not sets:
		sp = ll.soup(url)
		sets.extend([x for x in sp.find_all('a', href=_re.compile(f'\/console\/{sport}-cards-{year}-{brand}')) if not x.text.startswith("'")])

	sets = sets[::-1]
	sets = [x for x in sets if all(w.lower() in x.text.lower() for w in set_words)]
	sets = sorted(sets, key=lambda x: len(x.text))

	return sets


def download_sets(sport, sets, token):
	base_url = 'https://www.pricecharting.com'

	# for x in ll.track(ll.soup(url).find_all('a', href=_re.compile(f'\/console\/{sport}-cards-{year}-{brand}')), total=total):
	for x in sets:
		# sub_url = base_url + x.attrs['href']
		sub_url = base_url + f"/console/{x.replace(' ', '-')}"

		re = _re.compile('console_uid = "(.*)"')

		set_name = x

		set_code = ''
		for _ in range(15):
			try:
				subsoup = ll.soup(sub_url)
				uid = ll.regf('console_uid = "(.*)"')(subsoup(string=re)[0])

				'''
				scs = subsoup(string=_re.compile('Set Code.*'))
				try:
					set_code = scs[0].split(': ')[-1]
				except IndexError:
					pass
				'''

				break
			except IndexError:
				ll.sleep(3)
				continue

		while not uid:
			ll.sleep(3)
			subsoup = ll.soup(sub_url)
			uid = ll.regf('console_uid = "(.*)"')(subsoup(string=re)[0])

		csv_url = dl_url(uid, token)
		csv_name = ll.alphanums(set_name, also=' ').replace(' ', '_').lower() + '.csv'
		if set_code:
			csv_name = f'{set_code}_{csv_name}'
		csv_name = f'{sport}_{csv_name}'

		yield csv_name, csv_url#, ll.http(csv_url)
		# print(f'{csv_name}\n\t{csv_url}\n')

		time.sleep(3)

		# ll.write(ll.http(csv_url), '

def verify_sets(sport, dl_sets):
	print(f'{len(dl_sets)} sets to download ([bold yellow3]{sport}[/bold yellow3]):')
	for x in dl_sets:
		print(f'\t{x}')
	print('')
	return ll.yn(f'Download the above {len(dl_sets)} [bold yellow3]{sport}[/bold yellow3] sets?')

def download_sets_interactive(sport, dl_sets, token, outp_dir):
	os.makedirs(outp_dir, exist_ok=True)

	it = download_sets(sport, dl_sets, token)
	it = ll.track(it, total=len(dl_sets), title='Downloading:')
	for csv_name, csv_url in it:
		with open(os.path.join(outp_dir, csv_name), 'w+') as f:
			csv = 'DOCTYPE'
			while 'DOCTYPE' in csv:
				# print('.', end='')
				csv = ll.http(csv_url)
			f.write(csv)

def coordinate(sport, year, brand, set_words, token, force, outp_dir):
	# Get the set names to download
	dl_sets = get_sets(sport, year, brand, set_words)
	if not force and not verify_sets(sport, dl_sets):
		return

	# Download them
	download_sets_interactive(sport, dl_sets, token, outp_dir)


def main():
	ap = ArgumentParser()

	ap.add_argument('--sport')
	ap.add_argument('--year')
	ap.add_argument('--brand', default='panini')
	ap.add_argument('--force', action='store_true')

	ap.add_argument('words', nargs='*')

	args = ap.parse_args()

	sport = args.sport
	year = args.year
	brand = args.brand
	set_words = [x.strip().lower() for x in args.words]
	force = args.force

	outp_dir = 'scp_csvs'

	token = ll.env('SCP_API_TOKEN')

	# Do it!
	# def coordinate(sport, year, brand, set_words, token, force, outp_dir):
	coordinate(sport, year, brand, set_words, token, force, outp_dir)


if __name__ == '__main__':
	main()
