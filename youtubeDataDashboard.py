# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 09:46:50 2022

@author: farhan
"""

#import libraries
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import datetime

#defining functions
def styleNegative(v,props=''):
    '''For Styling negative values in dataframe'''
    try:
        return props if v<0 else None
    except:
        pass
def stylePositive(v,props=''):
    '''For Styling negative values in dataframe'''
    try:
        return props if v>0 else None
    except:
        pass
def audience_simple(country):
    """Show top countries"""
    if country=='US':
        return 'USA'
    elif country=='IN':
        return 'India'
    elif country=='BD':
        return 'Bangladesh'
    else:
        return 'Other'
#loading dataset
#@st.cache

def loadData():
    aggregatedMetricsByVideo=pd.read_csv('Aggregated_Metrics_By_Video.csv').iloc[1:,:]
    #redoing the columns of aggregatedMetricsByVideo
    aggregatedMetricsByVideo.columns=['Video','Video title','Video publish time','Comments added','Shares','Dislikes','Likes',
                          'Subscribers lost','Subscribers gained','RPM(USD)','CPM(USD)','Average % viewed','Average view duration',
                          'Views','Watch time (hours)','Subscribers','Your estimated revenue (USD)','Impressions','Impressions ctr(%)']
    aggregatedMetricsByVideo['Video publish time']=pd.to_datetime(aggregatedMetricsByVideo['Video publish time']) #converting the date time value from string
    aggregatedMetricsByVideo['Average view duration']=aggregatedMetricsByVideo['Average view duration'].apply(lambda x: datetime.strptime(x,'%H:%M:%S')) #converting the field
    aggregatedMetricsByVideo['Avg_duration_sec'] = aggregatedMetricsByVideo['Average view duration'].apply(lambda x: x.second + x.minute*60 + x.hour*3600) #re caclualting the average view duration
    aggregatedMetricsByVideo['Engagement_ratio'] =  (aggregatedMetricsByVideo['Comments added'] + aggregatedMetricsByVideo['Shares'] +aggregatedMetricsByVideo['Dislikes'] + aggregatedMetricsByVideo['Likes']) /aggregatedMetricsByVideo.Views
    aggregatedMetricsByVideo['Views / sub gained'] = aggregatedMetricsByVideo['Views'] / aggregatedMetricsByVideo['Subscribers gained']
    aggregatedMetricsByVideo.sort_values('Video publish time', ascending = False, inplace = True) 
    
    aggregatedMetricsByCountrySubscriber=pd.read_csv('Aggregated_Metrics_By_Country_And_Subscriber_Status.csv').iloc[1:,:]
    commentData=pd.read_csv('All_Comments_Final.csv').iloc[1:,:]
    timeData=pd.read_csv('Video_Performance_Over_Time.csv').iloc[1:,:]
    timeData['Date'] = pd.to_datetime(timeData['Date'])
    return aggregatedMetricsByVideo,aggregatedMetricsByCountrySubscriber,timeData,commentData

#creating dataset from the function
aggregatedMetricsByVideo,aggregatedMetricsByCountrySubscriber,timeData,commentData=loadData()

#Engineering Data
aggregatedMetricsByVideoCopy=aggregatedMetricsByVideo.copy()
metricDate12months=aggregatedMetricsByVideoCopy['Video publish time'].max()-pd.DateOffset(months=12)
median_aggregatedMetricsByVideo=aggregatedMetricsByVideoCopy[aggregatedMetricsByVideoCopy['Video publish time'] >= metricDate12months].median()

#Numeric columns
numericColumns = np.array((aggregatedMetricsByVideoCopy.dtypes == 'float64') | (aggregatedMetricsByVideoCopy.dtypes == 'int64'))
aggregatedMetricsByVideoCopy.iloc[:,numericColumns] = (aggregatedMetricsByVideoCopy.iloc[:,numericColumns] - median_aggregatedMetricsByVideo).div(median_aggregatedMetricsByVideo)

#merge daily data with publish data to get delta
timeDataFrameCopy=pd.merge(timeData, aggregatedMetricsByVideo.loc[:,['Video','Video publish time']], left_on ='External Video ID', right_on = 'Video')
timeDataFrameCopy['days_published'] = (timeDataFrameCopy['Date'] - timeDataFrameCopy['Video publish time']).dt.days

#get only last 12 months of data
date_12mo = aggregatedMetricsByVideo['Video publish time'].max() - pd.DateOffset(months =12)
dataframeTimeandYear = timeDataFrameCopy[timeDataFrameCopy['Video publish time'] >= date_12mo]

#get daily view data(first 30), median and percentiles
views_days = pd.pivot_table(dataframeTimeandYear,index= 'days_published',values ='Views', aggfunc = [np.mean,np.median,lambda x: np.percentile(x, 80),lambda x: np.percentile(x, 20)]).reset_index()
views_days.columns = ['days_published','mean_views','median_views','80pct_views','20pct_views']
views_days = views_days[views_days['days_published'].between(0,30)]
views_cumulative = views_days.loc[:,['days_published','median_views','80pct_views','20pct_views']] 
views_cumulative.loc[:,['median_views','80pct_views','20pct_views']] = views_cumulative.loc[:,['median_views','80pct_views','20pct_views']].cumsum()


#Building the Dashboard
add_sidebar = st.sidebar.selectbox('Aggregate or Individual Video', ('Aggregate Metrics','Individual Video Analysis'))

#picture
if add_sidebar=='Aggregate Metrics':
        aggregatedMetricsByVideoMetrics = aggregatedMetricsByVideo[['Video publish time','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed','Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
        metricDate6months = aggregatedMetricsByVideoMetrics['Video publish time'].max() - pd.DateOffset(months =6)
        metricDate12months= aggregatedMetricsByVideoMetrics['Video publish time'].max() - pd.DateOffset(months =12)
        metricMedians6months = aggregatedMetricsByVideoMetrics[aggregatedMetricsByVideoMetrics['Video publish time'] >= metricDate6months].median()
        metricMedians12months = aggregatedMetricsByVideoMetrics[aggregatedMetricsByVideoMetrics['Video publish time'] >= metricDate12months].median()   
        col1, col2, col3, col4, col5 = st.columns(5)
        columns = [col1, col2, col3, col4, col5]
        count=0;
        for i in metricMedians6months.index:
            with columns[count]:
                delta = (metricMedians6months[i] - metricMedians12months[i])/metricMedians12months[i]
                st.metric(label= i, value = round(metricMedians6months[i],1), delta = "{:.2%}".format(delta))
                count += 1
                if count >= 5:
                    count = 0
        aggregatedMetricsByVideoCopy['Publish_date'] = aggregatedMetricsByVideoCopy['Video publish time'].apply(lambda x: x.date())
        aggregatedMetricsByVideoCopyFinal = aggregatedMetricsByVideoCopy.loc[:,['Video title','Publish_date','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed','Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
        aggregatedMetricsByVideoNumeric1st=aggregatedMetricsByVideoCopyFinal.median().index.tolist()
        dataframetopct={}
        for i in  aggregatedMetricsByVideoNumeric1st:
            dataframetopct[i]='{:.1%}'.format
        st.dataframe(aggregatedMetricsByVideoCopyFinal.style.hide().applymap(styleNegative, props='color:red;').applymap(stylePositive, props='color:green;').format(dataframetopct))
        
if add_sidebar =='Individual Video Analysis':
    videos=tuple(aggregatedMetricsByVideo['Video title'])
    video_selected=st.selectbox('Pick a Video', videos)
    
    aggregatedFiltered=aggregatedMetricsByVideo[aggregatedMetricsByVideo['Video title']==video_selected]
    aggregatedSubFiltered=aggregatedMetricsByCountrySubscriber[aggregatedMetricsByCountrySubscriber['Video Title']==video_selected]
    aggregatedSubFiltered['Country'] = aggregatedSubFiltered['Country Code'].apply(audience_simple)
    aggregatedSubFiltered.sort_values('Is Subscribed',inplace=True)
    
    fig = px.bar(aggregatedSubFiltered, x ='Views', y='Is Subscribed', color ='Country', orientation ='h')
    #order axis 
    st.plotly_chart(fig)
       
    aggregatedTimeFiltered = timeDataFrameCopy[timeDataFrameCopy['Video Title'] == video_selected]
    first_30 = aggregatedTimeFiltered[aggregatedTimeFiltered['days_published'].between(0,30)]
    first_30 = first_30.sort_values('days_published')
    
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['20pct_views'],
                    mode='lines',
                    name='20th percentile', line=dict(color='purple', dash ='dash')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['median_views'],
                        mode='lines',
                        name='50th percentile', line=dict(color='black', dash ='dash')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['80pct_views'],
                        mode='lines', 
                        name='80th percentile', line=dict(color='royalblue', dash ='dash')))
    fig2.add_trace(go.Scatter(x=first_30['days_published'], y=first_30['Views'].cumsum(),
                        mode='lines', 
                        name='Current Video' ,line=dict(color='firebrick',width=8)))
        
    fig2.update_layout(title='View comparison first 30 days',
                   xaxis_title='Days Since Published',
                   yaxis_title='Cumulative views')
    
    st.plotly_chart(fig2)
        
    
    