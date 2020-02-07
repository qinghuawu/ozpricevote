import aiohttp
import asyncio
import re
import time
import aioredis
from bs4 import BeautifulSoup
import heapq
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


async def open_url(url, session, headers):
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.text()
            soup = BeautifulSoup(data, 'lxml')
            return soup
    except Exception as e:
        print(e)
        pass


async def get_product(soups, db_pool, heap, lowest_in_history, brands):
    category = soups[0].find('span', attrs={'id': 'category_title_span'}).text.strip()
    for soup in soups:
        L = soup.find('div', attrs={'class': 'product-list-container'}).find_all('td')
        while not L[-1].text:
            L = L[:-1]
        for item in L:
            mapping = {'title_chinese': item.find('a').get('title').strip(),
                       'title': item.find('img').get('alt').strip(),
                       'price': float(item.find('span').text.strip()[1:]),
                       'url': 'https://www.chemistwarehouse.com.au' + item.find('a').get('href'),
                       'image': item.find('img').get('src'),
                       'category': category}
            item_index = await db_pool.hget('item:index', mapping['title'])
            if not item_index:
                item_index = await db_pool.incr('item:id')
                await db_pool.hset('item:index', mapping['title'], item_index)
            mapping['item_id'] = int(item_index)
            mapping['original_price'] = float(mapping['price'] + (
                float(item.find('span', attrs={'class': 'Save'}).text.strip()[4:])
                if item.find('span', attrs={'class': 'Save'}) else 0))

            lowest_price_history = float(await db_pool.hget(f'item:info:{mapping["item_id"]}', 'lowest_price') \
                                   or mapping['price'])
            mapping['lowest_price'] = min(lowest_price_history, mapping['price'])
            if mapping['lowest_price'] == mapping['price']:
                lowest_in_history.append(mapping['item_id'])
            mapping['discount'] = float((mapping['original_price'] - mapping['price']) / mapping['original_price'])
            await db_pool.hmset_dict(f'item:info:{mapping["item_id"]}', mapping)
            brand = mapping['title'].split()[0].lower()
            brands.add(brand)
            await db_pool.sadd(f'{brand}:items', mapping['item_id'])
            heapq.heappush(heap, (mapping['discount'], mapping['item_id']))
            if len(heap) > 150:
                heapq.heappop(heap)


async def item_by_category(category, session, headers, db_pool, heap, lowest_in_history, brands):
    url = 'https://www.chemistwarehouse.hk/Shop-OnLine/' + category + '?size=120'
    print(category, 'started at', time.strftime('%X'))
    main_soup = await open_url(url, session, headers)
    soups = [main_soup]
    # print(category)
    if main_soup.find('a', attrs={'class': 'last-page'}):
        last = int(re.search(r'\d+$', main_soup.find('a', attrs={'class': 'last-page'}).get('href')).group())
        for page in range(2, last + 1):
            await asyncio.sleep(0.1)
            soup = await open_url(url + '&page=' + str(page), session, headers)
            # print(category)
            if soup:
                soups.append(soup)
    await get_product(soups, db_pool, heap, lowest_in_history, brands)
    print(category, 'done!', time.strftime('%X'))


async def init_spyder():
    try:
        while True:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Connection': 'keep-alive'
                }
                categories = ['256/health', '257/beauty', '258/medicines', '259/personal-care', '260/medical-aids']
                redis_pool = await aioredis.create_redis_pool('redis://localhost')
                heap = []
                lowest_in_history = []
                brands = set()
                todo = [item_by_category(x, session, headers, redis_pool, heap, lowest_in_history, brands) for x in categories]
                await asyncio.gather(*todo)
                tr = redis_pool.multi_exec()
                tr.delete('discount:highest')
                tr.zadd('discount:highest', *[item for pair in heapq.nsmallest(150, heap) for item in pair])
                tr.delete('price:lowest_history')
                tr.sadd('price:lowest_history', *lowest_in_history)
                tr.delete('brands:')
                tr.zadd('brands:', *[item for brand in brands for item in [0, brand]])
                await tr.execute()
                sleep_time = 10 * 60 * 60
            await asyncio.sleep(sleep_time)
    except asyncio.CancelledError:
        pass
    finally:
        if session:
            await session.close()


if __name__ == '__main__':
    asyncio.run(init_spyder())
