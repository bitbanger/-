import ll
import os
import re
import sys

from argparse import ArgumentParser


CSV_DIR = 'new_scp_csvs/'


def parse_set(s):
	grade = ''
	if len(graspl:=s.split('#')) == 2:
		s, grade = s.split('#')
		s = s.strip()
		grade = grade.strip()

	var = ''
	if '[' in s:
		var = ll.regf('\[(.*)\]')(s)

	# fset = s.split('[')[0].strip().replace('&', '').replace(' ', '_').lower()
	fset = s.split('[')[0].strip()
	fset = fset.replace('&', '') # special case for rookies & stars
	fset = ''.join([c for c in fset if c.lower() in 'abcdefghijklmnopqrstuvwxyz0123456789 '])
	fset = fset.replace(' ', '_')
	fset = fset.lower()
	
	return fset, var, grade


def get_cards(sport, set, var, quants_by_num, whole=True, warn=True):
	fns = [fn for fn in ll.ls(CSV_DIR, rel=False) if fn.endswith(f'{set.split("#")[0]}.csv') and ll.bn(fn).startswith(f'{sport}_')]
	if len(fns) == 0:
		ll.err(f"no csv file found for [grey70]{sport}[/grey70] set [grey70]{set}[/grey70]")
	if len(fns) > 1:
		print(f"[bold light_coral]error:[/bold light_coral] too many csv files found for [grey70]{sport}[/grey70] set [grey70]{set}[/grey70]:")
		for fn in fns:
			print(f"\t{fn}")
		os._exit(1)

	assert(len(fns)==1)
	fn = fns[0]

	cards = []
	got = []
	num2player = {}
	warned = ll.dd(lambda: bool)

	for row in cached_csv(CSV_DIR + fn):
		try:
			num = (rpn:=row['product-name']).split('#')[-1].strip()
		except:
			print(fn)
			print(row)
			quit()

		if num in quants_by_num:
			# Check the variant
			row_var = ll.regf('\[(.*)\]')(rpn) or ''
			if var != row_var:
				continue

			# Sadly, we have to do this because
			# of PJ-LMY being a DUPLICATE NUMBER
			# IN THE SAME FKN-SET
			# TODO: don't rely on getting lucky
			# with the one you want appearing first
			pname = row['product-name'].split('#')[0].split('[')[0].strip()
			if num in num2player and num2player[num] != pname and var == row_var:
				if warn and not warned[num]:
					print(f"\n\n\t[bold orange3]warning:[/bold orange3] number [grey70]{num}[/grey70] was already used for [grey70]{num2player[num]}[/grey70], so can't use it for [grey70]{pname}[/grey70]\n\n")
					warned[num] = True
				continue

			# Add the quantity
			for _ in range(quants_by_num[num]):
				got.append(num)
				cards.append(row if whole else row['product-name'])

			# Lock the player into the number :(
			num2player[num] = pname

	missed = 0
	for num in quants_by_num.keys():
		for copy in range(quants_by_num[num]):
			if num not in got:
				if var:
					ll.err(f'[bold red]missed:[/bold red] {set} #{num} [{var}]')
				else:
					ll.err(f'[bold red]missed:[/bold red] {set} #{num}')
				missed += 1
			got.remove(num)
	if missed > 0:
		quit(1)

	return cards


def is_set_name(line):
	# It's just a number
	if line.isnumeric():
		return False

	# Too short to be a set name
	if len(line) < 10:
		return False

	return True


def agg_quants_by_num_by_set(fn):
	quants_by_num_by_set = ll.dd(lambda: ll.dd(int))
	cur_set = ''
	cur_var = ''
	for line in ll.lines(fn):
		if line.strip().startswith('#'):
			line = line.strip()[1:].strip()

		if is_set_name(line):
			# It's a set
			# if (ms:=re.findall('(.*) ([0-9][0-9][0-9][0-9]) Topps (.*)', line)):
				# line = (m:=ms[0])[
				# print(ms)
				# quit()
			cur_set = line
		else:
			# It's a card
			if cur_set:
				quants_by_num_by_set[cur_set][line] += 1
			else:
				ll.err(f"file {fn} needs to at least start with a set name")

	return quants_by_num_by_set


