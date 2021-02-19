#  -*-  coding:   utf-8  -*-
#  Author  :      echoxu
#  DateTime:      2020/12/3 20:58
#%%
import re
import os
import shutil
import time
import logging
import aiohttp
import asyncio
import tldextract
from bs4 import BeautifulSoup
from pythonping import ping
import concurrent.futures
import platform

# 默认为Windows路径
is_windows = True
host_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"

if "Windows" in platform.platform():
    print("Windows")
else:
    host_path = "/etc/hosts"
    is_windows = False
    print("Linux")

print("Host Path: " + host_path)

#%%
need_domains = ['github.com',
                'www.github.com',
                'github.global.ssl.fastly.net',
                'github.map.fastly.net',
                'github.githubassets.com',
                'github.io',
                'assets-cdn.github.com',
                'gist.github.com',
                'help.github.com',
                'api.github.com',
                'nodeload.github.com',
                'codeload.github.com',
                'raw.github.com',
                'documentcloud.github.com',
                'status.github.com',
                'training.github.com',
                'raw.githubusercontent.com',
                'gist.githubusercontent.com',
                'cloud.githubusercontent.com',
                'camo.githubusercontent.com',
                'avatars0.githubusercontent.com',
                'avatars1.githubusercontent.com',
                'avatars2.githubusercontent.com',
                'avatars3.githubusercontent.com',
                'avatars4.githubusercontent.com',
                'avatars5.githubusercontent.com',
                'avatars6.githubusercontent.com',
                'avatars7.githubusercontent.com',
                'avatars8.githubusercontent.com',
                'user-images.githubusercontent.com',
                'favicons.githubusercontent.com',
                'github-cloud.s3.amazonaws.com',
                'github-production-release-asset-2e65be.s3.amazonaws.com',
                'github-production-user-asset-6210df.s3.amazonaws.com',
                'github-production-repository-file-5c1aeb.s3.amazonaws.com',
                'alive.github.com',
                'guides.github.com',
                'docs.github.com'
                ]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("获取域名对应的ip异常")


def generate_url_list():
    """ 生成符合ipadredd.com查询的url地址. """
    for domain in need_domains:
        result = tldextract.extract(domain)
        if result.registered_domain == domain:
            url = "https://{}.ipaddress.com".format(domain)
        else:
            url = "https://{}.ipaddress.com/{}".format(result.registered_domain, domain)

        url_list.append(url)


async def fetch_content(url):
    """ 爬取url,从返回的html中解析出域名对应的ip. """
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/84.0.4147.105 Safari/537.36'}

    async with aiohttp.ClientSession(
            headers=header, connector=aiohttp.TCPConnector(ssl=False)
    ) as session:
        try:
            async with session.get(url) as response:
                resp_text = await response.text()
                soup = BeautifulSoup(resp_text, 'lxml')
                ip_info_all = soup.find('tbody', id="dnsinfo").select('tr td a')
                ip_list = []

                for each_ip_all in ip_info_all:
                    ip_info = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", each_ip_all.text)
                    if ip_info:
                        str_ip = ''.join(ip_info)
                        ip_list.append(str_ip)

                await asyncio.create_task(fetch_ip(url, ip_list))

        except Exception as e:
            logger.error("获取 {} 信息时出现错误 {}".format(url, e))


async def fetch_ip(url, ip_list):
    """
    解析github相关域名的ip个数,当域名对应多个ip时进行异步操作,获取rtt最小的ip作为最终的ip.
    """
    real_url = url.split('/')[-1].replace(".ipaddress.com", "")

    if ip_list:
        if len(ip_list) == 1:
            str_ip_list = ''.join(ip_list)
            print('{} 解析到 {} 个ip,其值为 {} '.format(real_url, len(ip_list), str_ip_list))
            githubip_domain[real_url] = str_ip_list
        else:
            await asyncio.create_task(get_lowrtt_ip(url, ip_list))
    else:
        logger.error('{} 未获取到ip'.format(real_url))


def ping_ip(matched_ip):
    """ 阻塞操作,依次ping已获取ip列表里的ip并返回结果. """
    low_rtt_ip = {}

    for waitping_ip in matched_ip:
        p_r = ping(waitping_ip, timeout=1, count=5, verbose=False)
        low_rtt_ip.update({waitping_ip: p_r.rtt_avg})

    return low_rtt_ip


async def get_lowrtt_ip(url, ip_list):
    """
    利用asyncio + ThreadPoolExecutor将阻塞的操作改造成异步任务.
    """
    real_url = url.split('/')[-1].replace(".ipaddress.com", "")

    # 通过线程池将阻塞任务改造成异步任务.
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        loop = asyncio.get_running_loop()
        ping_res = await loop.run_in_executor(pool, ping_ip, ip_list)
        # print('{} 解析到 {} 个ip,多个ip与rtt对应关系分别为: {}'.format(real_url, len(ip_list), ping_res))

    for rtt_ip, rtt_value in ping_res.items():
        if rtt_value == min(ping_res.values()):
            githubip_domain[real_url] = rtt_ip

    if real_url in githubip_domain.keys():
        print('{} 解析到 {} 个ip,最终ip(取最小rtt值)为 {} '.format(real_url, len(ip_list), githubip_domain[real_url]))


async def main(urls):
    """ 异步任务函数主入口 """
    tasks = [asyncio.create_task(fetch_content(url)) for url in urls]
    await asyncio.gather(*tasks)
    # 不加下面代码会报错: RuntimeError: Event loop is closed
    await asyncio.sleep(2)


def distinct(line):
    """ 对hosts文件去重 """
    flag = False
    for site in need_domains:
        if site in line:
            flag = flag or True
        else:
            flag = flag or False
    return flag


def update_host():
    """ 更新windows中的hosts文件 """

    print("\n正在更新系统hosts文件...请不要关闭此窗口!\n")

    today = time.strftime("%Y-%m-%d %X")
    shutil.copy(host_path, str(host_path + ".bak"))

    f1 = open(host_path, "r")
    lines = f1.readlines()
    f2 = open("temphost", "w")

    for line in lines:
        match_line = re.compile(r'更新').search(line)
        if not distinct(line) and not match_line:
            f2.write(line)
    f2.write("\n# github相关域名的ip信息已于  " + str(today) + "  完成更新 \n")

    for key in githubip_domain:
        f2.write(githubip_domain[key]+"\t"+key+"\n")

    f1.close()
    f2.close()

    shutil.copy("./temphost", host_path)
    if is_windows:
        os.system("ipconfig /flushdns")
    else:
        os.system("systemd-resolve --flush-caches")
    print("\n已更新Github相关域名的IP信息!\n")


if __name__ == '__main__':
    start_time = time.perf_counter()
    url_list = []
    generate_url_list()
    githubip_domain = {}
    # asyncio.run(main(url_list), debug=True)
    asyncio.run(main(url_list))
    end_time = time.perf_counter()
    print('\nFetched: {}/{}(total) sites in {} seconds'.format(len(githubip_domain), len(url_list), end_time - start_time))
    update_host()
