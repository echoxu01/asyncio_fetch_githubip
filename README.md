# asyncio_fetch_githubip

解决github在国内加载慢的问题。

## 实现原理

使用asyncio + aiohttp 爬取获取ip地址并绑定本地host，绕过DNS解析。

## 运行环境

* python3.7+，我使用的是python3.8.6。

* 依赖库
  - asyncio
  - aiohttp
  - BeautifulSoup
  - pythonping
  - tldextract

 ## 使用方法

* 用记事本或notepad++打开`update_hosts.bat`文件，将` var变量值`改成你自己存放该项目的地址
* 右键点击`update_hosts.bat`, 以`管理员`身份运行

> src/fetch_githubip_sync.py中的代码没有使用asyncio,代码是同步阻塞的，不推荐使用。
>

## 效果图



![fetchip_cmd](https://cache.echoxu.cn/github-img/fetchip_cmd.png)



![update-hosts](https://cache.echoxu.cn/github-img/update-hosts.png)