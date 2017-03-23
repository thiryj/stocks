#Written by John Thiry - 2016

#other imports
import os
import csv
from collections import OrderedDict as OD
import collections
from datetime import datetime
import pandas as pd
import update as ud
import numpy as np
from shutil import copyfile
import pdb
from position import Position
import constants

#initialize magic numbers (constants)
FIRSTDATEINDEX =	1406
LASTDATEINDEX =		0
GOAL_INCREASE_PERCENT = 0.025
GOAL_OPEN =			0.01
GOAL_LH= 			0.01
STOP_LOSS =			0.01
GOAL_DIP = 			0


#initialize local variables
stratCounter = 0
stratSize=0
priceFileName = 'data_price.csv'
testCaseFileName = 'data_testcase.csv'
resultsFileName = 'results.csv'
dateRows=[]   #list of tuples.  each list iten is a day
dateRowsAdj=[]  #same list but prices adjusted for stock splits
outputInner=[] #list comprised of [goal,result]
output=[] # list comprised of [investment,outputInner[]]
#fieldnames are Date,Open,High,Low,Close

#define classes
class DayPrice(collections.namedtuple('DayPrice','Date, Open, High, Low, Close, Volume,CloseAdj' )):
	__slots__=()
	@property
	def adjustmentFactor(self):
		return (float(self.CloseAdj) / float(self.Close))
		
DayPriceAdj = collections.namedtuple('DayPriceAdj', 'Date, Open, High, Low, Close, Volume')

#read data from .csv
def readQuotes(priceFileName):
	with open(priceFileName,'r') as priceFile:
		header = priceFile.readline()
		for quoteRow in map(DayPrice._make, csv.reader(priceFile)):
			quoteRows.append(quoteRow)
	
	#parse data to data structure
	#prepare adjusted price data
	#data structure is a list of rows. each has date object, (floats) Open, High, Low, Close, (int) Volume
	for record in dateRows:
		dateRowAdj = DayPriceAdj(datetime.strptime(record.Date,"%m/%d/%Y"), \
			float(record.Open)*float(record.adjustmentFactor), \
			float(record.High)*float(record.adjustmentFactor), \
			float(record.Low)*float(record.adjustmentFactor), \
			float(record.CloseAdj), \
			int(record.Volume))
		dateRowsAdj.append(dateRowAdj)
		
def parseDT(dt):
	return datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
		
#write data to .csv
def writeResults(output):
	# python 3.x:with open(resultsFileName,'r+', newline='') as resultsFile:
	with open(resultsFileName,'r+') as resultsFile:
		resultsWriter = csv.writer(resultsFile,delimiter=',')
		#write header
		#resultsWriter.writerow(["Investment","Goal","Cum% Increase"])
		for resultsRow in output:
			resultsWriter.writerow(resultsRow)

def profit(buy,sell,costTrade=constants.COST_TRADE):
	"""given the total buy cost dollars and sell proceeds, return profit net of fee"""
	return(sell-buy - 2*costTrade)

def profitPercent(buy,sell):
	return(profit(buy,sell)/buy)
	
def dayOpenHigh(day):
	"""return the number of dollars from open to high for a given day"""
	return(day.High-day.Open)

def dayOpenHighMetDollarGoal(day,goal):
	"""True if High-Open met or exceeded dollar amount goal"""
	if dayOpenHigh(day) >= goal:
		return(True)
	else:
		return(False)
		
def dayOpenHighMetPercentGoal(day,goal=GOAL_INCREASE_PERCENT):
	"""True if High-Open met or exceeded percentage gain goal"""
	if  dayOpenHigh(day)/day.Open >= goal:
		return(True)
	else:
		return(False)
		
def numWins(
	goal=GOAL_INCREASE_PERCENT, 
	startDayIndex=FIRSTDATEINDEX,
	endDayIndex=LASTDATEINDEX): #prices is the list of day prices
	"""gives the number of days the High - Open met or exceed percentage gain goal"""
	wins=0
	for day in dateRowsAdj[endDayIndex:startDayIndex]:
		if dayOpenHighMetPercentGoal(day,goal) ==True:
			wins += 1
	print(wins)
		
