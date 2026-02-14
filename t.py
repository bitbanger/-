import ll
import sys


def parse_set(s):
	grade = ''
	if len(graspl:=s.split('*')) == 2:
		s, grade = s.split('*')

	var = ''
	if '[' in s:
		var = ll.regf('\[(.*)\]')(s)

	fset = s.split('[')[0].strip().replace('&', '').replace(' ', '_').lower()
	
	return fset, var, grade


def get_cards(sport, set, var, quants_by_num, whole=True):
	fns = [fn for fn in ll.ls(f'scp_csvs') if fn.endswith(f'{set.split("*")[0]}.csv') and ll.bn(fn).startswith(f'{sport}_')]
	if len(fns) == 0:
		ll.err(f"no csv file found for [grey70]{sport}[/grey70] set [grey70]{set}[/grey70]")
	assert(len(fns)==1)
	fn = fns[0]

	cards = []
	got = []

	for row in ll.csv('scp_csvs/' + fn):

		num = (rpn:=row['product-name']).split('#')[-1]

		if num in quants_by_num:

			# Check the variant
			row_var = ll.regf('\[(.*)\]')(rpn) or ''
			if var != row_var:
				continue

			# Add the quantity
			for _ in range(quants_by_num[num]):
				got.append(num)
				cards.append(row if whole else row['product-name'])

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
	return len(line) > 10 and not line.isnumeric()


def agg_quants_by_num_by_set(fn):
	quants_by_num_by_set = ll.dd(lambda: ll.dd(int))
	cur_set = ''
	cur_var = ''
	for line in ll.lines(fn):
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


def is_psa_10(grade):
	return grade.strip() == 'PSA 10'


def process(fn, console=True):
	fn_dir = ll.dn(fn)
	fn = ll.bn(fn)
	tfn = ll.ospj(fn_dir, fn)

	if len(spl:=fn.split('.')) != 2:
		ll.err(f"file [grey70]{fn_dir}/{fn}[/grey70] needs to end with a sport as its extension")

	sport = spl[1]

	quants_by_num_by_set = agg_quants_by_num_by_set(tfn)
	# TODO: this will clobber if duplicate filenames
	# exist in different dirs in the input
	with open(f'cards_{fn}', 'w+') as card_f:
		with open(f'prices_{fn}', 'w+') as price_f:
			gotten = 0

			for set, quants_by_num in quants_by_num_by_set.items():
				grade = ''
				if len(graspl:=set.split('*')) == 2:
					set, grade = set.split('*')

				# Get card info
				cur_fset, var, _ = parse_set(set)
				# card_row = get_card(sport, cur_fset, var, num)
				card_rows = get_cards(sport, cur_fset, var, quants_by_num)

				for card_row in card_rows:
					price_key = 'manual-only-price' if is_psa_10(grade) else 'loose-price'
					price = float(card_row[price_key][1:] or 0)

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

	if len(sys.argv) <= 1:
		ll.err(f'usage: t.py [grey70]input[/grey70]')

	fns = ll.dedupe(sys.argv[1:])

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
			for card in process(fn):
				yield card
	
	got = 0
	good_got = 0
	value = 0
	good_value = 0
	thresh = 4.00
	for (sport, year, set, name, num, var, price, grade) in ll.track(_track_it(), total=total):
		print_card(sport, year, set, name, num, var, price, grade)

		got += 1
		value += price
		if price >= 4:
			good_got += 1
			good_value += price

	print(f'\n{got} / {total}\n')
	print(f'${value:.02f}\n\t(${good_value:.02f} for {good_got} cards > ${thresh:.0f})\n')


if __name__ == '__main__':
	main()
