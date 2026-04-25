import ll
import time

FIRST_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'referer': 'https://www.sportscardspro.com/',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    'sec-ch-ua-arch': '"arm"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"144.0.7559.133"',
    'sec-ch-ua-full-version-list': '"Not(A:Brand";v="8.0.0.0", "Chromium";v="144.0.7559.133", "Google Chrome";v="144.0.7559.133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"macOS"',
    'sec-ch-ua-platform-version': '"15.2.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
}

HEADERS = {
	'accept': 'application/json, text/javascript, */*; q=0.01',
	'accept-language': 'en-US,en;q=0.9',
	'priority': 'u=1, i',
	'referer': 'https://www.sportscardspro.com/offers?seller=sz42fm6fpkuh5vrsxu4w3bpnrq&status=collection',
	'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
	'sec-ch-ua-arch': '"arm"',
	'sec-ch-ua-bitness': '"64"',
	'sec-ch-ua-full-version': '"144.0.7559.133"',
	'sec-ch-ua-full-version-list': '"Not(A:Brand";v="8.0.0.0", "Chromium";v="144.0.7559.133", "GoogleChrome";v="144.0.7559.133"',
	'sec-ch-ua-mobile': '?0',
	'sec-ch-ua-model': '""',
	'sec-ch-ua-platform': '"macOS"',
	'sec-ch-ua-platform-version': '"15.2.0"',
	'sec-fetch-dest': 'empty',
	'sec-fetch-mode': 'cors',
	'sec-fetch-site': 'same-origin',
	'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
	'x-requested-with': 'XMLHttpRequest',
}


def next_page(cursor):
	return ll.http(
		f'https://www.sportscardspro.com/offers?seller=sz42fm6fpkuh5vrsxu4w3bpnrq&status=collection&cursor={cursor}&internal=true',
		headers=HEADERS,
	)

	return ll.http(url)


def parse_card(p):
	if isinstance(p, dict):
		card, cset = p['product-name'], p['console-name']
	else:
		card, cset = ll.map(ll.strip, p.text.strip().split('\n'))

	sport, cset = cset.split(' Cards ')

	# year = ll.regf(f'(\d\d\d\d)')(cset)
	# print(int(year))
	# rest = cset[cset.find(f'{year} '):]

	var = ll.regf('\\[(.*)\\]')(card)
	name = card.split('[')[0].split('#')[0].strip()
	num = card.split('#')[-1].split('[')[-1].strip()

	return sport, cset, name, num, var


def first_page():
	FIRST_HEADERS['cookie'] = ll.read('.cookie')

	# soup = ll.soup('https://www.sportscardspro.com/offers?seller=sz42fm6fpkuh5vrsxu4w3bpnrq&status=collection', headers=FIRST_HEADERS)
	soup = ll.soup(ll.sel('https://www.sportscardspro.com/offers?seller=sz42fm6fpkuh5vrsxu4w3bpnrq&status=collection', headers=FIRST_HEADERS))

	total = int(soup.find_all('td', class_='number')[-1].text)

	cards = []
	quants = [int(x.attrs['value']) for x in soup.find_all('input', class_='quantity')]
	for i, p in enumerate(soup.find_all('p', class_='title')):
		for _ in range(quants[i]):
			cards.append(parse_card(p))

	del FIRST_HEADERS['cookie']
	soup = ll.soup('https://www.sportscardspro.com/offers?seller=sz42fm6fpkuh5vrsxu4w3bpnrq&status=collection', headers=FIRST_HEADERS)
	cursor = soup.find_all('input', attrs={'name': 'cursor'})[0].attrs['value']

	return cards, cursor, total


def main():

	first_page_url = 'https://www.sportscardspro.com/offers?seller=sz42fm6fpkuh5vrsxu4w3bpnrq&status=collection'

	cards = []

	fp_cards, cursor, total = first_page()
	cards.extend(fp_cards)

	def _it(cursor):
		while True:
			resp = ll.json(next_page(cursor))

			got = 0
			for card in resp['offers']:
				parsed_card = parse_card(card)
				for _ in range(card['quantity']):
					yield parsed_card
					got += 1

			if 'cursor' not in resp:
				if got > 0:
					break
				ll.print(resp)
				continue

			cursor = resp['cursor']

			time.sleep(3)

	for card in ll.track(_it(cursor), total=total, title='Scraping: '):
		cards.append(card)

	outp_f = 'scraped_collection.csv'

	ll.print(f'Wrote {len(cards)} cards to [green]{outp_f}[/green]')

	with open(outp_f, 'w+') as f:
		f.write(ll.csv(('sport', 'set', 'name', 'number', 'parallel')) + '\n')
		for card in cards:
			f.write(ll.csv(card) + '\n')


if __name__ == '__main__':
	main()