csv_cache = {}
def cached_csv(*a, stream=False, **kw):
	if 'stream' in kw:
		stream = kw['stream']
	if stream:
		kw['stream'] = True
		return ll.csv(*a, **kw)

	key = ll.md5(' '.join([str(x) for x in a] + [f'({k}: {v})' for k, v in kw.items()]))
	global csv_cache
	if key not in csv_cache:
		csv_cache[key] = ll.csv(*a, **kw)

	return csv_cache[key]


def process(fn, console=True, warn=True, force_price_key=None):
	fn_dir = ll.dn(fn)
	fn = ll.bn(fn)
	tfn = ll.ospj(fn_dir, fn)

	outp_dir = 'outp'
	os.makedirs(outp_dir, exist_ok=True)
	cards_fn = ll.ospj(outp_dir, f'cards_{fn}')
	price_fn = ll.ospj(outp_dir, f'price_{fn}')

	if len(spl:=fn.split('.')) != 2:
		ll.err(f"file [grey70]{fn_dir}/{fn}[/grey70] needs to end with a sport as its extension")

	sport = spl[1]

	quants_by_num_by_set = agg_quants_by_num_by_set(tfn)
	with open(cards_fn, 'w+') as card_f:
		with open(price_fn, 'w+') as price_f:
			gotten = 0

			for set, quants_by_num in quants_by_num_by_set.items():
				orig_set = set[::]

				def _procset(set):
					grade = ''
					if len(graspl:=set.split('#')) == 2:
						set, grade = set.split('#')
						set = set.strip()
						grade = grade.strip()

					# Get card info
					cur_fset, var, _ = parse_set(set)
					
					return set, grade, cur_fset, var

				set, grade, cur_fset, var = _procset(set)
				# card_row = get_card(sport, cur_fset, var, num)
				card_rows = get_cards(sport, cur_fset, var, quants_by_num, warn=warn)

				# Correct weird Topps formatting before rendering output, but
				# after looking up the set file
				for ender in ('Topps', 'Donruss', 'Upper Deck'):
					if (ms:=re.findall(f'(.*) ([0-9][0-9][0-9][0-9]) {ender} (.*)', orig_set)):
						_, year, stn = ms[0]
						set, grade, cur_fset, var = _procset(f'{year} {ender} {stn}')

				for card_row in card_rows:
					if force_price_key:
						price_key = force_price_key
					else:
						match grade.strip().lower().replace(' ', '_'):
							case 'psa_10':
								price_key = 'manual-only-price'
							case 'damaged':
								price_key = "damaged (this key won't be in the dict)"
							case _:
								price_key = 'loose-price'

					price = card_row.get(price_key)
					price = float(price[1:]) if price else 0.0

					_pr = lambda p: float(p[1:]) if p else 0
					psa_10 = _pr(card_row.get('manual-only-price'))
					cgc_10 = _pr(card_row.get('condition-17-price'))
					psa_9 = _pr(card_row.get('graded-price'))

					if force_price_key == 'manual-only-price':
						price = max(0, price-32)


					# Console output
					name = card_row['product-name'].split('#')[0].split(' [')[0].strip()
					num = card_row['product-name'].split('#')[1].split(' [')[0].strip()
					if '[' in card_row['product-name']:
						var = card_row['product-name'].split('[')[-1].split(']')[0].strip()
					else:
						var = ''
					unvar_set = set.split(' [')[0].strip()
					year = unvar_set.split(' ')[0].strip()
					unyear_set = ' '.join(unvar_set.split(' ')[1:]).strip()

					# print(sport)
					# print(year)
					# print(unyear_set)
					# print(name)
					# print(num)
					# print(var)
					# quit()

					# File output
					cid = card_row['id']
					if cid == 'fake_id':
						cid = 'fake_id_' + ll.md5(f'{sport} {year} {unyear_set} {name} {num} {var}')
					card_tup = (card_row['id'], sport, year, unyear_set, name, num, var, price, grade, psa_10, cgc_10, psa_9)

					# Find any price overrides
					with open('/tmp/overrides_price.csv', 'w+') as tmpf:
						for line in ll.lines('overrides_price.csv'):
							if not line.startswith('#'):
								tmpf.write(line+'\n')
						
					for trow in ll.csv('/tmp/overrides_price.csv', dicts=False):
						# to ID in override csv, which parallels col.csv
						brand, unbranded_set = split_brand(unyear_set)
						card_tup2 = card_tup[:3] + (brand, unbranded_set) + card_tup[4:]
						_id = lambda r: ' '.join(ll.map(str, list(r[1:8])+[r[9]]))
						if _id(card_tup2) == _id(trow):
							# We found a match in the overrides file,
							# so we'll take the prices there
							card_tup = list(card_tup) # mutable
							for __i in (7, 9, 10, 11):
								if trow[__i+1] != '':
									card_tup[__i] = type(card_tup[__i])(trow[__i+1])
							card_tup = tuple(card_tup)

					os.remove('/tmp/overrides_price.csv')

					yield card_tup

					if var:
						card_str = f'{name} #{num} [{var}] {unvar_set}'
					else:
						card_str = f'{name} #{num} {unvar_set}'
					if grade:
						card_str += f' ({grade})'

					card_f.write(f'{card_str}\n')
					price_f.write(f'{price:.02f}\t{card_str}\n')

					gotten += 1