def dayProfitFromPercentGoal(
	day,
	goal=GOAL_INCREASE_PERCENT,
	investment=constants.INVESTMENT):
	"""returns $ increase when same dale sale using goal increase"""
	if dayOpenHighMetPercentGoal(day,goal):
		return(profit(investment,investment*(1+goal)))
	else:
		return(0)

#introduce the "Position".  this takes into account that 
#a purchase may not sell for a period of days if price went down
def positionDatePercentGoalMet(
	startDayIndex=FIRSTDATEINDEX,
	goal=GOAL_INCREASE_PERCENT):
	"""returns end index of day when % goal is met.  Return False if goal never met"""
	for day in dateRowsAdj[startDayIndex: :-1]:
		if dayOpenHighMetPercentGoal(day,goal):
			return(dateRowsAdj.index(day))
	else:
		return(False)

#find non compounded total $ profit from multi day trading.  may involve 0, 1 or more position round trips
def profitDateRange(
	startDayIndex=FIRSTDATEINDEX,
	endDayIndex=LASTDATEINDEX,
	goal=GOAL_INCREASE_PERCENT,
	investment=constants.INVESTMENT):
	"""returns $ profit from trading over a period of days"""
	profitCum=0
	for day in dateRowsAdj[startDayIndex:endDayIndex:-1]:
		if dayOpenHighMetPercentGoal(day,goal):
			profitCum=profitCum+dayProfitFromPercentGoal(day,goal,investment)
	return(profitCum)	
			
#find Compounded! total $ profit from multi day trading.  may involve 0, 1 or more position round trips
def profitDateRangeCompounded(
	startDayIndex=FIRSTDATEINDEX,
	endDayIndex=LASTDATEINDEX,
	goal=GOAL_INCREASE_PERCENT,
	investment=constants.INVESTMENT):
	"""returns $ profit from trading over a period of days"""
	profitCum=0
	investmentCum=investment
	for day in dateRowsAdj[startDayIndex:endDayIndex:-1]:
		if dayOpenHighMetPercentGoal(day,goal):
			profitCum=profitCum+dayProfitFromPercentGoal(day,goal,investmentCum)
			investmentCum=investment + profitCum
	return(profitCum)	

def totalMin(df_):
	#returns the tuple (Timestamp(),dateime.time()) of the lowest min of the entire study
	return df_.low.idxmin()
	
def dupsNum(df_):
	#return the number of duplicate indexes
	dupCounter = df_.index.get_duplicates()
	print 'number of duplicate indexes is: ', len(dupCounter)
	return dupCounter

def scaleNum(standard,observable):
	#scale observable to a standard.  zero difference return 0.  
	#example:  scanleNum(5,6) returns 0.2.  in other words, 6 is 20% bigger than 5
	return (float(observable-standard)/standard)-1

def scale_(df_):#  takes a dfu mulitindex
	#scale each day data to %change from opening value
	#for instance if the time n quote is 23 and the opening was 22, then return (23-22)/22=.0454
	#21 would transform to (21-22)/22 -1 = 0.9545
	#df_['closeScaled'] = (df_.close.div(df_.groupby(level=0)['open'].transform('first'))-1)*100
	dfg_ = df_.groupby(level=0)['open'].transform('first')
	dfs_ = pd.DataFrame()
	dfs_['open']=(df_.open.div(dfg_)-1)*100
	dfs_['high']=(df_.high.div(dfg_)-1)*100
	dfs_['low']=(df_.low.div(dfg_)-1)*100
	dfs_['close']=(df_.close.div(dfg_)-1)*100
	return dfs_
	
def days(df_):
	return df_.groupby(level=0)
	
def day_(df_,i): #takes a dfm and day integer, returns one days worth
	return df_.xs(df_.iloc[i].name[0].date())

def dayCount(df_):
	#return the number of "minute" OHLC reports in each day
	#argument must be of type multiInd
	grouped=df_.groupby(level=0)
	print 'number of days in study is: ', len(grouped)
	return grouped.last()
	
