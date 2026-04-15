import ll
import os
import re
import sys

from argparse import ArgumentParser


CSV_DIRS = ('new_scp_csvs/', 'fake_scp_csvs/')


def maybe_print(args, *a, **kw):
	if args.quiet:
		return
	return print(*a, **kw)


def parse_set(args, s):
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


def get_cards(args, sport, set, var, quants_by_num, whole=True, warn=True):
	fns = []
	for CSV_DIR in CSV_DIRS:
		fns.extend([fn for fn in ll.ls(CSV_DIR, abs=True) if fn.endswith(f'{set.split("#")[0]}.csv') and ll.bn(fn).startswith(f'{sport}_')])
	if len(fns) == 0:
		ll.err(f"no csv file found for [grey70]{sport}[/grey70] set [grey70]{set}[/grey70]")
	if len(fns) > 1:
		maybe_print(args, (f"[bold light_coral]error:[/bold light_coral] too many csv files found for [grey70]{sport}[/grey70] set [grey70]{set}[/grey70]:"))
		for fn in fns:
			maybe_print(args, (f"\t{fn}"))
		os._exit(1)

	assert(len(fns)==1)
	fn = fns[0]

	cards = []
	got = []
	num2player = {}
	warned = ll.dd(lambda: bool)

	# for row in cached_csv(args, CSV_DIR + fn):
	for row in cached_csv(args, fn):
		try:
			num = (rpn:=row['product-name']).split('#')[-1].strip()
		except:
			maybe_print(args, (fn))
			maybe_print(args, (row))
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
					maybe_print(args, (f"\n\n\t[bold orange3]warning:[/bold orange3] number [grey70]{num}[/grey70] was already used for [grey70]{num2player[num]}[/grey70], so can't use it for [grey70]{pname}[/grey70]\n\n"))
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


def is_set_name(args, line):
	# It's just a number
	if line.isnumeric():
		return False

	# Too short to be a set name
	if len(line) < 10:
		return False

	return True


def agg_quants_by_num_by_set(args, fn):
	quants_by_num_by_set = ll.dd(lambda: ll.dd(int))
	cur_set = ''
	cur_var = ''
	for line in ll.lines(fn):
		if line.strip().startswith('#'):
			line = line.strip()[1:].strip()

		if is_set_name(args, line):
			# It's a set
			# if (ms:=re.findall('(.*) ([0-9][0-9][0-9][0-9]) Topps (.*)', line)):
				# line = (m:=ms[0])[
				# maybe_print(args, (ms))
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
def cached_csv(args, *a, stream=False, **kw):
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


def process(args, fn, console=True, warn=True, force_price_key=None):
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

	quants_by_num_by_set = agg_quants_by_num_by_set(args, tfn)
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
						force_price_key = ''

					# Get card info
					cur_fset, var, _ = parse_set(args, set)
					
					return set, grade, cur_fset, var

				set, grade, cur_fset, var = _procset(set)
				# card_row = get_card(sport, cur_fset, var, num)
				card_rows = get_cards(args, sport, cur_fset, var, quants_by_num, warn=warn)

				# Correct weird Topps formatting before rendering output, but
				# after looking up the set file
				for ender in ('Topps', 'Donruss', 'Upper Deck', 'Finger Lakes Gaming'):
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
							case 'psa_9':
								price_key = 'graded-price'
							case 'damaged':
								price_key = "damaged (this key won't be in the dict)"
							case _:
								price_key = 'loose-price'

					price = card_row.get(price_key)
					price = float(price[1:]) if price else 0.0

					_pr = lambda p: float(p[1:]) if p else 0
					psa_10, cgc_10, psa_9 = 0,0,0
					if card_row.get('sales-volume') and int(card_row['sales-volume']) > 0:
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

					# maybe_print(args, (sport))
					# maybe_print(args, (year))
					# maybe_print(args, (unyear_set))
					# maybe_print(args, (name))
					# maybe_print(args, (num))
					# maybe_print(args, (var))
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
						brand, unbranded_set = split_brand(args, year, unyear_set)
						card_tup2 = card_tup[:3] + (brand, unbranded_set) + card_tup[4:]
						_id = lambda r: ' '.join(ll.map(str, list(r[1:8])+[r[9]]))
						if _id(card_tup2) == _id(trow):
							# Don't do anything if the override file
							# specifies a condition and this condition
							# doesn't match
							if trow[-4] and trow[-4] != card_tup[-4]:
								continue
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


def maybe_print_card(args, id, sport, year, set, name, num, var, price, grade, psa_10, cgc_10, psa_9, price_threshold):
	if var:
		card_str = f'{name} #{num} [{var}] {year} {set}'
	else:
		card_str = f'{name} #{num} {year} {set}'

	if grade:
		card_str += f' ({grade})'

	if price >= price_threshold:
		maybe_print(args, (f'[yellow3]{price:.02f}[/yellow3]\t{card_str}'))
	elif price >= 1:
		maybe_print(args, (f'[grey50]{price:.02f}[/grey50]\t{card_str}'))
	elif price == 0:
		maybe_print(args, (f'[grey50]-[/grey50]\t{card_str}'))
	else:
		maybe_print(args, (f'[grey30]{price:.02f}[/grey30]\t{card_str}'))

