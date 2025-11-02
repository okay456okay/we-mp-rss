import json
import requests
import time
import random
import yaml
import re
from bs4 import BeautifulSoup
from .base import WxGather
from core.print import print_error
from core.log import logger
import traceback
# 继承 BaseGather 类
class MpsWeb(WxGather):

    # 重写 content_extract 方法
    def content_extract(self,  url):
        try:
            from driver.wxarticle import Web as App
            r = App.get_article_content(url)
            if r!=None:
                text = r.get("content","")
                if text is None:
                    return
                if "当前环境异常，完成验证后即可继续访问" in text:
                    print_error("当前环境异常，完成验证后即可继续访问")
                    return ""
                soup = BeautifulSoup(text, 'html.parser')
                # 找到内容
                js_content_div = soup
                # 移除style属性中的visibility: hidden;
                if js_content_div is None:
                    return ""
                js_content_div.attrs.pop('style', None)
                # 找到所有的img标签
                img_tags = js_content_div.find_all('img')
                # 遍历每个img标签并修改属性，设置宽度为1080p
                for img_tag in img_tags:
                    if 'data-src' in img_tag.attrs:
                        img_tag['src'] = img_tag['data-src']
                        del img_tag['data-src']
                    if 'style' in img_tag.attrs:
                        style = img_tag['style']
                        # 使用正则表达式替换width属性
                        style = re.sub(r'width\s*:\s*\d+\s*px', 'width: 1080px', style)
                        img_tag['style'] = style
                return  js_content_div.prettify()
        except Exception as e:
                logger.error(e)
        return ""
    # 重写 get_Articles 方法
    def get_Articles(self, faker_id:str=None,Mps_id:str=None,Mps_title="",CallBack=None,start_page:int=0,MaxPage:int=1,interval=10,Gather_Content=False,Item_Over_CallBack=None,Over_CallBack=None):
        """
        使用Web模式获取公众号文章列表
        
        Args:
            faker_id: 公众号faker_id
            Mps_id: 公众号ID
            Mps_title: 公众号名称
            CallBack: 文章回调函数
            start_page: 起始页码
            MaxPage: 最大页码
            interval: 请求间隔（秒）
            Gather_Content: 是否采集内容
            Item_Over_CallBack: 每页完成回调
            Over_CallBack: 全部完成回调
        """
        super().Start(mp_id=Mps_id)
        if self.Gather_Content:
            Gather_Content=True
        logger.info(f"[文章获取-Web模式] 开始获取文章 - 公众号: {Mps_title}, 公众号ID: {Mps_id}, faker_id: {faker_id}, 起始页: {start_page}, 最大页: {MaxPage}, 采集内容: {Gather_Content}")
        print(f"Web浏览器模式,是否采集[{Mps_title}]内容：{Gather_Content}\n")
        # 请求参数
        url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"
        count=5
        params = {
        "sub": "list",
        "sub_action": "list_ex",
        "begin":start_page,
        "count": count,
        "fakeid": faker_id,
        "token": self.token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": 1
    }
        # 连接超时
        session=self.session
        # 起始页数
        i = start_page
        total_articles = 0
        while True:
            if i >= MaxPage:
                logger.info(f"[文章获取-Web模式] 达到最大页数，停止获取 - 公众号: {Mps_title}, 当前页: {i}, 最大页: {MaxPage}")
                break
            begin = i * count
            params["begin"] = str(begin)
            logger.info(f"[文章获取-Web模式] 开始获取第{i+1}页 - 公众号: {Mps_title}, begin: {begin}")
            print(f"第{i+1}页开始爬取\n")
            # 随机暂停几秒，避免过快的请求导致过快的被查到
            sleep_time = random.randint(0,interval)
            logger.debug(f"[文章获取-Web模式] 等待 {sleep_time} 秒后继续 - 公众号: {Mps_title}")
            time.sleep(sleep_time)
            try:
                headers = self.fix_header(url)
                logger.debug(f"[文章获取-Web模式] 发送请求 - 公众号: {Mps_title}, URL: {url}, 参数: begin={begin}, fakeid={faker_id}")
                resp = session.get(url, headers=headers, params = params, verify=False)
                
                msg = resp.json()
                logger.debug(f"[文章获取-Web模式] 收到响应 - 公众号: {Mps_title}, ret: {msg.get('base_resp', {}).get('ret', 'unknown')}")
                self._cookies =resp.cookies
                # 流量控制了, 退出
                if msg['base_resp']['ret'] == 200013:
                    logger.error(f"[文章获取-Web模式] 触发频率限制 - 公众号: {Mps_title}, 在页码 {begin} 处停止")
                    super().Error("frequencey control, stop at {}".format(str(begin)))
                    break
                
                if msg['base_resp']['ret'] == 200003:
                    logger.error(f"[文章获取-Web模式] 登录会话失效 - 公众号: {Mps_title}, 在页码 {begin} 处停止")
                    super().Error("Invalid Session, stop at {}".format(str(begin)),code="Invalid Session")
                    break
                if msg['base_resp']['ret'] != 0:
                    error_msg = msg['base_resp'].get('err_msg', '未知错误')
                    error_code = msg['base_resp']['ret']
                    logger.error(f"[文章获取-Web模式] API返回错误 - 公众号: {Mps_title}, 错误原因: {error_msg}, 错误代码: {error_code}")
                    super().Error("错误原因:{}:代码:{}".format(error_msg, error_code),code="Invalid Session")
                    break    
                # 如果返回的内容中为空则结束
                if 'publish_page' not in msg:
                    logger.info(f"[文章获取-Web模式] 没有更多文章 - 公众号: {Mps_title}, 在页码 {begin} 处停止")
                    super().Error("all ariticle parsed")
                    break
                if msg['base_resp']['ret'] != 0:
                    error_msg = msg['base_resp'].get('err_msg', '未知错误')
                    error_code = msg['base_resp']['ret']
                    logger.error(f"[文章获取-Web模式] API返回错误 - 公众号: {Mps_title}, 错误原因: {error_msg}, 错误代码: {error_code}")
                    super().Error("错误原因:{}:代码:{}".format(error_msg, error_code))
                    break  
                if "publish_page" in msg:
                    msg["publish_page"]=json.loads(msg['publish_page'])
                    page_articles = 0
                    for item in msg["publish_page"]['publish_list']:
                        if "publish_info" in item:
                            publish_info= json.loads(item['publish_info'])
                       
                            if "appmsgex" in publish_info:
                                # info = '"{}","{}","{}","{}"'.format(str(item["aid"]), item['title'], item['link'], str(item['create_time']))
                                for item in publish_info["appmsgex"]:
                                    if Gather_Content:
                                        if not super().HasGathered(item["aid"]):
                                            logger.debug(f"[文章获取-Web模式] 采集文章内容 - 公众号: {Mps_title}, 文章ID: {item['aid']}, 标题: {item.get('title', '未知')[:50]}")
                                            item["content"] = self.content_extract(item['link'])
                                    else:
                                        item["content"] = ""
                                    item["id"] = item["aid"]
                                    item["mp_id"] = Mps_id
                                    if CallBack is not None:
                                        super().FillBack(CallBack=CallBack,data=item,Ext_Data={"mp_title":Mps_title,"mp_id":Mps_id})
                                        page_articles += 1
                    total_articles += page_articles
                    logger.info(f"[文章获取-Web模式] 第{i+1}页获取成功 - 公众号: {Mps_title}, 本页文章数: {page_articles}, 累计文章数: {total_articles}")
                    print(f"第{i+1}页爬取成功\n")
                # 翻页
                i += 1
            except requests.exceptions.Timeout:
                logger.error(f"[文章获取-Web模式] 请求超时 - 公众号: {Mps_title}, 页码: {i+1}")
                print("Request timed out")
                break
            except requests.exceptions.RequestException as e:
                logger.error(f"[文章获取-Web模式] 请求异常 - 公众号: {Mps_title}, 页码: {i+1}, 错误: {str(e)}")
                print(f"Request error: {e}")
                break
            except Exception as e:
                logger.error(f"[文章获取-Web模式] 处理异常 - 公众号: {Mps_title}, 页码: {i+1}, 错误: {str(e)}")
                import traceback
                logger.error(f"[文章获取-Web模式] 错误堆栈: {traceback.format_exc()}")
                break
            finally:
                super().Item_Over(item={"mps_id":Mps_id,"mps_title":Mps_title},CallBack=Item_Over_CallBack)
        logger.info(f"[文章获取-Web模式] 获取完成 - 公众号: {Mps_title}, 总共获取文章数: {total_articles}")
        super().Over(CallBack=Over_CallBack)
        pass