def dayMin(df_):
	#return df with the minimum 'low' in each day
	#argument must be of type multiInd
	return df_.groupby(level=0).low.min()
	
def dayMinTime(df_):
	#return the  time of day of the daily minimum
	return df_.groupby(level=0).low.idxmin()

def dayMax(df_):
	#return df with the max 'high' in each day
	#argument must be of type multiInd
	return df_.groupby(level=0).high.max()
	
def dayMaxTime(df_):
	#return the  time of day of the daily max
	return df_.groupby(level=0).high.idxmax()
	
def dayMean(df_):
	#return the mean of values in each day
	pass

def	dayOpen(df_):  #argument must be multiInd
	#gets the open for each day
	#find min time stamp then return open of that timestamp
	return df_.groupby(level=0).open.head(1)

def dayClose(df_):
	return df_.groupby(level=0).close.tail(1)
	
def dayAgg(df_):  #argument must be multiInd
	#shows open, high, low, close per day
	return df_.groupby(level=0).agg(OD([('high',np.max),('low',np.min)]))
	
def dayDisplay(df_):
	#builds a new dataframe showing various daily values of interest
	#drop the time from dayOpen
	daysOpen=dayOpen(df_)
	daysOpen.index=daysOpen.index.droplevel(1)
	daysClose=dayClose(df_)
	daysClose.index=daysClose.index.droplevel(1)
	dfd_ = pd.concat([daysOpen,
					  dayMaxTime(df_).apply(lambda x: x[1]),
					  dayMax(df_),
					  dayMinTime(df_).apply(lambda x: x[1]),
					  dayMin(df_),
					  daysClose],
					  join='outer',axis=1)
	dfd_.columns=['open','highT', 'high', 'lowT', 'low', 'close']
	return dfd_
	
def	dayStudy(df_,goalOpen=GOAL_OPEN, goalLH=GOAL_LH):
	#gets some choice info baby
	dfd = dayDisplay(df_)
	dfStudy_=pd.DataFrame()
	dfStudy_['open_high'] =		dfd['high']-dfd['open']
	dfStudy_['open_highP'] =	(dfd['high']-dfd['open'])/dfd['open']
	dfStudy_['open_low'] =		dfd['low']-dfd['open']
	dfStudy_['open_lowP'] =		(dfd['low']-dfd['open'])/dfd['open']
	dfStudy_['first'] =			np.where(dfd['highT']<dfd['lowT'],1,0)
	dfStudy_['trade_open'] =	np.where(dfStudy_['open_highP']>goalOpen,1,0)
	dfStudy_['trade_LH'] =		np.where(((dfd['high']-dfd['low'])/dfd['low']>goalLH) & 
									(dfd['lowT']<dfd['highT']),1,0)
	dfStudy_['day_result'] =	np.where(dfd['close']>dfd['open'],1,0)
	#dfStudy_['prev_day_result']=np.where(???
	return dfStudy_
	
def daysByMinutes(ticker,endDay=0,startDay=0):
#	pdb.set_trace()
	dfm_=ud.fetchMI(ticker)
	dfms_=scale_(dfm_)
	dfmsc_=dfms_['close']
	if endDay <> 0:
		dfmscu_=dfmsc_.unstack(1)
		dfmscuN=dfmscu_.iloc[startDay:endDay]
		dfWork=dfmscuN.stack()
	else:
		dfWork=dfmsc_
	return dfWork.unstack(0)
	
def minutesByDayScale(ticker):
	dfm=ud.fetchMI(ticker)
	dfms=scale_(dfm)
	dfmsu=dfms.unstack()
	return dfmsu.loc[:,['close']]['close']


def minutesByDay(ticker):
	dfm=ud.fetchMI(ticker)
	dfmu=dfm.unstack()
	return dfmu.loc[:,['close']]['close']

def stats(df_,goalOpen=GOAL_OPEN, goalLH=GOAL_LH):
	dfStudy_=dayStudy(df_,goalOpen, goalLH)
	stats_day=pd.DataFrame()
	stats = {}
	stats_day['day_result_up'] = np.where(dfStudy_['day_result']=='up',1,0)
	stats['day_result_up']= stats_day['day_result_up'].mean()
	return stats
	
