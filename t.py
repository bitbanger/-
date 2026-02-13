import ll
import sys


def parse_set(s):
	var = ''
	if '[' in s:
		var = ll.regf('\[(.*)\]')(s)

	fset = s.split('[')[0].strip().replace('&', '').replace(' ', '_').lower()
	
	return fset, var


def get_cards(sport, set, var, quants_by_num, whole=True):
	fns = [fn for fn in ll.ls(f'scp_csvs') if fn.endswith(f'{set}.csv') and ll.bn(fn).startswith(f'{sport}_')]
	assert(len(fns)==1)
	fn = fns[0]

	cards = []
	got = __builtins__.set()

	for row in ll.csv('scp_csvs/' + fn):

		num = (rpn:=row['product-name']).split('#')[-1]

		if num in quants_by_num:
			got.add(num)

			# Check the variant
			row_var = ll.regf('\[(.*)\]')(rpn) or ''
			if var != row_var:
				continue

			# Add the quantity
			for _ in range(quants_by_num[num]):
				cards.append(row if whole else row['product-name'])

	missed = 0
	for num in quants_by_num.keys():
		if num not in got:
			print(f'[bold red]missed:[/bold red] {set} #{num}')
			missed += 1
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


def process(fn):
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

			# Iterator that writes the cards
			def _track_it():
				for set, quants_by_num in quants_by_num_by_set.items():
					# Get card info
					cur_fset, var = parse_set(set)
					# card_row = get_card(sport, cur_fset, var, num)
					card_rows = get_cards(sport, cur_fset, var, quants_by_num)

					for card_row in card_rows:
						price = float(card_row['loose-price'][1:] or 0)

						# Console output
						if price >= 4.00:
							print(f'[yellow3]{price:.02f}[/yellow3]\t{card_row["product-name"]} {set}')
						elif price >= 1:
							print(f'[grey50]{price:.02f}[/grey50]\t{card_row["product-name"]} {set}')
						elif price == 0:
							print(f'[grey50]-[/grey50]\t{card_row["product-name"]} {set}')
						else:
							print(f'[grey30]{price:.02f}[/grey30]\t{card_row["product-name"]} {set}')

						# File output
						card_f.write(f'{card_row["product-name"]} {set}\n')
						price_f.write(f'{price:.02f}\t{card_row["product-name"]} {set}\n')

						# Tick the progress bar
						yield

			# Dummy tracker for the iterator
			# list(ll.track(_track_it(), total=sum([len(nums) for nums in quants_by_num_by_set.values()])))
			list(_track_it())


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
			if not is_set_name(line):
				total += 1

	for fn in ll.track(fns, total=total):
		process(fn)


if __name__ == '__main__':
	main()

'''
	ll.import_from(ll.here('scp.py'), 'price')


	def safe_price(*a, **kw):
		try:
			return price(*a, **kw)
		except Exception as e:
			return 0.0


	def get_card(sport, s, v, n, whole=True):
		fns = [fn for fn in ll.ls(f'scp_csvs') if fn.endswith(f'{s}.csv') and ll.bn(fn).startswith(f'{sport}_')]
		assert(len(fns)==1)
		for row in ll.csv('scp_csvs/' + fns[0]):
			if (rpn:=row['product-name']).endswith(f'#{n}'):
				row_var = ll.regf('\[(.*)\]')(rpn) or ''
				if v != row_var:
					continue
				return row if whole else row['product-name']

	set2cards = ll.dd()
	cur_set, cur_fset, var = '', '', ''


	def main():
		with open(f'cards_{fn}', 'w+') as card_f:
			with open(f'prices_{fn}', 'w+') as price_f:
				gotten = 0
				for line in ll.track(ll.lines(fn)):

					if len(line) > 10 and not line.isnumeric():
						# It's a set
						cur_set = line
						cur_fset, var = parse_set(cur_set)
						cur_set = line.split(' [')[0]

					else:
						if not cur_set:
							ll.err(f"file {fn} needs to at least start with a set name")

						card = get_card(sport, cur_fset, var, line)
						# card_price = safe_price(card['id'])
						card_price = float(card['loose-price'][1:] or 0)

						if card_price >= 3.50:
							print(f'[green]{card_price:.02f}[/green]\t{card["product-name"]} {cur_set}')
						elif card_price == 0:
							print(f'{card_price:.02f}\t{card["product-name"]} {cur_set}')
						else:
							print(f'[grey30]{card_price:.02f}[/grey30]\t{card["product-name"]} {cur_set}')

						card_f.write(f'{card["product-name"]} {cur_set}\n')
						price_f.write(f'{card_price:.02f}\t{card["product-name"]} {cur_set}\n')

						gotten += 1
'''
