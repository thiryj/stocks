import numpy as np
import pandas as pd
from update import getUpdate as gu

import pandas_datareader.data as web
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
from plotly.tools import FigureFactory as FF
from datetime import datetime

plotlyUN = 'thiryj'
plotlyAPI = 'YkbacEy2A8EdXtfJCRwM'

#credentials
plotly.tools.set_credentials_file(username=plotlyUN, api_key = plotlyAPI)

#get some data 
#df5 = web.DataReader("UBIO", 'yahoo', datetime(2008, 8, 15), datetime(2008, 10, 15))
def studyUpdate(days=1):
	return(gu(lookback_days=days))
	
def plotHist(df_):
	data = [go.Histogram(y=df_[:])]
	py.plot(data,filename='ubio-low-histogram')

#2D plot on plotly
def plot2D(days=1):
	df=studyUpdate(days)
	fig = FF.create_ohlc(df.quoteOpen, df.quoteHigh, df.quoteLow, df.quoteClose, dates=df.index)
	py.iplot(fig, filename='ubio-update-ohlc')
	
#3d plot on plotly
def plot3D():
#get data and do some stuff
	url_csv = 'http://www.stat.ubc.ca/~jenny/notOcto/STAT545A/examples/gapminder/data/gapminderDataFiveYear.txt'

	df = pd.read_csv(url_csv, sep='\t')
	df.head()

	countries = ['China', 'India', 'United States', 'Bangladesh', 'South Africa']
	fill_colors = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854']
	gf = df.groupby('country')

	data = []

	for country, fill_color in zip(countries[::-1], fill_colors):
		group = gf.get_group(country)
		years = group['year'].tolist()
		length = len(years)
		country_coords = [country] * length
		pop = group['pop'].tolist()
		zeros = [0] * length
		data.append(dict(
			type='scatter3d',
			mode='lines',
			# year loop: in incr. order then in decr. order then years[0]
			x=years + years[::-1] + [years[0]],  
			y=country_coords * 2 + [country_coords[0]],
			z=pop + zeros + [pop[0]],
			name='',
			# add a surface axis ('1' refers to axes[1] i.e. the y-axis)
			surfaceaxis=1, 
			surfacecolor=fill_color,
			line=dict(
				color='black',
				width=2
			),
		))
#define layout dict
	layout = dict(
		title='my cool plot title',
		showlegend=False,
		scene=dict(
			xaxis=dict(title='time'),
			yaxis=dict(title='days'),
			zaxis=dict(title='price'),
			camera=dict(
				eye=dict(x=-1.7, y=-1.7, z=0.5)
			)
		)
	)
#build fig and call plot
	fig = dict(data=data, layout=layout)
	url = py.plot(fig, validate=False, filename='filled-3d-lines')