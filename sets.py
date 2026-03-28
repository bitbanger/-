import json
import ll
import os
import re
import sys
import time

from ll import print

def main():
	scp_csv_dir = 'new_scp_csvs'
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
		'Donruss Optic',
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

	# _s(trie.dict())

	def copy(d, last=''):
		_um = lambda _k: ll.replaces(_k, {fm.replace(' ', ''): fm for fm in force_merges}).replace('&', 'and')
		_rc = lambda _k: _um(_k).replace(' Cards', '').replace('&', 'and')
		_rp = lambda _k: ll.rempre(_rc(_k), last).strip().replace('&', 'and')
		# TODO: this can't differentiate between true subsets of Topps
		# (e.g. 2014 Topps 1,000 Yard Club) and other Topps sets (e.g.
		# 2025 Topps Galaxy Chrome). scp has insert info; use that somehow?
		if isinstance(d, dict):

			def _ender(x):
				for ender in ('Topps', 'Donruss', 'Upper Deck'):
					if (ms:=re.findall(f'(.*) ([0-9][0-9][0-9][0-9]) {ender} (.*)', x)):
						return ms[0][-1]
				# if (spl:=x.split())[-2].isnumeric(): # <year> <ender>
					# return spl[-1]
				return ''

			if any(_ender(k) for k in d):
				# Gotta merge Topps into the subsets and flatten them out
				# to the parent level
				nd = {}
				for k, v in d.items():
					if (ender:=_ender(k)):
						# Normal
						if (rpk:=_rp(k)):
							nd[rpk] = copy(v, last=_rc(k))
					else:
						# Pull children out & flatten
						nd[(rpk:=_rp(k))] = []
						if isinstance(v, dict):
							for sk, sv in v.items():
								sk = rpk + ' ' + ll.rempre(_rp(sk), rpk).strip()
								nd[sk] = copy(sv, last=sk)
				return nd
			else:
				# Don't gotta deal with Topps
				return {_rp(k): copy(v, last=_rc(k)) for k, v in d.items() if _rp(k)}
		else:
			return d

	d = copy(trie.dict())
	_s(d)

	ll.write('hierarchy_of_sports_sets.json', json.dumps(d, indent=2))

	quit()


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
