#!/usr/bin/env python3
'''
API(FastAPI) for hh_grabber functionality
'''

from fastapi import FastAPI
from pydantic import BaseModel
from .grab_hh import get_vacancies, accept_vacancy, get_descriptions


class SearchRequest(BaseModel):
    'Class for search request'
    phone: str
    password: str
    request: str


class AcceptRequest(BaseModel):
    'Class for respond to vacancy'
    phone: str
    password: str
    vacancy_ids: list


class GetDescriptionRequest(BaseModel):
    'Class for grab description'
    phone: str
    password: str
    vacancy_ids: list


app = FastAPI(host='0.0.0.0')


@app.get('/health')
async def health():
    'Health function - returns "ok"'
    return 'ok'


@app.post('/find_vacancies')
async def find_vacancies(request: SearchRequest):
    'Get vacancies list and returns json'
    print('find vacancies ' + request.request)
    df = get_vacancies(request.phone, request.password, request.request)
    return df.to_json(orient='records')


@app.post('/get_vacancy_descriptions')
async def get_desc(request: GetDescriptionRequest):
    'Get vacancies descriptions by vac_id list'
    print('Get descriptions ' + str(request.vacancy_ids))
    res = get_descriptions(request.phone, request.password, request.vacancy_ids)
    return res.to_json(orient='records')


@app.post('/accept_vacancy')
async def accept_vacancy_by_id(request: GetDescriptionRequest):
    'Respond to vacancy by id'
    print('accept vacancies ' + str(request.vacancy_ids))
    accept_vacancy(request.phone, request.password, request.vacancy_ids)
