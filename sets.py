import ll
import os
import sys
import time

from ll import print

def main():
	scp_csv_dir = 'scp_csvs'
	words = [x.strip().lower() for x in sys.argv[1:]]

	seen = set()
	base = None
	trie = ll.lldd(dict)
	limit = None
	cns = set()
	for i, fn in enumerate(ll.track(sorted(ll.ls(ll.here(scp_csv_dir), pat='.*\\.csv', abs=True)))):
		if (limit is not None) and (i >= limit-1):
			break

		for row in ll.csv(fn):
			cns.add(row['console-name'])

	force_merges = [
		'Prizm WNBA',
		'Donruss WNBA',
		'Prizm Draft Picks',
	]
	force_repls = {
		' and ': ' & ',
	}
	def _norm(s):
		for fm in force_merges:
			s = s.replace(fm, fm.replace(' ', ''))
		for k, v in force_repls.items():
			s = s.replace(k, v)
		return s

	cns = list(cns)
	def _sport(s):
		return ll.splitf('[0-9]'*4)(s)[0].replace('Cards', '').strip()
	# sports = list(set(x.strip().split()[0] for x in cns))
	sports = [_sport(x) for x in cns]
	cns.extend(sports)
	
	cns = [_norm(cn) for cn in cns]
	cns = [cn.strip().split() for cn in cns]

	cns = sorted(cns, key=len, reverse=True)

	def lstartswith(l1, l2):
		return len(l2) <= len(l1) and all(l1[i]==l2[i] for i in range(len(l2)))

	pairs = []
	while len(cns) > 0:
		merged = False
		for cn in cns[1:]:
			# if cns[0].startswith(cn):
			# print(' '.join(cns[0]))
			# print('\t' + ' '.join(cn))
			# print(lstartswith(cns[0], cn))
			# print('')
			if lstartswith(cns[0], cn):
				pairs.append((' '.join(cn), ' '.join(cns[0])))
				merged = True
				break
		cns = cns[1:]

	trie = ll.lldd()
	for short, long in sorted(pairs, key=lambda p: (len(p[0]), len(p[1]))):
		cursor = trie
		while True:
			try:
				cursor_key = max([k for k in cursor.keys() if short.startswith(k)], key=len)
			except ValueError:
				cursor_key = short
				break
			if cursor_key == short:
				break
			cursor = cursor[cursor_key]

		# trie[short][long]
		cursor[cursor_key][long]

	# print(trie.dict())

	def _s(d, lvl=0):
		for k, v in sorted(d.items(), key=ll.nth(0)):
			dk = k.split(' Cards ')[-1]
			for sport in sorted(sports, key=len, reverse=True):
				if dk.startswith(sport+' '):
					dk = dk[len(sport)+1:]
					break
			for fm in force_merges:
				dk = dk.replace(fm.replace(' ', ''), fm)
			if k in sports and len(v)==0:
				continue
			print('\t'*lvl + dk)
			if isinstance(v, dict):
				_s(v, lvl=lvl+1)

	_s(trie.dict())

'''
	for cn in cns:
		s = cn.strip().split()
		cursor = trie
		for w in s:
			cursor = cursor[w]
		# cursor['<EOF>']

	def serialize(d, pref=''):
		def _it():
			for k, v in d.items():
				if k == '<EOF>':
					yield pref
				else:
					for x in serialize(v, pref=pref+' '+k):
						yield x
		return list(_it())

	# print('\n'.join(serialize(trie)))
	# print(trie.dict())
	print(ll.patricia(trie.dict()))
'''



if __name__ == '__main__':
	main()
