#!/usr/bin/env python3
from fastapi import FastAPI
from pydantic import BaseModel
from .grab_zp import get_vacancies, accept_vacancy, get_descriptions
import json


class SearchRequest(BaseModel):
    phone: str
    password: str
    request: str

class AcceptRequest(BaseModel):
    phone: str
    password: str
    vacancy_ids: list

class GetDescriptionRequest(BaseModel):
    phone: str
    password: str
    vacancy_ids: list

app = FastAPI(host='0.0.0.0')

@app.get('/health')
async def health():
    return 'ok'

@app.post('/find_vacancies')
async def find_vacancies(request: SearchRequest):
    print('find vacancies '+request.request)
    df = get_vacancies(request.phone, request.password, request.request)
    return df.to_json(orient='records')

@app.post('/get_vacancy_descriptions')
async def get_desc(request: GetDescriptionRequest):
    print('Get descriptions '+str(request.vacancy_ids))
    res = get_descriptions(request.phone, request.password,  request.vacancy_ids)
    return res.to_json(orient='records')

@app.post('/accept_vacancy')
async def accept_vacancy_by_id(request: GetDescriptionRequest):
    print('accept vacancies '++str(request.vacancy_ids))
    res = accept_vacancy(request.phone, request.password,  request.vacancy_ids)
    return str(res)