def bestTrade(df_):
	'''return time of the best trade'''
	#best trade is the day's most profitable trade, if any
	#buy low, sell high, later
	#return a dict with [time open, price open, time close, price close]
	#dot product the lows and highs creating many pairs
	
	#find the pair with the greatest delta and where time.low < time.high
	
def	buy(position_,price,investment=constants.INVESTMENT,cost=constants.COST_TRADE):
	position_['shares'] = 	(investment-cost)/price
	position_['basis'] = 	investment+cost
	position_['buyPrice'] = price
	
def sell(price, position, cost=constants.COST_TRADE):
	return position['shares']*price - cost

def getDate(ts): #ts must be Timestamp
	return str(ts.year) + '-' + str(ts.month) + '-' + str(ts.day)
	
'''stop 0.  trailStop in play
	harvest =	pd.Series(range(200,201))/100
	stop =		pd.Series(range(0,1))/100
	dip =		pd.Series(range(0,1))/1000
	trailP =	pd.Series(range(10,15))/1000
	trailInit = pd.Series(range(0,20))/1000
'''
''' stop 0.  harvest in play.  trailStop out
	harvest =	pd.Series(range(35,45))/1000
	stop =		pd.Series(range(0,1))/100
	dip =		pd.Series(range(0,5))/1000
	trailP =	pd.Series(range(200,201))/100
	trailInit = pd.Series(range(200,201))/100
'''
def runTrials(df_):
	global stratSize
	global stratCounter
	stratCounter=0
	#build a test DataFrame for the trials
	harvest =	pd.Series(range(200,201))/100
	stop =		pd.Series(range(0,1))/100
	dip =		pd.Series(range(0,1))/1000
	trailP =	pd.Series(range(945,1005))/100000
	trailInit = pd.Series(range(10,15))/10000
	#trailInit is the percentage that open price must climb to before trail stop is acive
	#0 means trail stop is active at open.  
	#1.0 menas trail stop is inactive until open doubles in price for the day - ie never
	closeEachDay = pd.Series([True])
	#pdb.set_trace()
	testdf_ = pd.DataFrame(index=pd.MultiIndex.from_product([harvest,stop,dip,trailP,trailInit,closeEachDay]))
	testdf_['harvestP'] = 		testdf_.index.get_level_values(0)
	testdf_['stopLossP'] = 		testdf_.index.get_level_values(1)
	testdf_['buyDip'] = 		testdf_.index.get_level_values(2)
	testdf_['trailP'] = 		testdf_.index.get_level_values(3)
	testdf_['trailI'] = 		testdf_.index.get_level_values(4)
	testdf_['closeEachDay'] = 	testdf_.index.get_level_values(5)
	stratSize =	len(testdf_)
	print 'number of trials is: ', stratSize
	testdf_['result1']=testdf_.apply(lambda x: strat(df_,
													goalOpen =		x[0],
													stopLoss =		x[1],
													goalDip =		x[2],
													trailStopP = 	x[3],
													trailStopInitP=	x[4],
													closeEachDay =	x[5],
													logLevel = 		0,
													singleRun = 	False),axis=1)
	#testdf_.nlargest(20,'result1')
	return testdf_
	
