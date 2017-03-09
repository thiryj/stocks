import stockLib
import datetime
import constants

class Position:
	'Common base class for all positions'
	count=0
	
	def __init__(self, ticker):
		self.ticker = 			ticker
		#self.openPrice = 		priceOpen
		#self.openDT = 			0
		#self.basis = 			0
		self.shares  = 			0
		#self.closePrice = 		0
		#self.closeDT = 		0
		#pos.high
		#self.harvest = 		0
		#self.stopLoss = 		0
		#self.trailStop = 		0
		#self.soldMethod = 		''
		self.open = 			False
		#self.trailStopInit
		self.trailStopActive = 	False
		Position.count += 1
		
	def displayCount(self):
		print "count is %d" % Position.count
		
	def display(self):
		print self.ticker.upper(), "| Open:", self.open, "| open Price:", self.openPrice
		
	def buy(self, 
			openPrice, 
			openDT = datetime.datetime.now(), 
			investment=constants.INVESTMENT, 
			cost=constants.COST_TRADE):
		'''opens a long position'''
		self.openPrice = openPrice
		self.openDT = openDT
		self.shares = (investment-cost)/float(openPrice)
		self.basis = investment
		self.high = openPrice
		self.proceeds = 0
		self.open = True
		
	def sell(	self, 
				closePrice, 
				closeDT = datetime.datetime.now(), 
				cost=constants.COST_TRADE, soldMethod='unk'):
		'''closes a long position'''
		self.closePrice = closePrice
		self.proceeds = self.shares * closePrice - cost 
		self.closeDT = closeDT
		self.shares = 0 
		self.profit = self.proceeds / float(self.basis) - 1
		self.soldMethod = soldMethod
		self.open = False
		return self.proceeds