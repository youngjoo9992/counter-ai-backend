import os
import dotenv
import cohere
import bs4
import requests
import asyncio
import aiohttp
import json

dotenv.load_dotenv()

co = cohere.AsyncClient(api_key=os.getenv("COHERE_API_KEY"))

async def fetch(url, headers: dict = {}):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url) as response:
            return await response.text()

async def search_articles(query: str, display: int = 10):
    """Search for articles on a given query"""
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
        "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET")
    }
    response = await fetch(f"https://openapi.naver.com/v1/search/news.json?query={query.strip()}&display={display}", headers=headers)

    data = json.loads(response)

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

async def read_article_link(link: str):
    """Read the article at a given LINK"""
    response = await fetch(link)

    original_content = response

    soup = bs4.BeautifulSoup(original_content, "html.parser")

    title = soup.find("h2", {"id": "title_area"}).get_text()
    text = soup.find("article", {"id": "dic_area"}).get_text()

    return {"title": title.strip(), "snippet": text.strip()}

async def print_counters(query: str, opinion: str, display: int = 10):
    articles = await search_articles(query=query, display=display)
    documents = []
    for article in articles:
        if not article['link']:
            continue
        try:
            response_article = await read_article_link(article['link'])
        except:
            continue
        documents.append(response_article)


    message = await co.chat(model="command-r-plus", message=f'다음 의견에 대해 근거와 함께 반박해: "{opinion}"', documents=documents)

    print('주제: "'+ query + '"\n사용자 의견: "' + opinion + '"\n반박: ' + message.text)
    return message.text


# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# asyncio.run(print_counters(query="코로나 백신", opinion="코로나 백신은 효과가 전혀 없을 뿐더러 그저 제약회사들의 수익창출 수단에 불과해.", display=20))
