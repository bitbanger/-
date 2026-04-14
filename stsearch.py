import ll
import os
import sys
import time

from argparse import ArgumentParser


def main():

	ap = ArgumentParser()
	ap.add_argument('set', nargs='+')
	ap.add_argument('-d', '--dir', default='new_scp_csvs')
	ap.add_argument('-m', '--minimal', action='store_true')
	ap.add_argument('-p', '--parallels', action='store_true')
	args = ap.parse_args()

	args.set = ' '.join(args.set)
	args.set = args.set.replace('and', '')
	args.set = args.set.replace('&', '')

	sets = [(fn, next(ll.csv(fn, stream=True))['console-name'])
		for fn in ll.ls(args.dir, abs=True) if fn.endswith('.csv')]

	matches = {s: ll.words_in(args.set, s[1]) for s in sets}
	top = [s for s, sc in matches.items() if sc==max(matches.values())]
	year = lambda s: int(ll.regf('[0-9]'*4)(s) or '0')
	top = [x for x in top if year(x[1])==max([year(s[1]) for s in top])]
	top = sorted(top, key=ll.nth(1))
	best_fn, best_set = min(top, key=lambda e: len(e[1]))

	if args.minimal:
		top = [(best_fn, best_set)]

	hier = ll.json(ll.read('hierarchy_of_sports_sets.json'))
	print('')
	for i, (c_fn, c_set) in enumerate(top):
		if i>0:
			print('')

		spl = c_set.split(' Cards ')
		sport = spl[0]
		c_set = spl[1].replace('&', 'and')
		c_subsets = set()

		for _set in hier[sport]:
			# if c_set == _set:
			if c_set.startswith(_set):
				c_set, c_subset = _set, c_set[len(_set):]
				break

		print(f'[green]{c_set}[/green][blue]{c_subset}[/blue]')

		for row in ll.csv(c_fn, stream=True):
			num_scheme = row['product-name'].split('#')[-1].split(' ')[0]
			print(f'\t[grey70](numbers like [steel_blue]{num_scheme}[/steel_blue])[/grey70]')
			break

		if args.parallels:
			parallels = set()
			for row in ll.csv(c_fn, stream=True):
				if (par:=ll.regf('\\[(.*)\\]')(row['product-name'])):
					parallels.add(par)
			parallels = sorted(list(parallels))

			for p in parallels:
				print(f'\t[{p}]')

	print('')

	pass


if __name__ == '__main__':
	main()
