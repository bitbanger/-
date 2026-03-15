import ll
import sys
import time


def price(id, graded=False, tries=5):
	url = f"https://www.sportscardspro.com/api/product?t={ll.env('SCP_API_TOKEN')}&id={id}"
	resp = None
	for _ in range(tries):
		try:
			resp = ll.json((raw_resp:=ll.url(url)))
			break
		except TypeError:
			print(raw_resp)
			print(resp)
			time.sleep(5)

	if resp is None:
		raise Exception(f"Error fetching card price: {tries} tries exhausted")

	if 'error' in resp:
		raise Exception(f"Error fetching card price: {resp['error']}")
	
	price = 0
	if graded:
		if 'manual-only-price' not in resp:
			if 'loose-price' in resp:
				raise Exception(f"Error fetching card price: graded price requested for ID {id}, but PSA 10 price not found in response")
			else:
				price = 0
		else:
			price = resp['manual-only-price']
	else:
		if 'loose-price' not in resp:
			price = 0
		else:
			price = resp['loose-price']

	return price/100


def main():
	if len(sys.argv) <= 1:
		ll.err(f"pass card IDs via CLI to get price")

	for id in sys.argv[1:]:
		print(price(id))


if __name__ == '__main__':
	main()
