#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import streamlit as st
import time

con = 'postgresql://postgres:postgres@postgres:5432/public'


def get_active_searches():
    df = pd.read_sql('select * from searches',con)
    return df

def update_db_df(edited_df):
    edited_df.to_sql('searches',con,index=False,if_exists='replace')

st.title('Job finder')
with st.sidebar:

    with st.spinner("Loading..."):
        df = get_active_searches()
    st.markdown('### Active searches')
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button('Save'):
        update_db_df(edited_df)

st.markdown('## Assistant for job search')

opt = st.selectbox('Select a search',edited_df['request'])

st.link_button('Monitor',f'http://localhost:3000/public-dashboards/91fc50641ff34fb18756b5a8d1b3f60b')
st.link_button('Analysis',f'http://localhost:3000/public-dashboards/07479326488e4bab8a8b237656b46863')


