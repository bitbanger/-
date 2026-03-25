import ll
import os
import sys
import time

from argparse import ArgumentParser


def main():

	ap = ArgumentParser()
	ap.add_argument('set', nargs='+')
	ap.add_argument('-d', '--dir', default='new_scp_csvs')
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
	best_fn, best_set = min(sorted(top, key=ll.nth(1)), key=lambda e: len(e[1]))

	parallels = set()
	for row in ll.csv(best_fn):
		if (par:=ll.regf('\\[(.*)\\]')(row['product-name'])):
			parallels.add(par)
	parallels = sorted(list(parallels))

	print('')
	print(best_set)
	for p in parallels:
		print(f'\t[{p}]')
	print('')

	pass


if __name__ == '__main__':
	main()
