import ll
import os
import sys
import time

from t import print_card


def main():

	rows = sorted(ll.csv('col.csv', header=False)[1:], key=lambda e: float(e[-2]))
	for row in rows:
		# 								sport,year,brand,set,name,number,parallel,price,condition
		#def print_card(	sport,year,set,name,num,var,price,grade,price_threshold):
		sport,year,brand,set,name,num,var,price,cond = row
		price = float(price)
		print_card(sport,year,set,name,num,var,price,cond,10.00)

	pass


if __name__ == '__main__':
	main()
