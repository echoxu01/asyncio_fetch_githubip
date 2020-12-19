#  -*-  coding:   utf-8  -*-
#  Author  :      EchoXuWIN
#  DateTime:      2020/11/1 15:59
#  Desc    :   获取最新的GitHub相关域名对应IP


import re
import time
import shutil
import os
import datetime
import sys
import requests
import json
import socket
import tldextract  # install tldextract
from bs4 import BeautifulSoup  # install beautifulsoup4
from pythonping import ping  # install pythonping 或者使用multi-ping


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


ip_domain = {}


# 利用ipaddress.com查找ip,也可用http://ip.tool.chinaz.com/ + domain查找
def ipaddress_output_hosts(domain):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
    result = tldextract.extract(domain)
    # 如果是一级域名(github.com)这样的,就拼接为https://{domain}.ipaddress.com
    # 否则就拼接成https://{result.registered_domain}.ipaddress.com/{domain}
    if result.registered_domain == domain:
        url = "https://{}.ipaddress.com".format(domain)
    else:
        url = "https://{}.ipaddress.com/{}".format(result.registered_domain, domain)

    resp = requests.get(url=url, headers=headers)
    real_ip = None
    try:
        soup = BeautifulSoup(resp.text, 'lxml')
        # 其实最精准的ip数据应该从'table[panel-item table table-border-row table-v faq]'下查找内容匹配
        # 'What IP address does 查询的域名 resolve to?'这样格式的'h3'标签
        # 从DNS Resource Records中也可找到
        has_ip_table = soup.select('#map-1 + table[class="panel-item table table-stripes table-v"]')[0]
        ips = has_ip_table.select('tr')[-1].select('td ul li')
        if len(ips) == 1:
            real_ip = ips[0].text
        else:
            low_ttl_ip = {}
            for ip in ips:
                # TODO 使用多线程加速完成ping的过程
                p_r = ping(ip.text, timeout=1, count=5, verbose=False)
                # 构造一个包含{ip地址:响应时间}的字典
                low_ttl_ip.update({ip.text: p_r.rtt_avg})
            # 将平均延迟最小的ip与域名绑定并添加到字典中
            for ttl_ip, ttl_value in low_ttl_ip.items():
                if ttl_value == min(low_ttl_ip.values()):
                    real_ip = ttl_ip
    except Exception as e:
        print(e)
    return real_ip


# 在ip_domain中存储ip:域名的对应关系
def generate_dict():
    for site_name in need_domains:
        site_ip = ipaddress_output_hosts(site_name)
        if site_ip:
            ip_domain[site_name] = site_ip
            print(site_ip + "\t" + site_name)
        else:
            print("# {} 没有找到IP。".format(site_name))


# 对hosts文件去重
def distinct(line):
    flag = False
    for site in need_domains:
        if site in line:
            flag = flag or True
        else:
            flag = flag or False
    return flag


# 更新hosts文件
# TODO 生成switchosts远程文件
def update_host():
    print("\n内容生成中,请耐心等待...请不要关闭此窗口!\n")
    generate_dict()
    today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    shutil.copy("C:\\Windows\\System32\\drivers\\etc\\hosts", "C:\\Windows\\System32\\drivers\\etc\\hosts.bak")
    f1 = open("C:\\Windows\\System32\\drivers\\etc\\hosts", "r")
    lines = f1.readlines()
    f2 = open("temphost", "w")
    # 为了防止host越写用越长，需要删除之前更新的含有github相关内容
    for line in lines:
        match_line = re.compile(r'更新').search(line)
        if not distinct(line) and not match_line:
            f2.write(line)
    f2.write("# github相关域名的ip信息已于  " + str(today) + "  完成更新 \n")
    for key in ip_domain:
        f2.write(ip_domain[key]+"\t"+key+"\n")
    f1.close()
    f2.close()
    # 覆盖原来的host
    shutil.copy("./temphost", "C:\\Windows\\System32\\drivers\\etc\\hosts")

    os.system("ipconfig /flushdns")
    print("\n已更新Github相关域名的IP信息!\n")


if __name__ == '__main__':
    start_time = time.perf_counter()
    update_host()
    end_time = time.perf_counter()
    print(end_time - start_time)
