import ll
import os
import re as _re

from rich import print

from argparse import ArgumentParser
ap = ArgumentParser()
ap.add_argument('--sport')
ap.add_argument('--year')
ap.add_argument('--brand', default='panini')
ap.add_argument('words', nargs='+')
args = ap.parse_args()

sport = args.sport
year = args.year
brand = args.brand
set_words = [x.strip().lower() for x in args.words]
# sport = 'basketball'
# year = 2025
# brand = 'panini'
# set_words = ['donruss', 'wnba']


base_url = 'https://www.sportscardspro.com'
url = base_url + f'/brand/{sport}-cards/{brand}'
outp_dir = 'scp_csvs'

token = '73eddf931e1f5c18156c7481ba16266abbfb46a4'

def dl_url(uid):
	return f'https://www.sportscardspro.com/price-guide/download-custom?t={token}&console-uids={uid}'

re = _re.compile('console_uid = "(.*)"')
xs = []
while not xs:
	sp = ll.soup(url)
	xs.extend([x for x in sp.find_all('a', href=_re.compile(f'\/console\/{sport}-cards-{year}-{brand}')) if not x.text.startswith("'")])

xs = xs[::-1]
xs = [x for x in xs if all(w.lower() in x.text.lower() for w in set_words)]
xs = sorted(xs, key=lambda x: len(x.text))

print(f'{len(xs)} sets to download ([bold yellow3]{sport}[/bold yellow3]):')
for x in xs:
	print(f'\t{x.text}')
print('')

if not ll.yn(f'Download the above {len(xs)} [bold yellow3]{sport}[/bold yellow3] sets?'):
	quit(1)

# for x in ll.track(ll.soup(url).find_all('a', href=_re.compile(f'\/console\/{sport}-cards-{year}-{brand}')), total=total):
for x in ll.track(xs):
	set_name = x.text

	sub_url = base_url + x.attrs['href']


	set_code = ''
	for _ in range(15):
		try:
			subsoup = ll.soup(sub_url)
			uid = ll.regf('console_uid = "(.*)"')(subsoup(string=re)[0])

			scs = subsoup(string=_re.compile('Set Code.*'))
			try:
				set_code = scs[0].split(': ')[-1]
			except IndexError:
				pass

			break
		except IndexError:
			ll.sleep(1)
			continue

	while not uid:
		ll.sleep(1)
		subsoup = ll.soup(sub_url)
		uid = ll.regf('console_uid = "(.*)"')(subsoup(string=re)[0])

	csv_url = dl_url(uid)
	csv_name = ll.alphanums(set_name, also=' ').replace(' ', '_').lower() + '.csv'
	if set_code:
		csv_name = f'{set_code}_{csv_name}'
	csv_name = f'{sport}_{csv_name}'

	print(f'{csv_name}\n\t{csv_url}\n')

	with open(os.path.join(outp_dir, csv_name), 'w+') as f:
		csv = 'DOCTYPE'
		while 'DOCTYPE' in csv:
			print('.', end='')
			csv = ll.http(csv_url)
			ll.sleep(1)
		f.write(csv)

	# ll.write(ll.http(csv_url), '
