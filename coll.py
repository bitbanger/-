import ll


def main():
	counts = ll.dd(int)
	for row in ll.csv('col.csv'):
		card = ll.render_csv(row, no_headers=True).strip()
		counts[card] += 1

	for c, n in sorted(counts.items(), key=ll.nth(1)):
		if n > 1:
			print(f'{n}\t\t{c}\n')


if __name__ == '__main__':
	main()
