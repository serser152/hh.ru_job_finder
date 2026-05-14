#!/usr/bin/env python
# coding: utf-8
"""
User interface module
"""
import pandas as pd
import streamlit as st
from tasks import (
    grab,
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
    respond_vacancies,
    get_filter_df,
    update_filter_df,
    app, get_cv_skills)


def display_data_tab():
    """
        Display data tab
    """
    with st.spinner("Загружаем последние скачанные вакансии..."):
        data = get_last_data_with_metric(resume_id=st.session_state.get('resume_id', None))
        filter_df = get_filter_df()
        filter_txt = '\n'.join(filter_df.company_mask.to_list())
        # filter masks
        new_filter_txt = st.text_area(
            'Фильтр(в каждой строке часть имени нежелательной компании):',
            filter_txt
        )

        company_mask_list = new_filter_txt.split('\n')
        new_filter_df = pd.DataFrame(company_mask_list, columns=['company_mask'])
        # update button
        if st.button('✅ Сохранить фильтр'):
            update_filter_df(edited_df=new_filter_df)

        # company filter
        for i in company_mask_list:
            data = data[~data['vac_company'].str.contains(i)]
        columns = data.columns

        # slider metric
        min_metric = st.slider('Соответствие резюме', 0, 100, 90)
        data2 = data[data['metric'] >= min_metric].sort_values('metric',ascending=False)
        view_cols = st.multiselect('Columns', columns,
                                   default=['link','vac_company','title','status','metric'])
        st.dataframe(data2[view_cols], width='content', height='auto',
                 column_config={
                     "link": st.column_config.LinkColumn(
                         "link", display_text="🌐"
                     ),
                 },
                 )

        if st.button('Откликнуться на вакансии из таблицы'):
            data3 = data2[data2['status'] == 'Откликнуться']
            df = get_active_searches()
            data3 = data3.merge(df, on='site')
            respond_vacancies.delay(data3.to_json(orient='records'))


def display_cv_tab():
    """
        Display cv tab
    """
    st.markdown('## Резюме')

    with st.spinner("Грузим данные..."):
        data = get_cv_data()

        if data.size == 0:
            txt = st.text_area('Текст резюме:', value='')
            if st.button('+'):
                add_cv(txt)
                st.rerun()

        else:
            resume_ids = data['resume_id']

            resume_id_old = st.session_state.get('resume_id', None)
            print(f'Found Resume id = {resume_id_old}')

            #find index for resume
            if resume_id_old:
                idx = data[data['resume_id'] == resume_id_old].index[0]
            else:
                idx = 0
            new_resume_id = st.selectbox('Select CV:', resume_ids, index=idx)

            txt = data[data['resume_id'] == new_resume_id]['resume'][0]
            st.session_state['resume_id'] = new_resume_id

            new_txt = st.text_area('Резюме:', txt)

            # show list of skills
            skills = get_cv_skills(new_resume_id)
            # show skills list
            if len(skills) > 0:
                st.write('Навыки:')
                st.dataframe(skills, height=200)

            # analyse button
            if st.button('Вытащить навыки из резюме'):
                process_resumes.delay(data.to_json(orient='records'))

            # vacancy matching button
            if st.button('Запуск сверки резюме с вакансиями'):
                vacancy_matching.delay()

            # save button
            if st.button('✅ Сохранить резюме'):
                update_cv(new_resume_id, new_txt)
            # update button
            if st.button('+'):
                add_cv(txt)
                st.rerun()


def display_settings_tab():
    """
        Вкладка настроек
    """
    with st.spinner("Загружаем таблицу настроек..."):
        df = get_active_searches()

    i = app.control.inspect()

    st.markdown('### Активные поиски')
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

    st.write('Активные задачи:')

    # display statuses
    for j in jobs:
        st.write(j['name'],'-',j['status'],'%')

    if st.button('▶️  Загрузить вакансии'):
        grab.delay(edited_df.to_json(orient='records'))
    if st.button('▶️  Ручная загрузка описаний вакансий'):
        grab_description.delay(edited_df.to_json(orient='records'))
    if st.button('▶️  Запустить парсинг требований вакансий'):
        with st.spinner("Loading last data..."):
            data = get_empty_descriptions_data()
            data = data[['vac_id', 'site', 'vac_descr']]
        process_description.delay(data.to_json(orient='records'))

    if st.button('🗑️ Удалить последнюю загрузку вакансий'):
        with st.spinner('deleting in progress'):
            del_last_data()
    if st.button('✅ Сохранить таблицу настроек'):
        with st.spinner('Сохранение...'):
            update_db_df(edited_df)
    if st.button(' Инициализировать БД'):
        with st.spinner('🧨 Инициализация БД...'):
            init_db()

    st.link_button('Grafana Monitor&Analysis', 'http://localhost:3000')


def display_count_by_tab():
    """
        Display count by tab
    """
    with st.spinner("Loading last data..."):
        data = get_last_data()
    columns = data.columns
    agg_col = st.selectbox('Количество вакансий по:',columns, index=0)
    data2 = data.groupby(agg_col).agg({'vac_id':'count'}).reset_index()
    data3 = data2.sort_values('vac_id',ascending=False).head(10)
    st.bar_chart(data3,x=agg_col,y='vac_id', horizontal=True, sort='-vac_id')






st.title('Ассистент поиска работы')

resume_id = st.session_state.get('resume_id', 0)

tab_settings,tab_data, tab_count_by, tab_cv = st.tabs([
    'Настройки',
    'Таблица вакансий',
    'Аналитика по вакансиям',
    'Резюме',
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
