#!/usr/bin/env python
# coding: utf-8
"""
User interface module
"""

import streamlit as st
from tasks import (
    grab,
    grab2,
    grab_description,
    get_last_data,
    update_cv,
    get_last_data_with_metric,
    get_cv_data,
    add_cv,
    get_empty_descriptions_data,
    del_last_data,
    update_db_df,
    get_active_searches,
    init_db,
    check_db,
    process_description,
    process_resumes,
    vacancy_matching,
    app, get_cv_skills)



def display_data_tab():
    """
        Display data tab
    """
    st.markdown('## Assistant for job search')

    with st.spinner("Loading last data..."):
        resume_id = st.session_state.get('resume_id', None)
        data = get_last_data_with_metric(resume_id=resume_id)
        columns = data.columns
        view_cols = st.multiselect('Columns', columns)
        st.dataframe(data[view_cols],
                 column_config={
                     "link": st.column_config.LinkColumn(
                         "link", display_text="🌐"
                     ),
                 },
                 )

def display_cv_tab():
    """
        Display cv tab
    """
    st.markdown('## CV')

    with st.spinner("Loading last data..."):
        data = get_cv_data()

        if data.size == 0:
            txt = st.text_area('CV text:', value='')
            if st.button('+'):
                add_cv(txt)
                st.rerun()

        else:
            resume_ids = data['resume_id']

            resume_id = st.session_state.get('resume_id',None)
            print(f'Found Resume id = {resume_id}')

            #find index for resume
            if resume_id:
                idx = data[data['resume_id'] == resume_id].index[0]
            else:
                idx = 0
            new_resume_id = st.selectbox('Select CV:', resume_ids, index=idx)

            txt = data[data['resume_id'] == new_resume_id]['resume'][0]
            st.session_state['resume_id'] = new_resume_id

            new_txt = st.text_area('CV:', txt)

            # show list of skills
            skills = get_cv_skills(new_resume_id)
            # show skills list
            if len(skills) > 0:
                st.write('Skills:')
                st.dataframe(skills)

            # analyse button
            if st.button('Analyse CV'):
                process_resumes.delay(data.to_json(orient='records'))


            # vacancy matching button
            if st.button('Run vacancy matching'):
                vacancy_matching.delay()

            # save button
            if st.button('✅ '):
                update_cv(new_resume_id, new_txt)
            # update button
            if st.button('+'):
                add_cv(txt)
                st.rerun()


def display_settings_tab():
    """
        Display settings tab
    """
    with st.spinner("Loading active searches..."):
        df = get_active_searches()

    i = app.control.inspect()

    st.markdown('### Active searches')
    edited_df = st.data_editor(df, num_rows="dynamic")

    # get active jobs status
    if len(i.active().keys()) > 0:
        jobs = []
        for worker in i.active().keys():
            tasks = i.active()[worker]
            jobs += [
        {
            'id':task['id'],
            'name':task['name'],
            'status': app.AsyncResult(task['id']).info['done']
        } for task in tasks]
    else:
        jobs = []

    st.write('Active tasks:')

    # display statuses
    for j in jobs:
        st.write(j['name'],'-',j['status'],'%')

    if st.button('▶️  Get vacancies'):
        grab.delay(edited_df.to_json(orient='records'))
    if st.button('▶️  Get descriptions'):
        grab_description.delay(edited_df.to_json(orient='records'))
    if st.button('▶️  Test job'):
        grab2.delay(edited_df.to_json(orient='records'))
    if st.button('▶️  parse vacancies skills'):
        with st.spinner("Loading last data..."):
            data = get_empty_descriptions_data()
            data = data[['vac_id', 'site', 'vac_descr']]
        process_description.delay(data.to_json(orient='records'))

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

resume_id = st.session_state.get('resume_id', 0)

tab_settings,tab_data, tab_count_by, tab_cv = st.tabs([
    'Settings',
    'Data',
    'Vacancies count by company',
    'CV',
])

with st.spinner("Check db..."):
    check_db()
# MAIN WINDOW
with tab_data:
    display_data_tab()

with tab_count_by:
    display_count_by_tab()

with tab_settings:
    display_settings_tab()

with tab_cv:
    display_cv_tab()
