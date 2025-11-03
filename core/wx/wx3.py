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
class MpsAppMsg(WxGather):

    # 重写 content_extract 方法
    def content_extract(self,  url):
        try:
            text = super().content_extract(url)
            if text is not None:
                soup = BeautifulSoup(text, 'html.parser')
                # 找到内容
                js_content_div = soup.find('div', {'id': 'js_content'})
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
        super().Start(mp_id=Mps_id)
        if self.Gather_Content:
            Gather_Content=True
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
        while True:
            if i >= MaxPage:
                break
            begin = i * count
            params["begin"] = str(begin)
            print(f"第{i+1}页开始爬取\n")
            # 随机暂停几秒，避免过快的请求导致过快的被查到
            time.sleep(random.randint(0,interval))
            try:
                headers = self.fix_header(url)
                # 记录请求详细信息
                logger.debug(f"[文章获取-AppMsg模式] 发送请求 - 公众号: {Mps_title}, URL: {url}, 参数: {params}")
                resp = session.get(url, headers=headers, params = params, verify=False)
                
                msg = resp.json()
                self._cookies =resp.cookies
                
                # 记录响应详细信息
                ret_code = msg.get('base_resp', {}).get('ret', 'unknown')
                err_msg = msg.get('base_resp', {}).get('err_msg', '')
                logger.debug(f"[文章获取-AppMsg模式] 收到响应 - 公众号: {Mps_title}, ret: {ret_code}, err_msg: {err_msg}, 状态码: {resp.status_code}")
                
                # 如果返回错误，记录完整的请求和响应信息
                if ret_code != 0:
                    logger.error(f"[文章获取-AppMsg模式] API返回错误 - 公众号: {Mps_title}, 请求URL: {url}")
                    logger.error(f"[文章获取-AppMsg模式] 请求参数: {params}")
                    logger.error(f"[文章获取-AppMsg模式] 响应内容: {msg}")
                    logger.error(f"[文章获取-AppMsg模式] HTTP状态码: {resp.status_code}")
                
                # 流量控制了, 退出
                if ret_code == 200013:
                    logger.error(f"[文章获取-AppMsg模式] 触发频率限制 - 公众号: {Mps_title}, 在页码 {begin} 处停止")
                    super().Error("frequencey control, stop at {}".format(str(begin)), code="FrequencyControl")
                    break
                
                if ret_code == 200003:
                    logger.error(f"[文章获取-AppMsg模式] 登录会话失效 - 公众号: {Mps_title}, 在页码 {begin} 处停止")
                    super().Error("Invalid Session, stop at {}".format(str(begin)),code="Invalid Session")
                    break
                if ret_code != 0:
                    # 200002 (invalid args) 等错误不应该清空队列，只跳过当前公众号
                    # 只有200003才是真正的Invalid Session
                    error_code_str = "Invalid Session" if ret_code == 200003 else "ApiError"
                    logger.error(f"[文章获取-AppMsg模式] API返回错误 - 公众号: {Mps_title}, 错误原因: {err_msg}, 错误代码: {ret_code}")
                    super().Error("错误原因:{}:代码:{}".format(err_msg, ret_code), code=error_code_str)
                    break    
                # 如果返回的内容中为空则结束
                if 'publish_page' not in msg:
                    logger.info(f"[文章获取-AppMsg模式] 没有更多文章 - 公众号: {Mps_title}, 在页码 {begin} 处停止")
                    super().Error("all ariticle parsed")
                    break  
                if "publish_page" in msg:
                    msg["publish_page"]=json.loads(msg['publish_page'])
                    for item in msg["publish_page"]['publish_list']:
                        if "publish_info" in item:
                            publish_info= json.loads(item['publish_info'])
                       
                            if "appmsgex" in publish_info:
                                # info = '"{}","{}","{}","{}"'.format(str(item["aid"]), item['title'], item['link'], str(item['create_time']))
                                for item in publish_info["appmsgex"]:
                                    if Gather_Content:
                                        if not super().HasGathered(item["aid"]):
                                            item["content"] = self.content_extract(item['link'])
                                    else:
                                        item["content"] = ""
                                    item["id"] = item["aid"]
                                    item["mp_id"] = Mps_id
                                    if CallBack is not None:
                                        super().FillBack(CallBack=CallBack,data=item,Ext_Data={"mp_title":Mps_title,"mp_id":Mps_id})
                    print(f"第{i+1}页爬取成功\n")
                # 翻页
                i += 1
            except requests.exceptions.Timeout:
                print("Request timed out")
                break
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                break
            finally:
                super().Item_Over(item={"mps_id":Mps_id,"mps_title":Mps_title},CallBack=Item_Over_CallBack)
        super().Over(CallBack=Over_CallBack)
        pass