def	strat(	df_,
			goalDip = 		GOAL_DIP,
			goalOpen=		GOAL_OPEN,
			goalLH=			GOAL_LH,
			stopLoss = 		STOP_LOSS,
			trailStopP = 	constants.TRAIL_STOP_P,
			trailStopInitP =	constants.TRAIL_STOP_INIT_P,
			investment =	constants.INVESTMENT,
			closeEachDay =	True,
			logLevel = 		2,
			singleRun =		True,
			debugLevel = 	0):
	#buy when stock dips down to x% of open
	#sell when meet open goal or sell when meet loss stop
	#logLevel=0 for running trials
	#logLevel=1 for printing start/end stats
	#logLevel=2 for logLevel and daily results
	global stratSize
	global stratCounter
	SOLD_STOP_LOSS =	'stop'
	SOLD_TRAIL_STOP = 	'trail'
	SOLD_HARVEST = 		'goal'
	SOLD_CLOSE = 		'close'
	SOLD_NO_SALE = 		'no sale'
	SOLD_NO_OPEN = 		'no open'
	profit =			0
	initialInvestment =	investment
	dfd_ = 				dayDisplay(df_)
	dfds_ = 			dayStudy(df_,goalOpen=goalOpen)
	dayLosses = 		0
	dayWins = 			0
	dayTrailStops =		0
	dayNoSale = 		0
	daySellClose = 		0
	dayNoOpen = 		0
	positionOpened =	False
	marketOrderLoss = 	0.01 #the loss due to inefficient market order execution
	lenDFD =			len(dfd_)
	if logLevel > 0:
		print('goalOpen: %.4f||stopLoss: %.4f||dip: %.4f||close day: %s||debug:%s' 
		%(goalOpen,stopLoss,goalDip,closeEachDay,debugLevel))
	#loop over all days in study
	if debugLevel > 0: pdb.set_trace()
	for i in range(1, lenDFD):
		if debugLevel > 0: pdb.set_trace()
		#if i==26: pdb.set_trace()
		tradeResult=0
		sold=False
		#pdb.set_trace()
		k=0
		#get days worth of df values
		iDay =	df_.xs(getDate(dfd_.iloc[i].name))
		#iPDay =	df_.xs(getDate(dfd_.iloc[i-1].name))
		#design a test to open.  if none desired, set test1 = True
		pDay = dfd_.iloc[i-1]
		test1 = True #pDay['close'] > pDay['open']
		lenIDay = len(iDay)
		if (not positionOpened) and test1:
			#establish open position (buy stock)
			dayBuyPrice = dfd_.iloc[i]['open']*(1-goalDip)
			#loop through all times in df day.  test for opening trigger (dip % met)
			for k in range(0, lenIDay):
				timePeriodLow = iDay.iloc[k].low
				if timePeriodLow <= dayBuyPrice:
					if debugLevel > 0: pdb.set_trace()
					#if i==26: pdb.set_trace()
					pos1=Position('strat')
					pos1.buy(	dayBuyPrice,
								openDT = datetime.combine(dfd_.iloc[i].name,iDay.iloc[k].name),
								investment=investment)
					positionOpened = 		True
					pos1.stopLoss = 		pos1.openPrice*(1-stopLoss)
					pos1.harvest =			pos1.openPrice*(1+goalOpen)
					pos1.trailStop =		pos1.high*(1-trailStopP)
					pos1.trailStopInit =	pos1.openPrice*(1+trailStopInitP)
					#advance k to next minute
					k+=1
					break
			if debugLevel > 0: pdb.set_trace()
		else:
			if logLevel > 2:
				print i,'|already open from last day'
		#test if we opened that day
		#pdb.set_trace()
		if positionOpened:
			#then test for stop loss or goal or trail stop.
			#alt trail stop - only activate if high > some trail stop initiation goal.  
			#if not, then test for goal (alternate strat - let position roll to next day)
			#if bought on dip, then must start searching for sell points after that buy time.
			sold=False
			#pdb.set_trace()
			for j_ in range(k, lenIDay):
				timePeriodLow = 	iDay.iloc[j_].low
				timePeriodHigh = 	iDay.iloc[j_].high
				if timePeriodHigh >= pos1.high:
					pos1.high = timePeriodHigh
				#if timePeriodHigh > pos1.trailStopInit:
					#pdb.set_trace()
				if pos1.trailStopActive:
					#check for updated high
					if timePeriodHigh >= pos1.high:
						pos1.high = 		timePeriodHigh
						pos1.trailStop = 	pos1.high*(1-trailStopP)
				else:
					#else check for trail stop initiation
					if pos1.high >=	pos1.trailStopInit:
						pos1.high = 			timePeriodHigh
						pos1.trailStopActive = 	True
				if ((timePeriodLow <= pos1.stopLoss) or (timePeriodHigh >= pos1.harvest) or ((timePeriodLow <= pos1.trailStop) and pos1.trailStopActive)):
					#pdb.set_trace()
					if ((timePeriodLow <= pos1.trailStop) and pos1.trailStopActive):
						#sell at trail stop
						soldMethod	= SOLD_TRAIL_STOP
						soldPrice 	= pos1.trailStop - marketOrderLoss
						dayTrailStops+=1
					elif timePeriodHigh >= pos1.harvest:
						#sell at goal
						soldMethod	= SOLD_HARVEST
						soldPrice 	= pos1.harvest
						dayWins+=1
					elif timePeriodLow <= pos1.stopLoss:
						#sell at loss suite
						soldMethod 	= SOLD_STOP_LOSS
						soldPrice 	= pos1.stopLoss - marketOrderLoss
						dayLosses+=1
					#if i==17: pdb.set_trace()
					soldTime = iDay.iloc[j_].name
					proceeds = pos1.sell(soldPrice,closeDT = soldTime)
					sold=True
					positionOpened=False
					break
				else:
					#did not meet sale criteria
					pass
			if not sold:
				if closeEachDay:
					soldTime = iDay.iloc[lenIDay-1].name
					proceeds = pos1.sell(dfd_.iloc[i]['close'],closeDT = soldTime)
					sold=True
					soldMethod=SOLD_CLOSE
					positionOpened=False
					daySellClose+=1
				else:
					#let position roll to next day
					soldMethod=SOLD_NO_SALE
					dayNoSale+=1
					dayReport = '%3d|%s|buy:%.2f|up:%.2f|stop:%.2f|trail:%.2f|%s|high: %.2f|run:%d|%+5.1f%%'
					dayPrintList = (i,
									dfd_.iloc[i].name.strftime('%Y/%m/%d'),
									pos1.openPrice,
									pos1.harvest,
									pos1.stopLoss,
									pos1.trailStop,
									soldMethod,
									pos1.high,
									investment,
									100*profit/float(initialInvestment))
			if sold:
				tradeResult = proceeds - investment
				profit = profit + tradeResult
				investment = investment + tradeResult 
				dayReport = '%3d|%s|buy:%.2f|up:%.2f|stop:%.2f|trail:%.2f|time:%s:%s|%s|gain:%5d|run:%d|%+5.1f%%'
				dayPrintList=(	i,
								dfd_.iloc[i].name.strftime('%Y/%m/%d'),
								pos1.openPrice,
								pos1.harvest,
								pos1.stopLoss,
								pos1.trailStop,
								str(soldTime.hour).zfill(2),
								str(soldTime.minute).zfill(2),
								soldMethod,
								tradeResult,
								investment,
								100*profit/float(initialInvestment))
				#destroy pos1 to get ready for next day.  
				#future enhancement = persist pos1 to postion history
				del pos1
			else:
				pass
		else:
			#did not open that day
			dayNoOpen+=1
			soldMethod=SOLD_NO_OPEN
			dayReport = '%3d|%s|position opened: %s|sold method: %s'
			dayPrintList = (i,dfd_.iloc[i].name.strftime('%Y/%m/%d'),positionOpened,soldMethod)
		#retain day performance of strategy in a dfds_.  Return dfd_ at end
		dfds_.ix[i,'result'] = tradeResult
		if logLevel > 1:
			print(dayReport % dayPrintList)
	#deal with open position at the end
	if positionOpened:
		#close it at end of last day
		soldTime = iDay.iloc[lenIDay-1].name
		proceeds = pos1.sell(dfd_.iloc[i]['close'], soldTime)
		sold=True
		positionOpened=False
		daySellClose+=1
		tradeResult = proceeds - investment
		profit = profit + tradeResult
		if logLevel > 1:
			print 'selling at end of study period.  i day is: ',i
			print i, 'trade result is: ', tradeResult
	if logLevel > 0:
		tabLen = 20
		print('total days is:\t%5d' % lenDFD).expandtabs(tabLen)
		print('wins is:\t%5d|%6.1f%%' %(dayWins, 100*(dayWins/float(lenDFD)))).expandtabs(tabLen)
		print('losses is:\t%5d|%6.1f%%' %(dayLosses, 100*(dayLosses/float(lenDFD)))).expandtabs(tabLen)
		print('trail stops is:\t%5d|%6.1f%%' %(dayTrailStops, 100*(dayTrailStops/float(lenDFD)))).expandtabs(tabLen)
		print('sell at close is:\t%5d|%6.1f%%' % (daySellClose, 100*(daySellClose/float(lenDFD)))).expandtabs(tabLen)
		print('did not open is:\t%5d|%6.1f%%' %(dayNoOpen, 100*(dayNoOpen/float(lenDFD)))).expandtabs(tabLen)
		print('prev open no sale:\t%5d|%6.1f%%' %(dayNoSale,100*(dayNoSale/float(lenDFD)))).expandtabs(tabLen)
		print('profit is:\t$%5d|%6.1f%%' %(profit, 100*(profit/float(initialInvestment)))).expandtabs(tabLen-1)
	finalReport = 'Gain: %.5f|dip %.4f|open %.4f|stop %.4f|trail %.4f|trailI %.4f|closeDay %s'
	printList = (((	profit/float(initialInvestment))*100), 
					goalDip, 
					goalOpen, 
					stopLoss, 
					trailStopP,
					trailStopInitP,
					closeEachDay)
	if singleRun:
		returnObj = dfds_
	else:
		stratCounter+=1
		statusReport = "%.4f|"
		finalReport = statusReport + finalReport
		printList = list(printList)
		printList.insert(0,stratCounter/float(stratSize))
		printList = tuple(printList)
		returnObj =  profit/initialInvestment
	print(finalReport % printList)
	return returnObj
		