def print_card(id, sport, year, set, name, num, var, price, grade, psa_10, cgc_10, psa_9, price_threshold):
	if var:
		card_str = f'{name} #{num} [{var}] {year} {set}'
	else:
		card_str = f'{name} #{num} {year} {set}'

	if grade:
		card_str += f' ({grade})'

	if price >= price_threshold:
		print(f'[yellow3]{price:.02f}[/yellow3]\t{card_str}')
	elif price >= 1:
		print(f'[grey50]{price:.02f}[/grey50]\t{card_str}')
	elif price == 0:
		print(f'[grey50]-[/grey50]\t{card_str}')
	else:
		print(f'[grey30]{price:.02f}[/grey30]\t{card_str}')

def split_brand(set_name):
	# TODO: better brand ID
	if 'topps' in set_name.lower():
		brand_name = 'Topps'
	elif 'bowman chrome' in set_name.lower():
		brand_name = 'Bowman Chrome'
	elif 'panini' in set_name.lower():
		brand_name = 'Panini'
	elif 'leaf' in set_name.lower():
		brand_name = 'Leaf'
	elif set_name.lower() == 'donruss':
		brand_name = 'Donruss'
	elif set_name.lower() == 'upper deck':
		brand_name = 'Upper Deck'
	else:
		raise Exception(f"unknown brand_name for set_name {set_name}")

	set_name = set_name[:set_name.lower().index(brand_name.lower())].strip() + set_name[set_name.lower().index(brand_name.lower())+len(brand_name)+len(' '):].strip()

	return brand_name, set_name


def card_row(id, sport, year, set, name, num, var, price, grade, psa10, cgc10, psa9):
	brand, set = split_brand(set)

	return cached_csv((id, sport, year, brand, set, name, num, var, price, grade, psa10, cgc10, psa9))
fcard_row = card_row


def card_csv(cards):
	headers = cached_csv(('scp_id', 'sport', 'year', 'brand', 'set', 'name', 'number', 'parallel', 'price', 'condition', 'psa_10', 'cgc_10', 'psa_9'))
	yield headers

	for crow in cards:
		(id, sport, year, set, name, num, var, price, grade, psa10, cgc10, psa9) = crow

		# set = set[:set.lower().index(brand.lower())].strip() + set[set.lower().index(brand.lower())+len(brand)+len(' '):].strip()

		yield card_row(id, sport, year, set, name, num, var, price, grade, psa10, cgc10, psa9)


