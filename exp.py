import ll


def main():
	crows = ll.lines('col.csv')[1:]
	card2quant = ll.freqs(crows)
	irows = []
	written = 0
	for i, (c, q) in enumerate(card2quant.items()):
		# if i == 0:
			# print(c, q)
			# quit()
			# continue

		(sport, year, brand, set, name, number, parallel, price, condition), quant = ll.csv(c), q
		sport = ' '.join((x[0].upper() + x[1:]) for x in sport.split('-'))

		q = f'{year} {set} {name} #{number}'
		if parallel:
			q += f' {parallel}'
		if condition and 'PSA' in condition:
			q += f' {condition}'
		q = q.replace('"', '""')
		q = f'"{q}"'

		extras = ['Date Purchased', 'Slab Serial #', 'Investment', 'Estimated Value', 'Ladder ID', 'Query', 'Notes', 'Tags', 'Date Sold', 'Sold Price', 'Image', 'Back Image']
		irow = {
			'Quantity': quant,
			'Category': sport,
			'Date Purchased': '02/01/2026',
			'Year': year,
			'Set': f'{brand} {set}',
			'Player': name,
			'Number': number,
			'Variation': parallel,
			'Condition': condition,
			'Query': q,
			# 'Investment': 0,
			'Investment': 'null',
			'Estimated Value': price,
		}
		# for e in extras:
			# if e not in irow:
				# irow[e] = ''

		irows.append(irow)

		if len(irows) == 500 or i == len(card2quant)-1:
			ll.write(ll.csv(irows), f't{written}.csv')
			written += 1
			irows = []



if __name__ == '__main__':
	main()
