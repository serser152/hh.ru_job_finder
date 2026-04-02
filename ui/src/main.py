#!/usr/bin/env python
# coding: utf-8
"""
User interface module
"""

import time
import datetime
import streamlit as st
from tasks import (
    grab,
    get_last_data,
    get_empty_descriptions_data,
    del_last_data,
    update_db_df,
    get_active_searches,
    init_db,
    check_db,
    process_description,
    app)


def display_data_tab():
    '''
        Display data tab
    '''
    st.markdown('## Assistant for job search')

    with st.spinner("Loading last data..."):
        data = get_last_data()
        columns = data.columns
        view_cols = st.multiselect('Columns', columns)
        st.dataframe(data[view_cols],
                 column_config={
                     "link": st.column_config.LinkColumn(
                         "link", display_text="🌐"
                     ),
                 },
                 )


def display_settings_tab(result_id):
    """
        Display settings tab
    """
    with st.spinner("Loading active searches..."):
        df = get_active_searches()

    st.markdown('### Active searches')
    edited_df = st.data_editor(df, num_rows="dynamic")

    try:
        if result_id:
            res = app.AsyncResult(result_id)

            print('res=', str(res))
            print('res.type=', type(res))

            # if done
            if res.state=='SUCCESS':
                st.session_state['get_vacancies_status'] = 'Vacancy last manually update: '\
                                                           + str(datetime.datetime.now())
                st.session_state['result_id'] = None
                res.get()
            # if task in progress or waiting
            elif res.state in ('PROGRESS', 'PENDING', 'STARTED', 'RETRY'):
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
                print('Created task:', result.id)
                st.session_state.result_id = result.id
                st.rerun()

    except Exception as e:
        print(e)
        if st.button('▶️  Get vacancies'):
            result = grab.delay(edited_df.to_json(orient='records'))
            print('Created task:', result.id)
            st.session_state.result_id = result.id
            st.rerun()

    if st.button('▶️  parse vacancy'):
        with st.spinner("Loading last data..."):
            data = get_empty_descriptions_data()
            data = data.head(100)
        result = process_description.delay(data.to_json(orient='records'))
        print('Created task:', result.id)
        with st.spinner("processing description..."):
            res = app.AsyncResult(result.id)
            while res.state == 'PROGRESS':
                p = res.info.get('done', 0)
                print(f'DONE = {p}%')
                time.sleep(10)
                res = app.AsyncResult(result.id)

    # print last update time
    if st.session_state.get('get_vacancies_status'):
        st.write(st.session_state.get('get_vacancies_status'))
    if st.button('🗑️ remove last load'):
        with st.spinner('deleting in progress'):
            del_last_data()
    if st.button('✅ Save'):
        with st.spinner('Saving'):
            update_db_df(edited_df)
    if st.button(' Initialize DB'):
        with st.spinner('🧨 Initializing DB'):
            init_db()

    st.link_button('Grafana Monitor&Analysis', 'http://localhost:3000')


def display_count_by_tab():
    """
        Display count by tab
    """
    with st.spinner("Loading last data..."):
        data = get_last_data()
    columns = data.columns
    agg_col = st.selectbox('Count vacancies by:',columns, index=0)
    data2 = data.groupby(agg_col).agg({'vac_id':'count'}).reset_index()
    data3 = data2.sort_values('vac_id',ascending=False).head(10)
    st.bar_chart(data3,x=agg_col,y='vac_id', horizontal=True, sort='-vac_id')

st.title('Job finder')

grabber_result_id = st.session_state.get('result_id',None)
print('Found resultid = ', grabber_result_id)
grabber_status = st.session_state.get('get_vacancies_status',None)

tab_settings,tab_data, tab_count_by = st.tabs(['Settings','Data','Vacancies count by company'])
with st.spinner("Check db..."):
    check_db()
# MAIN WINDOW
with tab_data:
    display_data_tab()

with tab_count_by:
    display_count_by_tab()

with tab_settings:
    display_settings_tab(grabber_result_id)

#time.sleep(600)
#st.rerun()
