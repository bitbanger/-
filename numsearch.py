import ll
import os
import sys
import time

from argparse import ArgumentParser


def main():

	ap = ArgumentParser()
	ap.add_argument('-s', '--set', required=True, nargs='+')
	ap.add_argument('-n', '--name', required=True, nargs='+')
	ap.add_argument('-d', '--dir', default='new_scp_csvs')
	args = ap.parse_args()

	args.set = ' '.join(args.set)
	args.name = ' '.join(args.name)

	args.set = args.set.replace('and', '')
	args.set = args.set.replace('&', '')

	sets = []
	for fn in ll.ls(args.dir, abs=True):
		if not fn.endswith('.csv'):
			continue
		if (ln:=len(ll.lines(fn)))<=1:
			s = 's'*bool(ln)
			ll.err(f'{fn} is {ln} line{s}!')

		try:
			sets.append((fn, next(ll.csv(fn, stream=True))['console-name']))
		except:
			print(ll.lines(fn))
			quit()

	matches = {s: ll.words_in(args.set, s[1]) for s in sets}
	top = [s for s, sc in matches.items() if sc==max(matches.values())]
	year = lambda s: int(ll.regf('[0-9]'*4)(s) or '0')
	top = [x for x in top if year(x[1])==max([year(s[1]) for s in top])]
	best_fn, best_set = min(top, key=lambda e: len(e[1]))

	row2sc = {row['product-name']: ll.words_in(args.name, row['product-name']) for row in ll.csv(best_fn)}
	row2sc = {k: v for k, v in row2sc.items() if v==max(row2sc.values())}
	print('')
	print(best_set, end='\n\n')
	for k in row2sc:
		print(f'\t{k}')
	print('')

	pass


if __name__ == '__main__':
	main()