def best(df_, results=20):
	return df_.nlargest(results,'result1')
	
def corrs(df_,goalOpen=GOAL_OPEN,stopLoss=STOP_LOSS,goalDip=GOAL_DIP,closeEachDay=False): #takes a regular df
	#convert to dayStudy df
	dfds_=dayStudy(df_,goalOpen,stopLoss)
	#get strat results
	#pdb.set_trace()
	dfdr_ = strat(df_,goalOpen=goalOpen,stopLoss=stopLoss,goalDip=goalDip)
	
	#first to up/down result
	corFirst_DayResult=dfds_['first'].corr(dfds_['day_result'])
	print 'corFirst_DayResult:', corFirst_DayResult
	
	#first to trade result sign
	corFirst_ResultSign = dfds_['first'].corr((dfdr_['result']/dfdr_['result'].abs()))
	print 'corFirst_ResultSign: ', corFirst_ResultSign
	
	#day result to trade result $
	corDayResult_Result = dfds_['day_result'].corr(dfdr_['result'])
	print 'corDayResult_Result: ', corDayResult_Result
	
	#day result to trade result sign positve/negative
	corDayResult_ResultSign = dfds_['day_result'].corr((dfdr_['result']/dfdr_['result'].abs()))
	print 'corDayResult_ResultSign: ', corDayResult_ResultSign
	
