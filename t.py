import ll
import os
import sys

from argparse import ArgumentParser


def parse_set(s):
	grade = ''
	if len(graspl:=s.split('#')) == 2:
		s, grade = s.split('#')
		s = s.strip()
		grade = grade.strip()

	var = ''
	if '[' in s:
		var = ll.regf('\[(.*)\]')(s)

	fset = s.split('[')[0].strip().replace('&', '').replace(' ', '_').lower()
	
	return fset, var, grade


def get_cards(sport, set, var, quants_by_num, whole=True, warn=True):
	fns = [fn for fn in ll.ls(f'scp_csvs') if fn.endswith(f'{set.split("#")[0]}.csv') and ll.bn(fn).startswith(f'{sport}_')]
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

	for row in ll.csv('scp_csvs/' + fn):

		num = (rpn:=row['product-name']).split('#')[-1].strip()

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
			cur_set = line
		else:
			# It's a card
			if cur_set:
				quants_by_num_by_set[cur_set][line] += 1
			else:
				ll.err(f"file {fn} needs to at least start with a set name")

	return quants_by_num_by_set


def process(fn, console=True, warn=True):
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
				grade = ''
				if len(graspl:=set.split('#')) == 2:
					set, grade = set.split('#')
					set = set.strip()
					grade = grade.strip()

				# Get card info
				cur_fset, var, _ = parse_set(set)
				# card_row = get_card(sport, cur_fset, var, num)
				card_rows = get_cards(sport, cur_fset, var, quants_by_num, warn=warn)

				for card_row in card_rows:
					match grade.strip().lower().replace(' ', '_'):
						case 'psa_10':
							price_key = 'manual-only-price'
						case 'damaged':
							price_key = "damaged (this key won't be in the dict)"
						case _:
							price_key = 'loose-price'

					price = card_row.get(price_key)
					price = float(price[1:]) if price else 0.0

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

					# File output
					card_tup = (sport, year, unyear_set, name, num, var, price, grade)
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


def print_card(sport, year, set, name, num, var, price, grade):
	if var:
		card_str = f'{name} #{num} [{var}] {year} {set}'
	else:
		card_str = f'{name} #{num} {year} {set}'

	if grade:
		card_str += f' ({grade})'

	if price >= 4.00:
		print(f'[yellow3]{price:.02f}[/yellow3]\t{card_str}')
	elif price >= 1:
		print(f'[grey50]{price:.02f}[/grey50]\t{card_str}')
	elif price == 0:
		print(f'[grey50]-[/grey50]\t{card_str}')
	else:
		print(f'[grey30]{price:.02f}[/grey30]\t{card_str}')


def main():

	ap = ArgumentParser()
	ap.add_argument('input', nargs='+')
	ap.add_argument('-q', '--quiet-warnings', action='store_true')
	ap.add_argument('-p', '--price-threshold', type=float, default=0.0)
	ap.add_argument('-s', '--sort-by-price', action='store_true')
	args = ap.parse_args()

	fns = ll.dedupe(args.input)

	if (fakes:=[fn for fn in fns if not ll.fexists(fn)]):
		lump = '\n\t' + '\n\t'.join(fakes)
		ll.err(f"the following file(s) were not found:[grey70]{lump}[/grey70]")

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
			for card in process(fn, warn=(not args.quiet_warnings)):
				yield card
	
	got = 0
	good_got = 0
	value = 0
	good_value = 0
	unknown_got = 0
	cards = []
	for card in ll.track(_track_it(), total=total):
		sport, year, set, name, num, var, price, grade = card
		cards.append(card)
		if price >= args.price_threshold:
			if not args.sort_by_price:
				print_card(*cards[-1])

		got += 1
		value += price
		if price >= 4:
			good_got += 1
			good_value += price
		elif price == 0:
			unknown_got += 1

	if args.sort_by_price:
		cards = sorted(cards, key=ll.nth(6))
		for card in cards:
			print_card(*card)

	print(f'\n{got} / {total}\n')
	print(f'${value:.02f}\n\t(${good_value:.02f} for {good_got} cards > ${args.price_threshold:.0f})\n')
	print(f'\t[grey70]([/grey70]{unknown_got}[grey70] cards w/ no mkt. data)[/grey70]\n')


if __name__ == '__main__':
	main()
