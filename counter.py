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
            "originallink": i['originallink'],
        })

    return items

async def read_article_link(title: str, link: str, original_link: str = "Unknown"):
    """Read the article at a given LINK"""
    response = await fetch(link)

    original_content = response

    soup = bs4.BeautifulSoup(original_content, "html.parser")

    text = soup.find("article", {"id": "dic_area"}).get_text()

    return {"title": title.strip() + "<출처 링크: " + original_link + ">", "snippet": text.strip()}

async def print_counters(query: str, opinion: str, display: int = 10):
    articles = await search_articles(query=query, display=display)
    documents = []
    for article in articles:
        if not article['link']:
            continue
        try:
            response_article = await read_article_link(article['title'], article['link'], article['originallink'])
        except:
            continue
        documents.append(response_article)


    message = await co.chat(model="command-r-plus", message=f'다음 의견에 대해 뉴스 기사를 이용한 근거와 함께 반박해: "{opinion}". 그리고 네 반박의 근거로 사용된 기사들의 출처를 밝혀줘. 출처를 밝힐 때는 출처 링크를 같이 덧붙여줘. 명심해, "너의 반박"에 "사용된" 기사들의 출처들만 추가해야 해. 너의 반박과 상관 없는 기사는 추가하지 마. 만약 너의 반박의 근거로 사용된 기사가 없다면 출처를 추가하지 않아도 좋아.', documents=documents)

    print('주제: "'+ query + '"\n사용자 의견: "' + opinion + '"\n반박: ' + message.text)
    return message.text.strip()


# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# asyncio.run(print_counters(query="코로나 백신", opinion="코로나 백신은 효과가 전혀 없을 뿐더러 그저 제약회사들의 수익창출 수단에 불과해.", display=50))
