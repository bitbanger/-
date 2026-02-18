import ll

ll.import_from(ll.here('dl_scp.py'), 'get_sets')
ll.import_from(ll.here('dl_scp.py'), 'download_sets_interactive')
ll.import_from(ll.here('dl_scp.py'), 'verify_sets')
# ll.import_from(ll.here('dl_scp.py'), 'coordinate')


def main():
	set_names = []

	for fn in ll.ls('scp_csvs', abs=True):
		if not fn.endswith('.csv'):
			continue

		dn = ll.dn(fn)
		bn = ll.bn(fn)

		set_name = bn[:-len('.csv')].replace('__', '_').replace('_', ' ')
		set_names.append(set_name)

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

	# sets_to_dl = []
	sets_to_dl = ll.dd(list)
	for p in ll.track(prefixes, title='Getting set names: '):
		sport = p.strip().split(' ')[0]
		p = ' '.join(p.strip().split(' ')[1:])

		year = ll.regf('([0-9][0-9][0-9][0-9])')(p)
		spl = [x for x in p[p.index(year):].strip().split(' ')[1:]]
		brand = spl[0]
		words = spl[1:]

		sets_to_dl[sport].extend(get_sets(sport, year, brand, words))

	# Check which sets we couldn't find, so can't update
	total = set()
	fns = set([('_'.join([x for x in fn.split('_') if x==x.lower()])) for fn in ll.ls('scp_csvs')])
	for sport, gss in sets_to_dl.items():
		for gs in gss:
			set_name = gs.text
			csv_name = ll.alphanums(set_name, also=' ').replace(' ', '_').lower() + '.csv'
			csv_name = f'{sport}_{csv_name}'
			total.add(csv_name)
	if len(fns-total) > 0:
		print(f"\n[bold orange3]warning:[/bold orange3] couldn't find {len(fns-total)} / {len(fns)} sets:")
		for missing in (fns-total):
			print(f'\t{missing}')
	print('')

	# Download the updates!
	for sport, gss in sets_to_dl.items():
		# if not verify_sets(sport, gss):
			# os._exit(1)
		outp_dir = 'new_scp_csvs'
		download_sets_interactive(sport, gss, ll.env('SCP_API_TOKEN'), outp_dir)

			# if set_code:
				# csv_name = f'{set_code}_{csv_name}'
			# print(csv_name)

		# coordinate(sport, year, brand, words, ll.env('SCP_API_TOKEN'), True, 'scp_csvs')


if __name__ == '__main__':
	main()