def main():

	ap = ArgumentParser(add_help=False)
	ap.add_argument('input', nargs='+')
	ap.add_argument('-q', '--quiet-warnings', action='store_true')
	ap.add_argument('-p', '--price-threshold', type=float, default=10.00)
	ap.add_argument('-h', '--hide-cheap', action='store_true')
	ap.add_argument('-s', '--sort-by-price', action='store_true')
	ap.add_argument('-n', '--no-progress', action='store_true')
	ap.add_argument('-g', '--grade-10', action='store_true')
	args = ap.parse_args()

	pre_fns = ll.dedupe(args.input)
	if (fakes:=[fn for fn in pre_fns if not ll.fexists(fn)]):
		lump = '\n\t' + '\n\t'.join(fakes)
		ll.err(f"the following file(s) were not found:[grey70]{lump}[/grey70]")

	fns = []
	for fn in pre_fns:
		if ll.isdir(fn):
			fns.extend(ll.ls(fn, rel=True))
		else:
			fns.append(fn)

	bn2dupes = ll.dd()
	for i, fn1 in enumerate(fns):
		for j, fn2 in enumerate(fns):
			if i <= j:
				continue
			if ll.bn(fn1) != ll.bn(fn2):
				continue
			bn = ll.bn(fn1)
			if fn1 not in bn2dupes[bn]:
				bn2dupes[bn].append(fn1)
			if fn2 not in bn2dupes[bn]:
				bn2dupes[bn].append(fn2)
	if bn2dupes:
		lump = ''
		for i, (bn, dupes) in enumerate(bn2dupes.items()):
			if i > 0:
				lump += '\n' # Extra spacing
			for dupe in dupes:
				lump += f'\n\t{dupe}'

		ll.err(f"the following file(s) have the same names & will clobber each other: [grey70]{lump}[/grey70]")


	total = 0
	for fn in fns:
		for line in ll.lines(fn, stream=True):
			if line.strip() and not is_set_name(line):
				total += 1

	def _track_it():
		for fn in fns:
			for card in process(fn, warn=(not args.quiet_warnings), force_price_key=('manual-only-price' if args.grade_10 else None)):
				yield card
	
	got = 0
	good_got = 0
	value = 0
	good_value = 0
	unknown_got = 0
	cards = []

	_it = _track_it()
	if not args.no_progress:
		_it = ll.track(_it, total=total)
	
	# print(cached_csv(('sport', 'year', 'brand', 'set', 'name', 'number', 'parallel', 'price', 'condition')))
	for card in _it:
		id, sport, year, set, name, num, var, price, grade, psa_10, cgc_10, psa_9 = card
		# print(card_row(*card))
		cards.append(card)
		if (not args.hide_cheap) or (price >= args.price_threshold):
			if not args.sort_by_price:
				print_card(*cards[-1], price_threshold=args.price_threshold)

		got += 1
		value += price
		if price >= args.price_threshold:
			good_got += 1
			good_value += price
		elif price == 0:
			unknown_got += 1

	if args.sort_by_price:
		cards = sorted(cards, key=ll.nth(6))
		for card in cards:
			_,_,_,_,_,_,_,price,_,_,_,_ = card
			if (not args.hide_cheap) or (price >= args.price_threshold):
				print_card(*card, price_threshold=args.price_threshold if args.hide_cheap else 0.00)


	# ll.rule()
	# sc = sorted(cards, key=lambda c: (c[2], c[5], c[4]))
	# for c in sc:
		# print_card(*c, price_threshold=args.price_threshold if args.hide_cheap else 0.00)


	with open('col.csv', 'w+') as f:
		for crow in card_csv(cards):
			f.write(crow + '\n')


	print(f'\n{got} / {total}\n')
	print(f'${value:.02f}\n\t(${good_value:.02f} for {good_got} cards > ${args.price_threshold:.0f})\n')
	print(f'\t[grey70]([/grey70]{unknown_got}[grey70] cards w/ no mkt. data)[/grey70]\n')


if __name__ == '__main__':
	main()