def split_brand(args, year, set_name):
	year = int(year)
	sn = set_name.lower()

	# TODO: better brand ID
	if 'topps' in sn:
		brand_name = 'Topps'
	elif 'bowman chrome' in sn:
		brand_name = 'Bowman Chrome'
	elif 'bowman' in sn:
		brand_name = 'Bowman'
	elif 'panini' in sn:
		if 'donruss' in sn and year<2009:
			brand_name = 'Donruss'
		else:
			brand_name = 'Panini'
	elif 'leaf' in sn:
		brand_name = 'Leaf'
	elif 'rittenhouse' in sn:
		brand_name = 'Rittenhouse'
	elif sn == 'donruss':
		brand_name = 'Donruss'
	elif sn.startswith('donruss '):
		brand_name = 'Donruss'
	elif sn.startswith('upper deck'):
		brand_name = 'Upper Deck'
	elif sn.startswith('sage'):
		brand_name = 'Sage'
	elif sn.startswith('fleer'):
		brand_name = 'Fleer'
	elif sn.startswith('hostess'):
		brand_name = 'Hostess'
	elif sn.startswith('kraft singles'):
		brand_name = 'Kraft Singles'
	elif sn.startswith('score'):
		brand_name = 'Score'
	elif sn.startswith('score '):
		brand_name = 'Score'
	elif 'finger lakes gaming' in sn:
		brand_name = 'Finger Lakes Gaming'
	else:
		maybe_print(args, (sn))
		raise Exception(f"unknown brand_name for set_name {set_name}")

	set_name = set_name[:set_name.lower().index(brand_name.lower())].strip() + set_name[set_name.lower().index(brand_name.lower())+len(brand_name)+len(' '):].strip()

	return brand_name, set_name


def card_row(args, id, sport, year, set, name, num, var, price, grade, psa10, cgc10, psa9):
	brand, set = split_brand(args, year, set)

	return cached_csv(args, (id, sport, year, brand, set, name, num, var, price, grade, psa10, cgc10, psa9))
fcard_row = card_row


def card_csv(args, cards):
	headers = cached_csv(args, ('scp_id', 'sport', 'year', 'brand', 'set', 'name', 'number', 'parallel', 'price', 'condition', 'psa_10', 'cgc_10', 'psa_9'))
	yield headers

	for crow in cards:
		(id, sport, year, set, name, num, var, price, grade, psa10, cgc10, psa9) = crow

		# set = set[:set.lower().index(brand.lower())].strip() + set[set.lower().index(brand.lower())+len(brand)+len(' '):].strip()

		yield card_row(args, id, sport, year, set, name, num, var, price, grade, psa10, cgc10, psa9)


def main():

	ap = ArgumentParser(add_help=False)
	ap.add_argument('input', nargs='+')
	ap.add_argument('-w', '--quiet-warnings', action='store_true')
	ap.add_argument('-q', '--quiet', action='store_true')
	ap.add_argument('-p', '--price-threshold', type=float, default=8.00)
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
			if line.strip() and not is_set_name(args, line):
				total += 1

	def _track_it():
		for fn in fns:
			for card in process(args, fn, warn=(not args.quiet_warnings), force_price_key=('manual-only-price' if args.grade_10 else None)):
				yield card
	
	got = 0
	good_got = 0
	value = 0
	good_value = 0
	unknown_got = 0
	cards = []

	_it = _track_it()
	if not args.no_progress:
		_it = ll.track(_it, total=total, title='t.py: ')
	
	# maybe_print(args, (cached_csv(args, ('sport', 'year', 'brand', 'set', 'name', 'number', 'parallel', 'price', 'condition')))
	for card in _it:
		id, sport, year, set, name, num, var, price, grade, psa_10, cgc_10, psa_9 = card
		# maybe_print(args, (card_row(args, *card))
		cards.append(card)
		if (not args.hide_cheap) or (price >= args.price_threshold):
			if not args.sort_by_price:
				maybe_print_card(args, *cards[-1], price_threshold=args.price_threshold)

		got += 1
		value += price
		if price >= args.price_threshold:
			good_got += 1
			good_value += price
		elif price == 0:
			unknown_got += 1

	if args.sort_by_price:
		cards = sorted(cards, key=ll.nth(7))
		for card in cards:
			_,_,_,_,_,_,_,price,_,_,_,_ = card
			if (not args.hide_cheap) or (price >= args.price_threshold):
				maybe_print_card(args, *card, price_threshold=args.price_threshold if args.hide_cheap else 0.00)


	# ll.rule()
	# sc = sorted(cards, key=lambda c: (c[2], c[5], c[4]))
	# for c in sc:
		# maybe_print(args, *c, price_threshold=args.price_threshold if args.hide_cheap else 0.00)


	with open('col.csv', 'w+') as f:
		for crow in card_csv(args, cards):
			f.write(crow + '\n')


	maybe_print(args, f'\n{got} / {total}\n')
	maybe_print(args, f'${value:.02f}\n\t(${good_value:.02f} for {good_got} cards > ${args.price_threshold:.0f})\n')
	maybe_print(args, f'\t[grey70]([/grey70]{unknown_got}[grey70] cards w/ no mkt. data)[/grey70]\n')


if __name__ == '__main__':
	main()
