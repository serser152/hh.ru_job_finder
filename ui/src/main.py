#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import streamlit as st
import time
import pandas as pd
import json
from time import sleep
import datetime
import requests


con = 'postgresql://postgres:postgres@postgres:5432/public'


def get_active_searches():
    df = pd.read_sql('select * from searches',con)
    return df

def update_db_df(edited_df):
    edited_df.to_sql('searches',con,index=False,if_exists='replace')




def grab_hh(phone, password, request):

    con = 'postgresql://postgres:postgres@postgres:5432/public'
    res = requests.post('http://hh_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,

                            "password": password,
                          "request": request
                        })

    max_try = 5

    while not res.ok:
        if max_try == 0:
            raise Exception('API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://hh_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,

                            "password": password,
                          "request": request
                        })
        max_try -= 1

    d=res.json()
    df = pd.DataFrame(json.loads(d))
    df['dt']=pd.to_datetime(df.dt, unit='ms')

    df.to_sql('hh_ds',con=con, if_exists='append',index=False)


    # grab new vac_ids
    df2 = pd.read_sql('''select vac_id from hh_ds_last_values where vac_id not in (select vac_id from vacancy_descriptions)''', con=con)

    vac_ids = df2.vac_id.to_list()

    res = requests.post('http://hh_grabber:8000/get_vacancy_descriptions',
                    json={
                      "phone": phone,

                        "password": password,
                      "vacancy_ids": vac_ids
                    })

    max_try = 5
    while not res.ok:
        if max_try == 0:
            raise Exception('Request vac desriptions: API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://hh_grabber:8000/get_vacancy_descriptions',
                        json={
                          "phone": phone,

                            "password": password,
                          "vacancy_ids": vac_ids
                        })
        max_try -= 1


    d=res.json()
    df = pd.DataFrame(json.loads(d))

    df.to_sql('vacancy_descriptions',con=con, if_exists='append', index=False)


def grab(df):
    print('grab job started')
    for i,row in df.iterrows():
        grab_hh(row.phone, row.password, row.request)

st.title('Job finder')
with st.sidebar:

    with st.spinner("Loading..."):
        df = get_active_searches()
    st.markdown('### Active searches')
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button('▶️  Get vacancies'):
        grab(edited_df)

    if st.button('✅ Save'):
        update_db_df(edited_df)

st.markdown('## Assistant for job search')

opt = st.selectbox('Select a search',edited_df['request'])

st.link_button('Monitor',f'http://localhost:3000/public-dashboards/91fc50641ff34fb18756b5a8d1b3f60b')
st.link_button('Analysis',f'http://localhost:3000/public-dashboards/07479326488e4bab8a8b237656b46863')


