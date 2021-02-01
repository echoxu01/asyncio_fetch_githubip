#  -*-  coding:   utf-8  -*-
#  Author  :      echoxu
#  DateTime:      2021/2/1 16:46

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("下载网易包子表情包异常")


def generate_url_list():
    for i in range(10, 253):
        download_url = "http://qnm.16163.com/static/image/smiley/baozi/{}.gif".format(i)
        url_list.append(download_url)
    print(url_list)


async def fetch_content(url):
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/84.0.4147.105 Safari/537.36'}

    async with aiohttp.ClientSession(
            headers=header, connector=aiohttp.TCPConnector(ssl=False)
    ) as session:
        try:
            async with session.get(url) as response:
                resp_content = await response.content.read()
                file_name = url.rsplit('/')[-1]
                with open(file_name, mode='wb') as file_object:
                    file_object.write(resp_content)

        except Exception as e:
            logger.error(e)


async def main(urls):
    """ 异步任务函数主入口 """
    tasks = [asyncio.create_task(fetch_content(url)) for url in urls]
    await asyncio.gather(*tasks)
    # 不加下面代码会报错: RuntimeError: Event loop is closed
    await asyncio.sleep(2)


if __name__ == '__main__':
    url_list = []
    generate_url_list()
    asyncio.run(main(url_list))

