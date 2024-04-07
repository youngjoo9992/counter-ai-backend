from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
import anthropic
import requests
import os
import dotenv
import time 
import bs4
# from openai import OpenAI 

dotenv.load_dotenv()

# model = ChatOpenAI(model="gpt-3.5-turbo", base_url="https://api.ohmygpt.com/v1/", api_key=os.getenv("OHMYGPT_API_KEY"))
model = ChatAnthropic(model="claude-3-haiku-20240307", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

client = anthropic.Anthropic()
# client = OpenAI(api_key=os.getenv("OHMYGPT_API_KEY"), base_url="https://api.ohmygpt.com/v1/")

@tool
def search_articles(query: str, display: int = 10):
    """Search for articles on a given query"""
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
        "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET")
    }
    response = requests.get(f"https://openapi.naver.com/v1/search/news.json?query={query.strip()}&display={display}", headers=headers)
    
    data = response.json()

    items = []

    for i in data['items']:
        if not "naver" in i['link']:
            continue
        items.append({
            "title": i['title'],
            "link": i['link'],
            "description": i['description'],
            "pubDate": i['pubDate']
        })

    return items


@tool
def read_article_link(link: str):
    """Read the article at a given LINK"""
    response = requests.get(link)

    original_content = response.text

    soup = bs4.BeautifulSoup(original_content, "html.parser")

    text = soup.find("article", {"id": "dic_area"}).get_text()

    return text.strip()

    # message = client.messages.create(
    #     model="claude-3-haiku-20240307",
    #     max_tokens=1024,
    #     messages=[{"role": "user", "content": text}],
    #     system="Summarize the article.",
    # )
    # print(message.content)

    # return message.content

    # # Remove more useless stuffs
    # for div in soup.find_all("script"):
    #     div.decompose()

    # for div in soup.find_all("style"):
    #     div.decompose()

    # text = soup.get_text()

    # try:
    #     message = client.messages.create(
    #         model="claude-3-haiku-20240307",
    #         max_tokens=1024,
    #         messages=[
    #             {"role": "user", "content": text}
    #         ],
    #         system="You are parsing expert for news articles. You will be provided with the HTML of news article. Please respond back with the news headline and FULL content(I repeat, FULL content) of the article."
    #     )
    #     # message = client.chat.completions.create(
    #     #     model="gpt-3.5-turbo",
    #     #     messages=[
    #     #         {"role": "system", "content": "You are parsing expert for news articles. You will be provided with the HTML of news article. Please respond back with the news headline and FULL content(I repeat, FULL content) of the article."},
    #     #         {"role": "user", "content": response.text}
    #     #     ],
    #     #     max_tokens=2048,
    #     # )
    # except Exception as e:
    #     time.sleep(2)
    #     print(e)
    #     return read_article_link(link)
    # return message.content[0].text

class SearchArticles(BaseModel):
    """Search for articles on a given query"""

    query: str = Field(description="The query to search for")
    display: int = Field(description="The number of articles to search", default=10)

class ReadArticleLink(BaseModel):
    """Read the article at a given LINK"""

    link: str = Field(description="The link to read the article from")

llm_with_tools = model.bind_tools([SearchArticles, ReadArticleLink])



def print_counters(query: str, opinion: str, display: int = 10):
    prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "너는 주어진 의견에 대해 반박하는 챗봇이야. 너는 뉴스 기사를 검색하고 분석해서 주어진 의견에 대한 반박을 해야해. read_article_url 툴을 꼭 사용해서 **너가 생각하기에** 반박에 필요한 뉴스 기사를 읽어 (읽을 때 originalLink가 아닌 **그냥** link를 읽어!).",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
    )

    chain = prompt | llm_with_tools

    print(list(chain.stream({"input": f'"{query}"에 대한 뉴스 기사들을 {display}개 찾고, 찾은 기사들을 토대로 다음 의견에 반박해: "{opinion}"'}))[-1])

    # tools = [search_articles, read_article_link]

    # # llm_with_tools = model.bind_tools(tools)

    # agent = (
    #     {
    #         "input": lambda x: x["input"],
    #         "agent_scratchpad": lambda x: format_to_openai_tool_messages(
    #             x["intermediate_steps"]
    #         ),
    #     }
    #     | prompt
    #     | llm_with_tools
    #     | OpenAIToolsAgentOutputParser()
    # )

    # agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # print(list(agent_executor.stream({"input": f'"{query}"에 대한 뉴스 기사들을 {display}개 찾고, 찾은 기사들을 토대로 다음 의견에 반박해: "{opinion}"'}))[-1])

print_counters(query="의대 증원", opinion="의대 증원은 의료 재정 붕괴 가능성이 있고, 의료 교육이 부실화될 수 있기 때문에 반대한다.", display=10)