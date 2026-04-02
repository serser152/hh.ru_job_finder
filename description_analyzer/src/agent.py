#!/usr/bin/env python
"""
Agent module
Agent tools and llm initialization
"""

from datetime import date
from datetime import datetime
from os import environ

from ddgs import DDGS
from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_gigachat.chat_models import GigaChat
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama
from .planning import planning_tools
load_dotenv(find_dotenv())




#=======================================
# Tools
# Tools for agent
#=======================================

tools=planning_tools
@tool
def search_web_ddgs(query: str) -> str:
    """ 
    Find information in web.
    Args:
    query - search query
    """
    with DDGS() as ddgs:
        max_results=5
        hits = ddgs.text(query, region="ru-ru", time="w", max_results=max_results)
        return "\n".join(f"{hit['title']}: {hit['body']} -- {hit['href']}" \
                         for hit in hits[:max_results])

tools.append(search_web_ddgs)


@tool
def search_web_tavily(query:str) -> str:
    """ 
    Find information in web.
    Args:
    query - search query
    """
    tav = TavilySearch(max_results=15)
    res=tav.invoke({'query':query})
    return '\n'.join([t['title']+":"+t['content'] for t in res['results']])

tools.append(search_web_tavily)


@tool
def get_current_time():
    """Get current time and date"""
    dt=datetime.now()
    return dt.strftime('Текущее время %H:%M:%S')

tools.append(get_current_time)

@tool
def get_current_date():
    """Get current date"""
    dt=datetime.now()
    return "Текущая дата "+dt.strftime('%d.%m.%Y')

tools.append(get_current_date)


#======================================
#   Agent section
#======================================


class WrongLLMException(Exception):
    """ Wrong LLM exception
    Specify wrong llm name or model"""
    def __init__(self, message="Wrong LLM"):
        self.message = message
        super().__init__("Invalid LLM:" + self.message)


def init_llm(
        name='gigachat',
        model='meta-llama/llama-3.3-8b-instruct:free',
        ollama_base_url="http://localhost:11434"):
    """
    :param name: openrouter/gigachat
    :param model:
        "meta-llama/llama-3.3-8b-instruct:free"
        "z-ai/glm-4.5-air:free"
        "openai/gpt-oss-20b:free"
    :return: llm instance
    """

    if name == 'gigachat':
        llm = GigaChat(credentials=environ.get("GIGACHAT_API_KEY",""),
                    verify_ssl_certs=False)
    elif name == 'openrouter':
        llm = ChatOpenAI(model=model,
        base_url="https://openrouter.ai/api/v1",
        api_key=environ.get("OPENROUTER_API_KEY",""))
    elif name == 'ollama':
        llm = ChatOllama(model="gpt-oss:20b",
                        base_url=ollama_base_url)
        llm.bind_tools(tools)
    else:
        raise WrongLLMException('Unknown llm initialization')
    return llm

def init_agent(
        llm_provider = 'gigachat',
        model = 'openai/gpt-oss-20b:free',
        use_search = False,
        system_prompt = None
):
    """

    :param llm_provider: openrouter/gigachat
    :param model:
        "meta-llama/llama-3.3-8b-instruct:free"
        "z-ai/glm-4.5-air:free"
        "openai/gpt-oss-20b:free"
    :param use_search: use web search tools
    :return:
    """
    llm = init_llm(llm_provider, model)

    if use_search:
        tools_used = tools
    else:
        tools_used = []


    checkpointer = InMemorySaver()

    agent = create_agent(
            model = llm,
            tools = tools_used,
            system_prompt=system_prompt,
            checkpointer=checkpointer,
            )
    return llm, agent


class MyAgent:
    """
    Agent class
    For using agent or agent crowd
    """
    llm, agent = None, None
    def __init__(self, name='gigachat',
                 model='openai/gpt-oss-20b:free',
                 **kwargs):
        self.use_search = kwargs.get('use_search', False)
        today = date.today().strftime("%d.%m.%Y")  # DD.MM.YYYY
        self.system_prompt = kwargs.get(
            'system_prompt', (
            "Мы находимся в г. Нижний Новгород."
            "Ты полезный ассистент. Используй search_web_tavily и "
            "search_web_ddgs для поиска информации в интернете. Отвечай кратко и простыми словами."
            "При ответе не используй markdown формат. Ответ должен содеражать только текст."
            ))
        self.system_prompt = f"Сегодня {today}." + self.system_prompt
        self.llm, self.agent = init_agent(
            name,
            model,
            self.use_search,
            system_prompt=self.system_prompt
        )
        self.max_iterations = kwargs.get('max_iterations', 5)
        self.verbose = kwargs.get('verbose', False)
        self.config = {'configurable': {'thread_id': 1}}


    def ask(self, message: str) -> str:
        """
        return agent answer
        """

        msg = {'messages': [{'role': 'user', 'content': message}]}
        step = 0
        ans = ''
        for chunk in self.agent.stream(msg, config=self.config, print_mode=()):
            for k, v in chunk.items():
                step += 1
                if self.verbose:
                    print(f'step {step}: => {k}: {v}')
                ans = v['messages'][-1].content
                if step > self.max_iterations:
                    break
        return ans

    def ask_llm(self, message: str) -> str:
        """
        return model answer
        """
        response = self.llm.invoke(message)
        return response.content

#a = MyAgent('gigachat',use_search=True,verbose=True,max_iterations=10)
#a = MyAgent('openrouter', model='openai/gpt-oss-20b:free',use_search=True)
#a = MyAgent('ollama', model='gpt-oss:20b',use_search=True)
#print(a.ask('Какой 22.11.2025 день недели? Ответь в одно слово.'))
#print(a.ask('Какой завтра день недели?'))