def	fileName(ticker,type, overwrite=False):
	if overwrite:
		strTime = ''
	else:
		strTime = datetime.now().strftime('%Y-%m-%d-%H-%M')+ '-' + ticker + '-'
	return strTime + type + '.csv'

def filePath(ticker):
	return os.path.join(os.getcwd(),ticker)+ os.sep 
	
def filePathRemote(ticker):
	return constants.SAVE_PATH_REMOTE + ticker + os.sep

def save_(df_, ticker, type, overwrite=False):
	#fileName = datetime.now().strftime('%Y-%m-%d-%H-%M-')+ str('result.csv')
	if overwrite:
		savePathName = os.path.join(filePath(ticker), (fileName(ticker,type,overwrite=True)))
		df_.to_csv(savePathName)
	else:
		savePathName = os.path.join(filePath(ticker), (fileName(ticker,type)))
		df_.to_csv(savePathName)	
		if type=='master':
			copyfile(savePathName,filePath(ticker)+'master.csv')
	
#use query to filter on values
# df.query('quoteLow < 20.5')
#dfm['quoteLow'].min(level=0) gives you the mins for each day.  how to get the time?
#dfm.groupby(level=0).quoteLow.idxmin() gives you index tuple for min per dayfor (k1, k2) in dfmg.quoteLow.idxmin():
#for name, group in dfm.groupby(level=0):
#     ...:     print name.month, name.day, group.quoteLow.idxmin()[1], group.quoteLow.min()
#     ...:
#for name, group in dfm.groupby(level=0):
#     ...:     print group.quoteLow.idxmin()[1], group.quoteLow.min()
#     ...:     d.append({'Time': group.quoteLow.idxmin()[1], 'Low': group.quoteLow.min()})
#pd.DataFrame(d)
#to get by hour df['hour'] = [ts.hour for ts in df.index]
#to get by min (in 10 min increments) df['mins'] = [ts.minute // 10 * 10 for ts in df.index]
#df.groupby(['hour','mins']).quoteHigh.max() where df is not mulitindex
#but these give you min/max over the entire data set.  results are skewed by long term trends
#i really want daily trends.  so need to normalize daily prices to some baseline.  quoteOpen?

