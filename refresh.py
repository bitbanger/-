import argparse
import ll
import os

ll.import_from(ll.here('dl_scp.py'), 'get_sets')
ll.import_from(ll.here('dl_scp.py'), 'download_sets')
ll.import_from(ll.here('dl_scp.py'), 'verify_sets')
# ll.import_from(ll.here('dl_scp.py'), 'coordinate')


def main():

	ap = argparse.ArgumentParser()
	ap.add_argument('set', nargs='*')
	ap.add_argument('-m', '--minimal', action='store_true')
	args = ap.parse_args()

	args.set = ' '.join(args.set)
	args.set = args.set.replace('and', '')
	args.set = args.set.replace('&', '')

	set_names = set()
	for fn in ll.ls('remake', abs=True):
		sport = fn.split('.')[-1]
		for line in ll.lines(fn):
			if ' ' in line:
				line = sport + ' ' + line.split('#')[0].split('[')[0].strip()
				line = line.lower()
				line = line.replace('& ', '')
				line = line.replace('!', '')
				if line not in set_names:
					set_names.add(line)
	set_names = sorted(list(set_names))

	if args.set:
		matches = {s: ll.words_in(args.set, s) for s in set_names}
		top = [s for s, sc in matches.items() if sc==max(matches.values())]
		year = lambda s: int(ll.regf('[0-9]'*4)(s) or '0')
		top = [x for x in top if year(x)==max([year(s) for s in top])]
		top = sorted(top)
		if args.minimal:
			set_names = [min(sorted(top), key=len)]
		else:
			set_names = top

	'''
	set_names = []
	for fn in ll.ls('scp_csvs', abs=True):
		if not fn.endswith('.csv'):
			continue

		dn = ll.dn(fn)
		bn = ll.bn(fn)

		set_name = bn[:-len('.csv')].replace('__', '_').replace('_', ' ')
		set_names.append(set_name)
	'''

	'''
	prefixes = set()
	longers = set()
	for i, sn1 in enumerate(set_names):
		for j, sn2 in enumerate(set_names):
			if i == j:
				continue
			if (len(sn1.split(' ')) > 1) and (sn2.startswith(sn1)):
				prefixes.add(sn1)
				longers.add(sn2)

	prefixes = prefixes-longers

	files_to_get = prefixes#+longers
	files_to_get = prefixes.union(longers)
	'''
	files_to_get = set_names

	# sets_to_dl = []
	sets_to_dl = ll.dd(list)
	missed = []
	for p in ll.track(files_to_get, title='Getting set names: '):
		sport = p.strip().split(' ')[0]
		orig_p = p[::]
		p = ' '.join(p.strip().split(' ')[1:])

		year = ll.regf('([0-9][0-9][0-9][0-9])')(p)
		if year is None:
			print(orig_p)
			quit()
		spl = [x for x in p[p.index(year):].strip().split(' ')[1:]]
		brand = spl[0]
		words = spl[1:]

		_sets = get_sets(sport, year, brand, words)
		# sets_to_dl[sport].extend()
		if len(_sets) > 0:
			sets_to_dl[sport].append(min(_sets, key=lambda t: len(t[0])))
		else:
			missed.append(p)

	print('')
	for sport, sets in sorted(sets_to_dl.items(), key=ll.nth(0)):
		print(sport)
		for _set in sorted(sets, key=ll.nth(0)):
			print(f'\t{_set[0]}')


	# Check which sets we couldn't find, so can't update
	'''
	total = set()
	fns = set([('_'.join([x for x in fn.split('_') if x==x.lower()])) for fn in ll.ls('scp_csvs')])
	for sport, gss in sets_to_dl.items():
		for gs in gss:
			set_name = gs[0]
			csv_name = ll.alphanums(set_name, also=' ').replace(' ', '_').lower() + '.csv'
			csv_name = f'{sport}_{csv_name}'
			total.add(csv_name)
	if len(fns-total) > 0:
		print(f"\n[bold orange3]warning:[/bold orange3] couldn't find {len(fns-total)} / {len(fns)} sets:")
		for missing in (fns-total):
			print(f'\t{missing}')
	print('')
	'''
	if len(missed) > 0:
		print(f"\n[bold orange3]warning:[/bold orange3] couldn't find {len(missed)} / {len(set_names)} sets:")
		for m in sorted(missed):
			print(f'\t{m}')
	print('')

	stdl_ct = sum(len(v) for v in sets_to_dl.values())
	if not ll.yn(f"Download {stdl_ct} sets?"):
		quit()

	# def download_sets(sport, dl_sets, token, outp_dir):

	# Download the updates!
	for sport, gss in sets_to_dl.items():
		# if not verify_sets(sport, gss):
			# os._exit(1)
		outp_dir = 'new_scp_csvs'
		os.makedirs(outp_dir, exist_ok=True)
		download_sets(sport, gss, ll.env('SCP_API_TOKEN'), outp_dir)

			# if set_code:
				# csv_name = f'{set_code}_{csv_name}'
			# print(csv_name)

		# coordinate(sport, year, brand, words, ll.env('SCP_API_TOKEN'), True, 'scp_csvs')


if __name__ == '__main__':
	main()
