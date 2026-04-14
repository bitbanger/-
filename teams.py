import ll

from quick.colors import colors
from quick.txt import rgb


def last_word(s):
	return s.strip().split()[-1]


def main():
	# checklist_csv = 'checklists/donruss_checklist.csv'
	checklist_csv = 'checklists/score_checklist.csv'
	def too_valuable(var):
		if 'Signature' in var:
			return True
		return False
	# checklist_csv = 'checklists/donruss_wnba_checklist.csv'

	# checklist_csv = 'checklists/rookies_stars_checklist.csv'

	checklist_csv = 'panini_checklists/football/2025/panini/rookies_and_stars.csv'

	# checklist_csv = 'checklists/prizm_wnba_checklist.csv'

	def too_valuable(var):
		if var:
			return True
		if var == 'Purple':
			return True
		if 'Signature' in var:
			return True
		if 'True Blue' in var:
			return True
		return False

	checklist_set = None

	by_team = ll.dd(set)
	num2name = {}
	for row in ll.csv(checklist_csv):
		# if row['ATHLETE'] == 'Marcus Allen':
			# print(row)
		checklist_set = str(row['YEAR']) + ' Panini ' + str(row['PROGRAM'])
		checklist_set = checklist_set.replace('WNBA Prizm', 'Prizm WNBA')
		by_team[last_word(row['TEAM'])].add(row['CARD NUMBER'])
		num2name[row['CARD NUMBER']] = row['ATHLETE']

	num2team = {}
	for team, nums in by_team.items():
		for num in nums:
			num2team[num] = team

	have_by_team = ll.dd(list)
	have_nums = []

	for row in ll.csv('col.csv'):
		have_set = str(row['year']) + ' ' + row['brand'] + ' ' + row['set']
		have_set = have_set.replace('&', 'and')
		# if row['parallel'] or (have_set != checklist_set):
		if have_set != checklist_set:
			continue
		if too_valuable(row['parallel']):
			continue

		have_nums.append(row['number'])

		have = row['number']
		team = num2team[have]
		have_by_team[team].append((have, row['parallel'], row['name']))

	for team, nums in by_team.items():
		if all(num in have_nums for num in nums):
			continue
		print(team)
		for num in nums:
			if num in have_nums:
				print(f'\t{num}\t✅')
			else:
				print(f'\t{num}\t❌')

	ll.rule()

	for team, have in have_by_team.items():
		havenms = [t[0] for t in have]
		havect = len(set(havenms))
		teamct = len(set(by_team[team]))
		if havect>=teamct and havect>1:
			freqs = ll.freqs(havenms)
			print(f'{min(freqs.values())} x [gold3]{team}[/gold3]')
			freqs = ll.freqs(have)
			for (num, var, name), ct in sorted(freqs.items(), key=ll.nth(0)):
				vstr = f' [{var}]' if var else ''
				for color, (r,g,b) in colors.items():
					if color.lower() in var.lower().split():
						vstr = rgb(vstr, r, g, b)
				ll.print(f'\t{ct}', end='')
				ll.print(f' [grey70]x[/grey70] [khaki3]{name}[/khaki3]', end='')
				ll.oldprint(vstr)
			print('')

	print('Missing:')
	for num, name in sorted(num2name.items(), key=lambda t: (ll.safe_int(t[0], none=True), ll.safe_int(t[0]))):
		if num not in have_nums:
			print(f'\t{name} #{num}')

	print('')

	print(f"Have: {len(sorted(set(have_nums)))} / {max([row['CARD NUMBER'] for row in ll.csv(checklist_csv)])}")

	pass


if __name__ == '__main__':
	main()
