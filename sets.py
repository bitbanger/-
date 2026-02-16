import ll
import os
import sys
import time


def main():
	scp_csv_dir = 'scp_csvs'
	words = [x.strip().lower() for x in sys.argv[1:]]

	for fn in ll.ls(ll.here(scp_csv_dir)):
		if all(w in fn.lower() for w in words):
			print(fn)


if __name__ == '__main__':
	main()
