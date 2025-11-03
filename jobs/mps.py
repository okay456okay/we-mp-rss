from datetime import datetime
from core.models.article import Article
from .article import UpdateArticle,Update_Over
import core.db as db
from core.wx import WxGather
from core.log import logger
from core.task import TaskScheduler
from core.models.feed import Feed
from core.config import cfg,DEBUG
from core.print import print_info,print_success,print_error
from driver.wx import WX_API
from driver.success import Success
wx_db=db.Db(tag="任务调度")
def fetch_all_article():
    print("开始更新")
    wx=WxGather().Model()
    try:
        # 获取公众号列表
        mps=db.DB.get_all_mps()
        for item in mps:
            try:
                wx.get_Articles(item.faker_id,CallBack=UpdateArticle,Mps_id=item.id,Mps_title=item.mp_name, MaxPage=1)
            except Exception as e:
                print(e)
        print(wx.articles) 
    except Exception as e:
        print(e)         
    finally:
        logger.info(f"所有公众号更新完成,共更新{wx.all_count()}条数据")


def test(info:str):
    print("任务测试成功",info)

from core.models.message_task import MessageTask
# from core.queue import TaskQueue
from .webhook import web_hook
import time
import traceback
interval=int(cfg.get("interval",60)) # 每隔多少秒执行一次
def do_job(mp=None,task:MessageTask=None):
        """
        执行单个公众号的文章同步任务
        
        Args:
            mp: Feed对象，包含公众号信息
            task: MessageTask对象，包含任务信息
        """
        if mp is None:
            logger.error(f"任务({task.id if task else 'None'})执行失败: 公众号对象为空")
            return
            
        start_time = time.time()
        mp_name = mp.mp_name if mp else "未知公众号"
        mp_id = mp.id if mp else "未知ID"
        task_id = task.id if task else "未知任务"
        
        logger.info(f"[公众号同步] 开始同步公众号 - 任务ID: {task_id}, 公众号ID: {mp_id}, 公众号名称: {mp_name}, 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查缓存：如果该公众号近N小时已有文章，则跳过同步
        sync_cache_hours = int(cfg.get("sync.cache_hours", 8))  # 默认8小时
        if sync_cache_hours > 0:
            try:
                from core.models.article import Article
                from core.models.base import DATA_STATUS
                import time as time_module
                
                current_time = int(time_module.time())
                cache_time_threshold = current_time - (sync_cache_hours * 3600)  # 转换为秒
                
                session = db.DB.get_session()
                # 查询该公众号在指定时间范围内是否有文章
                recent_article = session.query(Article).filter(
                    Article.mp_id == mp_id,
                    Article.publish_time >= cache_time_threshold,
                    Article.status == DATA_STATUS.ACTIVE
                ).order_by(Article.publish_time.desc()).first()
                
                if recent_article:
                    logger.info(f"[公众号同步] 跳过同步 - 公众号: {mp_name}, 公众号ID: {mp_id}, 原因: 近{sync_cache_hours}小时内已有文章 (最新文章发布时间: {datetime.fromtimestamp(recent_article.publish_time).strftime('%Y-%m-%d %H:%M:%S')})")
                    print_success(f"任务({task_id})[{mp_name}]跳过同步，近{sync_cache_hours}小时内已有文章")
                    return
                else:
                    logger.debug(f"[公众号同步] 继续同步 - 公众号: {mp_name}, 公众号ID: {mp_id}, 近{sync_cache_hours}小时内无文章")
            except Exception as e:
                logger.warning(f"[公众号同步] 缓存检查失败，继续同步 - 公众号: {mp_name}, 错误: {str(e)}")
                # 缓存检查失败不影响同步流程，继续执行
        
        all_count=0
        wx=WxGather().Model()
        success = False
        error_msg = None
        
        try:
            logger.info(f"[公众号同步] 正在获取文章列表 - 公众号: {mp_name}, faker_id: {mp.faker_id if mp else 'None'}")
            wx.get_Articles(mp.faker_id,CallBack=UpdateArticle,Mps_id=mp.id,Mps_title=mp.mp_name, MaxPage=1,Over_CallBack=Update_Over,interval=interval)
            success = True
            logger.info(f"[公众号同步] 文章列表获取成功 - 公众号: {mp_name}, 获取到文章数: {wx.all_count()}")
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logger.error(f"[公众号同步] 同步失败 - 公众号: {mp_name}, 公众号ID: {mp_id}, 任务ID: {task_id}, 错误信息: {error_msg}")
            logger.error(f"[公众号同步] 错误堆栈: {error_trace}")
            print_error(e)
            # raise
        finally:
            count=wx.all_count()
            all_count+=count
            end_time = time.time()
            duration = end_time - start_time
            
            # 记录同步结果
            if success:
                logger.info(f"[公众号同步] 同步完成 - 公众号: {mp_name}, 公众号ID: {mp_id}, 任务ID: {task_id}, 成功获取文章数: {count}, 耗时: {duration:.2f}秒")
            else:
                logger.warning(f"[公众号同步] 同步异常完成 - 公众号: {mp_name}, 公众号ID: {mp_id}, 任务ID: {task_id}, 获取文章数: {count}, 耗时: {duration:.2f}秒, 错误: {error_msg}")
            
            # 如果同步失败，发送通知
            if not success and error_msg:
                try:
                    from core.notice import notice
                    from core.config import cfg
                    
                    # 获取配置的通知webhook地址
                    notice_config = cfg.get('notice', {})
                    webhook_urls = []
                    
                    # 收集所有配置的webhook地址
                    if notice_config.get('dingding'):
                        webhook_urls.append(notice_config['dingding'])
                    if notice_config.get('wechat'):
                        webhook_urls.append(notice_config['wechat'])
                    if notice_config.get('feishu'):
                        webhook_urls.append(notice_config['feishu'])
                    if notice_config.get('custom'):
                        webhook_urls.append(notice_config['custom'])
                    
                    # 发送失败通知到所有配置的webhook
                    if webhook_urls:
                        error_title = f"公众号同步失败 - {mp_name}"
                        error_text = f"""### 公众号同步失败通知

**公众号名称**: {mp_name}
**公众号ID**: {mp_id}
**任务ID**: {task_id}
**错误信息**: {error_msg}
**获取文章数**: {count}
**耗时**: {duration:.2f}秒
**失败时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查公众号配置或网络连接是否正常。"""
                        
                        for webhook_url in webhook_urls:
                            try:
                                # notice函数会自动根据webhook地址识别通知类型（钉钉、企微、飞书等）
                                notice(webhook_url, error_title, error_text)
                                logger.info(f"[公众号同步] 失败通知已发送 - 公众号: {mp_name}, webhook: {webhook_url[:50]}...")
                            except Exception as e:
                                logger.error(f"[公众号同步] 发送失败通知失败 - 公众号: {mp_name}, webhook: {webhook_url[:50]}..., 错误: {str(e)}")
                    else:
                        logger.debug(f"[公众号同步] 未配置通知webhook，跳过发送失败通知 - 公众号: {mp_name}")
                except Exception as e:
                    logger.error(f"[公众号同步] 发送失败通知异常 - 公众号: {mp_name}, 错误: {str(e)}")
            
            try:
                from jobs.webhook import MessageWebHook 
                tms=MessageWebHook(task=task,feed=mp,articles=wx.articles)
                web_hook(tms)
            except Exception as e:
                logger.error(f"[公众号同步] WebHook调用失败 - 公众号: {mp_name}, 错误: {str(e)}")
            
            if success:
                print_success(f"任务({task_id})[{mp_name}]执行成功,{count}成功条数")
            else:
                print_error(f"任务({task_id})[{mp_name}]执行异常,{count}条数,错误:{error_msg}")

from core.queue import TaskQueue
def add_job(feeds:list[Feed]=None,task:MessageTask=None,isTest=False):
    """
    将公众号同步任务添加到队列
    
    Args:
        feeds: Feed对象列表，要同步的公众号列表
        task: MessageTask对象，任务信息
        isTest: 是否为测试任务
    """
    if feeds is None or len(feeds) == 0:
        logger.warning(f"[任务队列] 没有公众号需要同步 - 任务ID: {task.id if task else 'None'}")
        return
        
    task_id = task.id if task else "未知任务"
    task_name = task.name if task else "未知任务名"
    
    logger.info(f"[任务队列] 开始添加同步任务 - 任务ID: {task_id}, 任务名称: {task_name}, 公众号数量: {len(feeds)}, 测试模式: {isTest}")
    
    if isTest:
        TaskQueue.clear_queue()
        logger.info(f"[任务队列] 测试模式，已清空队列")
    
    added_count = 0
    for feed in feeds:
        if feed is None:
            logger.warning(f"[任务队列] 跳过空的Feed对象")
            continue
            
        TaskQueue.add_task(do_job,feed,task)
        added_count += 1
        
        logger.info(f"[任务队列] 公众号已加入队列 - 公众号名称: {feed.mp_name}, 公众号ID: {feed.id}, 任务ID: {task_id}")
        
        if isTest:
            print(f"测试任务，{feed.mp_name}，加入队列成功")
            reload_job()
            break
        print(f"{feed.mp_name}，加入队列成功")
    
    queue_info = TaskQueue.get_queue_info()
    logger.info(f"[任务队列] 任务添加完成 - 任务ID: {task_id}, 已添加公众号数: {added_count}, 队列状态: {queue_info}")
    print_success(TaskQueue.get_queue_info())
    pass
import json
def get_feeds(task:MessageTask=None):
    """
    获取任务关联的公众号列表
    
    Args:
        task: MessageTask对象，包含任务信息
        
    Returns:
        公众号Feed对象列表
    """
    if task is None:
        logger.warning(f"[获取公众号列表] 任务对象为空，返回所有公众号")
        return wx_db.get_all_mps()
    
    try:
        mps = json.loads(task.mps_id)
        ids=",".join([item["id"]for item in mps])
        logger.info(f"[获取公众号列表] 任务ID: {task.id}, 从任务配置中获取公众号ID列表: {ids}")
        mps=wx_db.get_mps_list(ids)
        if len(mps)==0:
            logger.warning(f"[获取公众号列表] 任务配置的公众号列表为空，返回所有公众号 - 任务ID: {task.id}")
            mps=wx_db.get_all_mps()
        else:
            logger.info(f"[获取公众号列表] 成功获取公众号列表 - 任务ID: {task.id}, 公众号数量: {len(mps)}, 公众号名称: {[mp.mp_name for mp in mps]}")
        return mps
    except Exception as e:
        logger.error(f"[获取公众号列表] 获取公众号列表失败 - 任务ID: {task.id if task else 'None'}, 错误: {str(e)}")
        logger.error(f"[获取公众号列表] 错误堆栈: {traceback.format_exc()}")
        # 如果出错，返回所有公众号
        return wx_db.get_all_mps()
scheduler=TaskScheduler()
def reload_job():
    print_success("重载任务")
    scheduler.clear_all_jobs()
    TaskQueue.clear_queue()
    start_job()

def run(job_id:str=None,isTest=False):
    from .taskmsg import get_message_task
    tasks=get_message_task(job_id)
    if not tasks:
        print("没有任务")
        return None
    for task in tasks:
            #添加测试任务
            from core.print import print_warning
            print_warning(f"{task.name} 添加到队列运行")
            add_job(get_feeds(task),task,isTest=isTest)
            pass
    return tasks
def start_job(job_id:str=None):
    """
    启动定时任务调度器
    
    Args:
        job_id: 可选的任务ID，如果指定则只启动该任务
    """
    from .taskmsg import get_message_task
    tasks=get_message_task(job_id)
    if not tasks:
        logger.warning(f"[定时任务] 没有找到任务 - job_id: {job_id}")
        print("没有任务")
        return
    
    logger.info(f"[定时任务] 开始启动定时任务调度器 - 任务数量: {len(tasks)}, job_id: {job_id}")
    tag="定时采集"
    
    added_count = 0
    for task in tasks:
        cron_exp=task.cron_exp
        if not cron_exp:
            logger.error(f"[定时任务] 任务没有设置cron表达式 - 任务ID: {task.id}, 任务名称: {task.name}")
            print_error(f"任务[{task.id}]没有设置cron表达式")
            continue
      
        try:
            scheduler_job_id=scheduler.add_cron_job(add_job,cron_expr=cron_exp,args=[get_feeds(task),task],job_id=str(task.id),tag="定时采集")
            added_count += 1
            logger.info(f"[定时任务] 成功添加定时任务 - 任务ID: {task.id}, 任务名称: {task.name}, cron表达式: {cron_exp}, 调度器任务ID: {scheduler_job_id}")
            print(f"已添加任务: {scheduler_job_id}")
        except Exception as e:
            logger.error(f"[定时任务] 添加定时任务失败 - 任务ID: {task.id}, 任务名称: {task.name}, cron表达式: {cron_exp}, 错误: {str(e)}")
            logger.error(f"[定时任务] 错误堆栈: {traceback.format_exc()}")
    
    try:
        scheduler.start()
        logger.info(f"[定时任务] 定时任务调度器启动成功 - 已添加任务数: {added_count}")
        print("启动任务")
    except Exception as e:
        logger.error(f"[定时任务] 定时任务调度器启动失败 - 错误: {str(e)}")
        logger.error(f"[定时任务] 错误堆栈: {traceback.format_exc()}")
def start_all_task():
      #开启自动同步未同步 文章任务
    from jobs.fetch_no_article import start_sync_content
    start_sync_content()
    start_job()
if __name__ == '__main__':
    # do_job()
    # start_all_task()
    pass