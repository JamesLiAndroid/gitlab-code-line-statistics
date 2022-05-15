#!/usr/bin/bash
# 项目启动脚本
# crontab设置信息，这里以按天统计执行为例子
# 每10分钟执行一次（测试使用）
# */10 * * * * sh +x /root/python/code-statistics/start.sh >> /root/python/venv/running.log 2>&1
# 正式使用，每晚凌晨1点执行
# 0 1 * * * sh +x /root/python/code-statistics/start.sh >> /root/python/venv/running.log 2>&1
# 下面设置是240服务器gitlab访问示例
gitlab_url=''
gitlab_token=''
circle_mode='day'
source /root/python/venv/bin/activate && python /root/python/code-statistics/python_gitlab_statistics.py $gitlab_url $gitlab_token $circle_mode
