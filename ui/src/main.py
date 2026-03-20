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
from tasks import *


st.title('Job finder')

grabber_result_id = st.session_state.get('result_id',None)
grabber_status = st.session_state.get('get_vacancies_status',None)

st.write(str(grabber_result_id))

st.write(str(grabber_status))
with st.sidebar:

    with st.spinner("Loading..."):
        df = get_active_searches()
    st.markdown('### Active searches')
    edited_df = st.data_editor(df, num_rows="dynamic")


    if grabber_result_id:
        res = app.AsyncResult(grabber_result_id)
        st.write(res.state)
        # if done
        if res.state=='SUCCESS':
            st.session_state['get_vacancies_status'] = 'Vacancy last manually update: '+str(datetime.datetime.now())
            st.session_state['result_id'] = None
            res.get()
        # if task in progress or waiting
        elif res.state in ('PROGRESS','PENDING', 'STARTED', 'RETRY'):
            if res.state in ('PROGRESS',):
                st.progress(res.info.get('done', 0))

            if st.button('⏹️  stop grabber'):
                res = app.AsyncResult(grabber_result_id)
                res.revoke(terminate=True)
                res.forget()
                st.session_state['result_id'] = None
        #some error
        else:
            st.session_state['result_id'] = None
            st.markdown('# **Error grabbing vacancies**')
    else:
        if st.button('▶️  Get vacancies'):
            result = grab.delay(edited_df.to_json(orient='records'))
            st.session_state.result_id = result.id

    # print last update time
    if st.session_state.get('get_vacancies_status'):
        st.write(st.session_state.get('get_vacancies_status'))

    if st.button('✅ Save'):
        update_db_df(edited_df)

st.markdown('## Assistant for job search')

opt = st.selectbox('Select a search',edited_df['request'])



st.link_button('Grafana Monitor&Analysis',f'http://localhost:3000')

time.sleep(1)
st.rerun()
