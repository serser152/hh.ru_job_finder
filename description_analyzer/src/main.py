#!/usr/bin/env python3
'''
API(FastAPI) for hh_grabber functionality
'''

from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from .llm import parse_desc, parse_resume, match_vacancy_cv


class ParseDescriptionRequest(BaseModel):
    'Class for search request'
    desc: str

class MatchRequest(BaseModel):
    'Class for match request'
    vacancy: str
    resume: str

app = FastAPI(host='0.0.0.0')


@app.get('/health')
async def health():
    """Health function - returns "ok\""""
    return 'ok'


@app.post('/parse_descriptions')
async def parse_description(request: ParseDescriptionRequest):
    """Get vacancies list and returns json"""
    print('find skills from vacancy ' + request.desc)
    res = parse_desc(request.desc)
    print(f'res = {res}')
    df = pd.DataFrame(res.split('\n'), columns=['skill'])
    return df.drop_duplicates().to_json(orient='records')


@app.post('/parse_resume')
async def parse_resumes(request: ParseDescriptionRequest):
    """Get skills list and returns json"""
    #print('find resume skills ' + request.desc)
    res = parse_resume(request.desc)
    #print(f'res = {res}')
    df = pd.DataFrame(res.split('\n'), columns=['skill'])
    return df.drop_duplicates().to_json(orient='records')

@app.post('/match_vacancy_resume')
async def match(request: MatchRequest):
    'Get vacancies list and returns json'
    print('Matcher\n---------\n',request.vacancy, request.resume)
    res = match_vacancy_cv(request.vacancy, request.resume)
    print(f'res = {res}')
    return {'match': res}
