#Main
#Written by John Thiry - 2015

#import trade modules
#import AUI_tts

#other imports
import csv
import collections
from datetime import datetime

#initialize magic numbers (constants)
FIRSTDATEINDEX=1406
LASTDATEINDEX=0
COST_TRADE=10
INVESTMENT=1000
GOAL_INCREASE_PERCENT = 0.035


#initialize local variables
priceFileName = 'data_price.csv'
testCaseFileName = 'data_testcase.csv'
resultsFileName = 'results.csv'
dateRows=[]   #list of tuples.  each list iten is a day
dateRowsAdj=[]  #same list but prices adjusted for stock splits
outputInner=[] #list comprised of [goal,result]
output=[] # list comprised of [investment,outputInner[]]
#fieldnames are Date,Open,High,Low,Close,Volume,Adj_Close

#define classes
class DayPrice(collections.namedtuple('DayPrice','Date, Open, High, Low, Close, Volume,CloseAdj' )):
	__slots__=()
	@property
	def adjustmentFactor(self):
		return (float(self.CloseAdj) / float(self.Close))
		
DayPriceAdj = collections.namedtuple('DayPriceAdj', 'Date, Open, High, Low, Close, Volume')

#run main loop
print ('starting main loop')

#read data from .csv
with open(priceFileName,'r') as priceFile:
	header = priceFile.readline()
	for dateRow in map(DayPrice._make, csv.reader(priceFile)):
		dateRows.append(dateRow)
	
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

#read and parse test case
#Q:  what is profit from buying and selling on last day of data?
#define functions
def profit(buy,sell,costTrade=COST_TRADE):
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
	investment=INVESTMENT):
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
	investment=INVESTMENT):
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
	investment=INVESTMENT):
	"""returns $ profit from trading over a period of days"""
	profitCum=0
	investmentCum=investment
	for day in dateRowsAdj[startDayIndex:endDayIndex:-1]:
		if dayOpenHighMetPercentGoal(day,goal):
			profitCum=profitCum+dayProfitFromPercentGoal(day,goal,investmentCum)
			investmentCum=investment + profitCum
	return(profitCum)	

#NOW: calc most profitable goal for given date range
def findBestGoal(
	startDayIndex=FIRSTDATEINDEX,
	endDayIndex=LASTDATEINDEX,
	investment=INVESTMENT):
	"""return the most profitable goal for given date range and starting investment amount"""
	bestGoal = 0
	bestProfit = 0
	beginRange = 0
	endRange = 101
	precision = 1000
	step = 1
	daysElapsed = (dateRowsAdj[endDayIndex].Date - dateRowsAdj[startDayIndex].Date).days
	output=[]
	#do first row of output.  this is the header containing goal percentages
	outputHdr = []
	outputHdr.append("")
	for goal in range(beginRange,endRange,step):
		outputHdr.append(goal*((endRange-1)/precision))
	output.insert(0,(("",outputHdr)))
	print(outputHdr)
	for inv in range(1000,10000,1000):
		investment = inv
		for goal in range(beginRange,endRange,step):
			goalPercent = goal/precision
			goalProfit = profitDateRangeCompounded(startDayIndex,endDayIndex,goalPercent,investment)
			outputInner.append([investment,[(goal*((endRange-1)/precision)),((goalProfit/investment)*100)]])
			outputInner.append(goalProfit)
			if goalProfit > bestProfit:
				bestProfit = goalProfit
				bestGoal = goal
		print(
		"best goal is " + "{0:.2f}".format(bestGoal*((endRange-1)/precision))+"%" + 
		"\nWith a cumulative profit of $" + "{0:.2f}".format(bestProfit) + 
		"\nWhich is a cumulative percentage increase of " + "{0:.2f}".format((bestProfit/investment)*100)+"% over " + str(daysElapsed)+ " days" +
		"\nOn the $" + str(investment) + " investment" +
		"\nWhich is an annualized ROI of " + "{0:.2f}".format(((bestProfit/investment)/(daysElapsed/365))*100)+"%"
		)
		writeResults(output)
	#output results
	
#write data to .csv
def writeResults(output):
	with open(resultsFileName,'w', newline='') as resultsFile:
		resultsWriter = csv.writer(resultsFile,delimiter=',')
		#write header
		#resultsWriter.writerow(["Investment","Goal","Cum% Increase"])
		for resultsRow in output:
			resultsWriter.writerow(resultsRow)
		
	





        