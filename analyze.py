import giq
import stock_lib
import datetime

#initialize local variables
ticker = 'UBIO'
interval = 120
lookback_days = 2
highQuotes=[]
quotes=[]
day_=[] # array of all the intraday quotes in single day
days=[] # array of all days in a result set
day21=[]
daysIncluded=[] #array of days included in result
quotesSorted=[]
quotesSortedDay=[]

#quotes is an array of intraday price data
#each record in array is a quote
#quote is {'quoteDT':dt,'quoteOpen': open_,'quoteHigh': high,'quoteLow':low,'quoteClose':close}
#dt format is "yyyy-mm-dd hh:mm:ss"

#returns string? of quotes 
q = giq.GoogleIntradayQuote_(ticker,interval,lookback_days)

#parse q into array of quotes
quotes=q.dataList
print len(quotes)
for quote in quotes:
	if quote['quoteDT'].day==21:
		print quote['quoteClose']
		
#finds the largest High in a day
high= max(quote['quoteHigh']for quote in quotes if quote['quoteDT'].day==23)
print high
#find lowest low in a day
low= min(quote['quoteHigh']for quote in quotes if quote['quoteDT'].day==23)
print low
print stock_lib.profit(low*1000,high*1000)
print stock_lib.profitPercent(low*1000,high*1000)

#parse quotes into days
for quote in quotes:
        if quote['quoteDT'].date()==datetime.date(2016,11,21):
                day21.append(quote)
        if quote['quoteDT'].date() in daysIncluded:
                pass
        else:
                daysIncluded.append(quote['quoteDT'].date())
print daysIncluded #print out which days in data

#make an array of days containing the array of quotes for that day
for thisDay in daysIncluded:
        quotesSortedDay=[]
        for quote in quotes:
                if quote['quoteDT'].date()==thisDay:
                        #quotesSortedDay.append([quote['quoteDT'].isoformat(),quote['quoteOpen'],quote['quoteHigh'],quote['quoteLow'],quote['quoteClose']])
                        quotesSortedDay.append([quote['quoteDT'].isoformat(),quote['quoteClose']])
        quotesSorted.append(quotesSortedDay)

#populate master db of data.  don't allow dups.  db is csv file
stock_lib.writeResults(quotesSorted)
