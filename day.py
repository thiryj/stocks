#Written by John Thiry - 2017
# this file contains routines to analyze one day's worth of price movements
#goal is to find tradable prior signals 

import stockLib as sl
import update as ud
import constants 
from position import Position 
from datetime import datetime
import pandas as pd
import itertools as iter

GOAL=2


def bestTrade(df):
	'''return time of the best trade'''
	#takes a minuteByDay single row df as argument
	#
	#best trade is the day's most profitable trade, if any
	#buy low, sell high, later
	#find the pair with the greatest delta and where time.low < time.high
	#sort them return best
	lenDf = len(df)
	#establish list of Positions
	Positions = []	
	#iterate through eachtime period and build a list of possible open/close Positions
	for i in range (0,lenDf):
		#open Position
		buyPrice=df.iloc[i]
		pos = Position('ticker')
		pos.buy(buyPrice,datetime.combine(datetime.now().date(),df.iloc[i].name),cost=0)
		Positions.append(pos)
		#loop through remaining time periods and build list of possible Positoins
		for k in range (i,lenDf):
			if (df.iloc[k] - buyPrice >= GOAL):	
				pos.sell(df.iloc[k],closeDT=datetime.combine(datetime.now().date(),df.iloc[k].name),cost=0)
	for x in Positions:
		x.display

def bestTradeDay(ticker,day):
	dfmbd = sl.minutesByDay(ticker)
	df0=pd.DataFrame(dfmbd.iloc[day])
	df0.columns=['close']
	df0['index'] = df0.index
	df0['index-open'] = df0[['index','close']].apply(tuple, axis=1)
	dfcomb=pd.DataFrame(list(iter.combinations(df0['index-open'],2)),columns=list(['open','close']))
	dfcomb['trade'] = dfcomb[['open','close']].apply(lambda row: (row['close'][1]-row['open'][1]),axis=1)
	daybest=dfcomb.groupby('trade').max().tail(1)
	return daybest

def bestTradeDay_(dfmbd,day):
	df0=pd.DataFrame(dfmbd.iloc[day])
	date_=df0.columns[0]
	open_=df0.iloc[0][0]
	df0.columns=['close']
	df0['index'] = df0.index
	df0['index-open'] = df0[['index','close']].apply(tuple, axis=1)
	dfcomb=pd.DataFrame(list(iter.combinations(df0['index-open'],2)),columns=list(['open','close']))
	dfcomb['trade'] = dfcomb[['open','close']].apply(lambda row: (row['close'][1]-row['open'][1]),axis=1)
	daybest=dfcomb.groupby('trade').max().tail(1)
	daybest['date']=date_
	daybest['dayOpen']=open_
	return daybest

def bestTrades(ticker,startDay=0,endDay=-1,startMinute=0,endMinute=-1):
	#returns best trade for each day
	dfmbd = sl.minutesByDay(ticker)
	#slice columns on minute
	if endMinute == -1:
		dfmbd=dfmbd.ix[:,startMinute:]
	else:
		dfmbd=dfmbd.ix[:,startMinute:endMinute+1]

	if endDay == -1:
		endRun = len(dfmbd)
	else:
		endRun = end
	#loop through remaining time periods and build list of possible Positoins
	print 'starting run'
	for i in range (startDay,endRun):
		print 'running day ' + str(i) + ':' + str((i/float((endRun-startDay))*100)) + '% done      \r',   
		if i == startDay:
			bestTrades=bestTradeDay_(dfmbd,i)
		else:
			bestTrades=bestTrades.append(bestTradeDay_(dfmbd,i))
	#reshape df
	bestTrades['tradeResult']=bestTrades.index
	bestTrades.index=bestTrades['date']
	del bestTrades['date']
	bestTrades['openTime']=bestTrades['open'].str[0]
	bestTrades['open']=bestTrades['open'].str[1]
	bestTrades['closeTime']=bestTrades['close'].str[0]
	bestTrades['close']=bestTrades['close'].str[1]
	bestTrades['openNorm']=bestTrades[['dayOpen','open']].apply(lambda row: sl.scaleNum(row['dayOpen'],row['open']),axis=1)
	bestTrades['closeNorm']=bestTrades[['dayOpen','close']].apply(lambda row: sl.scaleNum(row['dayOpen'],row['close']),axis=1)
	bestTrades['openMinute']=bestTrades[['openTime']].apply(lambda row: (row['openTime'].hour*60+row['openTime'].minute)-(9.5*60),axis=1)
	bestTrades['closeMinute']=bestTrades[['closeTime']].apply(lambda row: (row['closeTime'].hour*60+row['closeTime'].minute)-(9.5*60),axis=1)
	bestTrades['timeHeld']=bestTrades[['closeTime','openTime']].apply(lambda row: row['closeTime'].hour+row['closeTime'].minute/float(60)-row['openTime'].hour+row['openTime'].minute/float(60),axis=1) 
	bestTrades['resultPercent']=100*bestTrades['tradeResult']/bestTrades['open']
	return bestTrades
	
		