#work with index of mulitindex base df
#get index:  
#In [48]: dfu.index.tolist()[0]
#Out[48]: (Timestamp('2016-11-28 00:00:00'), datetime.time(9, 43))

#pull the day out of the TS
#In [56]: dfu.index.tolist()[0][0].day
#Out[56]: 28

#Single index!!  get a column showing minutes
#dfu['minute']=dfu.index.minute

#join to columns
#daysStudy=pd.concat([daysOpen,daysHigh], join='outer', axis=1)
#daysStudy=pd.concat([daysStudy,days.low.min()], join='outer', axis=1)

#to get the open or high from the groupby
#daysOpen = days.open.head(1).to_frame(name='open')

#to drop a level of multi index
#daysOpen.index=daysOpen.index.droplevel(1)

#to get the time each day of the lowest low
#days.low.idxmin().apply(lambda x: x[1])

#to get a df with the lowest low of each day and its time
#daysLowStudy=pd.concat([days.low.idxmin().apply(lambda x: x[1]),days.low.min()],join='outer', axis=1)

#create a test frame
#testdf = pd.DataFrame(np.random.randn(64,1),index=pd.MultiIndex.from_product([ser1,ser2]))
#ser1,ser2 = pd.Series(range(1,9))/1000

#make index into columns
#testdf['new column name'] = testdf.index.get_level_values(1)

#mother load - to run the trials
#testdf['result1']=testdf.apply(lambda x: sl.trialOpenStrategy(df,goalOpen=x[0],stopLoss=x[1]),axis=1)

#correlation 
#dfds['day_result'].corr(dfds['result'])

#correlations:
#'day_result' (up/down) to sign of money result = 0.39
#'first' (which is first, the up or down in day) to 'day_result' = -.45
#
#get days on index and time on columns: dfmsc.unstack(1)
#get time on index and days on columns: dfmsc.unstack(0)  MOTHER LOAD
#sequence:
#1.  dfm=fetchMI
#2.  scale it.  dfms=sl.scale_(dfm)
#3.  select one column:  dfmsc=dfms['close']
#4.  unstack it by hour on column: dfmscu=dfmsc.unstack(1)
#5.  select the dates you want by iloc.  dfmscu3=dfmscu.iloc[0:3]
#6.  restack it. dfmsc3=dfmscu3.stack()
#7.  unstack it by date on column: dfmsc3u=dfmsc3.unstack(0)
#8.  plot:  dfmsc3u.plot()
#9. show plot.  plt.show()

# Observations about days of week:
# for strat of 1% harvest from open: best trade day is Friday.  25% of the good days are Friday
# worst day is Monday by far.  45% of the bad days are monday
# stop loss should be around -1.64%.  if less than that, then lose to many good days.  
# ave loss open to low on bad days is -3.66%
