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


#loading dataset
@st.cache
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

#Building the Dashboard
add_sidebar = st.sidebar.selectbox('Aggregate or Individual Video', ('Aggregate Metrics','Individual Video Analysis'))
