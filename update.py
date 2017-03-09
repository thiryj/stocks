#import giq
import stockLib as sl
import datetime
import pytz
import pandas as pd
from shutil import copyfile
import pdb

import time
t0 = time.clock()

from pandas.tseries.offsets import BDay
import numpy as np
import datetime as dt
from copy import copy
import warnings
warnings.filterwarnings('ignore',category=pd.io.pytables.PerformanceWarning)

#initialize local variables
COLS = ['DT', 'open', 'high', 'low', 'close']
TIMESTAMP_INDEX_NAME = 'DT'
masterFilePathLocal = r'c:\dev\projects\stocks\\'
masterFilePathRemote = r'D:\Dropbox\JohnThiryFamilyShare\Financial\stocks\\'
masterFileName = 'master.csv'
bestFileName = 'best.csv'
interval = 60
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
#quote is {'DT':dt,'open': open_,'high': high,'low':low,'close':close}
#dt format is "yyyy-mm-dd hh:mm:ss"

# ================================================================== #
# filepath management

project_dir = r'insert_your_project_directory' 
price_path = project_dir + r'Stock_Price_Data\\'
SAVE_PATH_LOCAL = 'd:\dev\projects\stocks\\'

# ================================================================== #
apikey = '8f482448cfcb7259ebc2f2efdd719695'

def	persistMaster(df_, ticker):
	masterFile = sl.filePath(ticker) + sl.fileName(ticker,masterFileName)
	df_.to_csv(masterFile)
	
def fetchMaster(ticker):
	dtypes = {0:datetime}
	masterFile = sl.filePath(ticker) + 'master.csv'
	dfm_= pd.read_csv(masterFile, index_col=0)
	dfm_.index=pd.to_datetime(dfm_.index)
	dfm_.dropna()
	return dfm_
	
def fetchMI(ticker):
	return multiInd(fetchMaster(ticker)).dropna()

def timeForPlotly(df):
	# change time index to seconds
	df[:,0]=[(datetime.strptime(str(d),'%H:%M:%S.%f')).total_seconds() for d in df[:,0]]
	return df
	
def multiInd(df__):
	#multi index
	df__.index = pd.MultiIndex.from_arrays([df__.index.date, df__.index.time], names=['Date','Time'])
	#return pd.MultiIndex.from_arrays([df_.index, df_.index.time], names=['Date','Time'])
	return df__
	
def concatDedup(df1_,df2_):
	#concat rows then dedup master
	df1_= pd.concat([df1_,df2_])
	df1_=df1_[~df1_.index.duplicated(keep='last')]
	return df1_

# def getUpdateG(ticker='UBIO', interval=60, lookback_days=2):
	# q = giq.GoogleIntradayQuote_(ticker,interval,lookback_days)
	# df = pd.DataFrame(q.dataList)
	# df = df.reindex(columns=COLS)
	# df.set_index('DT',inplace=True)
	# #df.index = pd.MultiIndex.from_arrays([df.index, df.index.time], names=['Date','Time'])
	# #print df.head(4)
	# return df
	
def dailyUpdate(ticker,lb=2):
	masterFile = sl.filePath(ticker) + masterFileName
	#get update
	dfu_ = getUpdate(ticker, lb=lb)
	#concat update to master, dedup, sort
	dfm_ = pd.read_csv(masterFile, index_col=0)
	dfm_.index=pd.to_datetime(dfm_.index)
	dfm_ = concatDedup(dfm_,dfu_)
	dfms = dfm_.sort_index()
	#persist new master to dropbox csv
	masterFileRemote = sl.filePathRemote(ticker) + sl.fileName(ticker,'master')
	dfms.to_csv(masterFileRemote)
	#copy dropbox master to local master
	copyfile(masterFileRemote, masterFile)
	#updateBest(ticker)

	
def construct_barChart_url(sym, start_date, freq, api_key=apikey):
    '''Function to construct barchart api url'''
    
    url = 'http://marketdata.websol.barchart.com/getHistory.csv?' +\
            'key={}&symbol={}&type={}&startDate={}'.format(api_key, sym, freq, start_date)
    return url
	
def barchartsToGoogle(df_):
	'''Function to modify dataframe to previous Google format'''
	#rename index
	df_.index.names=[TIMESTAMP_INDEX_NAME]
	#drop columns
	df_=df_.drop(df_.columns[[0,1,6]],axis=1)
	return df_
	
def lookBack(lookback_days=1):
	'''Function to return a yahoo start datetime given number of days from now'''
	#pseduo: start = now()-lookback_days
	start=(datetime.datetime.today()-datetime.timedelta(lookback_days)).strftime('%Y%m%d000000')
	return start

def getUpdate(sym='UBIO',lb=1):
	'''Function to Retrieve <= 3 months of minute data for SP500 components'''
	# This is the required format for datetimes to access the API
	start = lookBack(lb)
    #end = d
	freq = 'minutes'
	#prices = {}
	#symbol_count = len(syms)
	#N = copy(symbol_count)
	try:
		#for i, sym in enumerate(syms, start=1):
		api_url = construct_barChart_url(sym, start, freq, api_key=apikey)
		try:
			csvfile = pd.read_csv(api_url, parse_dates=['timestamp'])
			csvfile.set_index('timestamp', inplace=True)
			#pdb.set_trace()
			csvfile.index = csvfile.index.tz_localize('utc').tz_convert('US/Eastern')
			csvfile.index = csvfile.index.tz_localize(None)
			csvfile=barchartsToGoogle(csvfile)
			csvfile.dropna()
			#prices[sym] = csvfile
		except:
			#continue
			pass
			#N -= 1
			#pct_total_left = (N/symbol_count)
			#print('{}..[done] | {} of {} symbols collected | percent remaining: {:>.2%}'.format(\
			#sym, i, symbol_count, pct_total_left)) 
	except Exception as e:
		print(e)
	finally:
		pass
    #px = pd.Panel.from_dict(prices)
	#px = pd.DataFrame.from_dict(prices)
    # convert timestamps to EST
    #px.major_axis = px.major_axis.tz_localize('utc').tz_convert('US/Eastern')
	return csvfile
	
def updateBest(ticker):
	'''record last day's best strat in csv file'''
	#get best strat for ticker
	#fetch df for ticker, then run strat trials then best.head(1)
	bestStrat = sl.best(sl.runTrials(fetchMI('ubio')),results=1)
	#get a column with date of last time period in trials
	bestStrat['date'] = dt.datetime.now().date()
	#turn that column into the index
	bestStratTS=bestStrat.set_index(pd.DatetimeIndex(bestStrat['date']))
	#drop the temp date column.  better way to do this?  likely.
	bestStratTS = bestStratTS.drop('date',1)
	#bestStratTS
	#save to csv - concat dedup to existing file
	bestFile = sl.filePath(ticker) + bestFileName
	#concat update to best, dedup, sort
	dfm_ = pd.read_csv(bestFile, index_col=0)
	dfm_.index=pd.to_datetime(dfm_.index)
	dfm_ = concatDedup(dfm_,bestStratTS)
	dfms = dfm_.sort_index()
	#persist new best to dropbox csv
	bestFileRemote = sl.filePathRemote(ticker) + sl.fileName(ticker,'best')
	dfms.to_csv(bestFileRemote)
	#copy dropbox best to local best
	copyfile(bestFileRemote, bestFile)
	