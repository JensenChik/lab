## IP池
这是为爬虫维护的IP池，IP源取自
* [西刺代理](http://www.xicidaili.com)
* [66代理](http://www.66ip.cn)
* [全民代理](http://www.goubanjia.com)
* [酷伯伯代理](http://www.coobobo.com)
* [云代理](http://www.ip3366.net/)
* [云海代理](http://www.kxdaili.com/)
* [DATA5U](http://www.data5u.com)

### 结构设计
<pre>


                              ┏━━━━━━━━━━━━┓
                              ┃   Server   ┃
                              ┣━━━━━━━━━━━━┫
                              ┃     get    ┃
                              ┗━━━━━━┳━━━━━┛
                                     ┗ ━ ━ ━ ━  ━ ━ ━ ━ ━ ━ ━ ┓
     ┏━━━━━━━━━━━━┓            ┏━━━━━━━━━━━━┓           ┏━━━━━┻━━━━━━┓
     ┃   Source   ┃            ┃  Producer  ┃           ┃            ┃
     ┣━━━━━━━━━━━━┫  ◂━━━━━━♦  ┣━━━━━━━━━━━━┫  ━ ━ ━ ━  ┃    MySQL   ┃
     ┃  _request  ┃            ┃    _dump   ┃           ┃            ┃
     ┃    get     ┃            ┃    serve   ┃           ┃            ┃
     ┗━━━━━━━━━━━━┛            ┗━━━━━━━━━━━━┛           ┗━━━━━━━━━━━━┛
           Δ
      ┏━━━━┻━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┏━━━━━┻━━━━━━┓    ┏━━━━━┻━━━━━━┓        ┏━━━━━┻━━━━━━┓   ┏━━━━━┻━━━━━━┓
┃    XiCi    ┃    ┃   SixSix   ┃        ┃   YunHai   ┃   ┃   Data5U   ┃
┣━━━━━━━━━━━━┫    ┣━━━━━━━━━━━━┫ ...... ┣━━━━━━━━━━━━┫   ┣━━━━━━━━━━━━┫
┃  _extract  ┃    ┃  _extract  ┃        ┃  _extract  ┃   ┃  _extract  ┃
┃    get     ┃    ┃    get     ┃        ┃    get     ┃   ┃    get     ┃
┗━━━━━━━━━━━━┛    ┗━━━━━━━━━━━━┛        ┗━━━━━━━━━━━━┛   ┗━━━━━━━━━━━━┛
</pre>
* Source.get: 抽象方法，从源中获取最新的IP列表
* Source._request: 父类方法，获取IP列表时所使用的request接口
* XiCi._extract: 将HTML中的内容解析出ip，转化为list
* Producer._dump: 从各个源中获取最新ip，并存放到mysql中
* Producer.serve: 启动自动更新服务
* Server.get: 通过HTTP随机获取一个当前可用的IP

### 运行机制
