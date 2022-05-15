#!/usr/bin/env python
# coding=utf-8

import datetime
import time
import urllib.parse

import gitlab
import collections
import pandas as pd
import json
import os
import sys
from urllib.parse import urlparse, quote, unquote, urlencode

import requests

# 需要先设置这两个参数，才能运行
gitlab_url = "http://192.168.166.202:8181/"
gitlab_access_token = "JBpzNcTKFLzv_cqRYXLt"

# 分钟左右跑完
gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_access_token, timeout=60, api_version='4')

# 获取日期信息
# start_date = datetime.date.today() + datetime.timedelta(-1)
start_date = datetime.date.today() + datetime.timedelta(-30)
# end_date = datetime.date.today() + datetime.timedelta(-1)

# 获取起始时间，获取前一天内的统计信息
day_of_start_time = str(start_date) + " 00:00:00"
day_of_end_time = str(start_date) + " 23:59:59"

# 获取起始时间，获取前一个月内的统计信息
# day_of_start_time = str(start_date) + " 00:00:00"
# day_of_end_time = str(end_date) + " 23:59:59"

# 调用结果远程发送地址
#remote_url = ""

# 统计信息来源
source_url = ""


class DataItem:
    def __init__(self, UserID, Add, Del, Edit, Type, Source):
        self.UserID = UserID
        self.Add = Add
        self.Del = Del
        self.Edit = Edit
        self.Type = Type
        self.Source = Source


# 创建dataItems参数信息
def create_data_items(params):
    list_item = []
    for dataItem in params:
        data_item_instance = DataItem(dataItem["UserID"], int(dataItem["ADD_LINES"]),
                                      int(dataItem["DEL_LINES"]), 0, dataItem["TYPE"], dataItem["SOURCE"])
        list_item.append(data_item_instance.__dict__)

    return list_item


def main_args(argv):
    """
    主函数，以传参方式实现
    :param argv:
    :return:
    """
    # 传入三个参数，gitlab地址、访问token、一天还是一个月（day or month）
    gitlab_url = argv[1]
    access_token = argv[2]
    day_or_month = argv[3]

    global start_date, day_of_start_time, day_of_end_time, gl, source_url
    # 注意，这里生成前一天或者前一个月的日期信息！
    if "day" == day_or_month:
        start_date = datetime.date.today() + datetime.timedelta(-1)
        day_of_start_time = str(start_date) + " 00:00:00"
        day_of_end_time = str(start_date) + " 23:59:59"
    else:
        start_date = datetime.date.today() + datetime.timedelta(-30)
        end_date = datetime.date.today() + datetime.timedelta(-1)
        day_of_start_time = str(start_date) + " 00:00:00"
        day_of_end_time = str(end_date) + " 23:59:59"

    gl = gitlab.Gitlab(gitlab_url, private_token=access_token, timeout=60, api_version='4')
    source_url = gitlab_url
    url_parse = urlparse(gitlab_url)
    # 在windows下，需要先创建好文件才能正常读写
    # 在Linux下不需要，直接运行即可
    file_name = "D:\Dev\Python\workspace\gitlab-code-line-statistics\gitlab_" + str(url_parse.hostname) + "_" + day_or_month + "_" + str(start_date) + ".csv"
    print("生成文件名称为：", file_name)
    csv(file_name)


# 输出格式化
def str_format(txt):
    lenTxt = len(txt)
    lenTxt_utf8 = len(txt.encode('utf-8'))
    size = int((lenTxt_utf8 - lenTxt) / 2 + lenTxt)
    length = 20 - size
    return length


def get_gitlab():
    """
    gitlab API
    """
    commit_result_list = []
    projects = gl.projects.list(owned=True, all=True)
    num = 0
    for project in projects:
        num += 1
        print("查看了%d个项目" % num)
        print("项目名称为：", project.name)

        # 屏蔽特殊项目影响
        if "Monitoring" == project.name:
            continue
        for branch in project.branches.list():
            commits = project.commits.list(all=True, query_parameters={'since': day_of_start_time, 'until': day_of_end_time,
                                                                       'ref_name': branch.name})

            for commit in commits:
                if "Merge" in commit.title or "Merge" in commit.message or "合并" in commit.title or "合并" in commit.message:  # 不统计合并操作
                    continue
                com = project.commits.get(commit.id)

                pro = {}
                try:
                    # 筛选单次提交行数超过10000行的操作
                    if com.stats["total"] > 10000 or com.stats["additions"] > 10000 or com.stats["deletions"] > 10000:
                        continue
                    # print(project.path_with_namespace,com.author_name,com.stats["total"])
                    pro["projectName"] = project.path_with_namespace
                    pro["authorName"] = com.author_name
                    pro["authorEmail"] = com.committer_email
                    pro["branch"] = branch.name
                    pro["additions"] = com.stats["additions"]
                    pro["deletions"] = com.stats["deletions"]
                    pro["commitNum"] = com.stats["total"]
                    pro["commitId"] = commit.id
                    commit_result_list.append(pro)
                except Exception as e:
                    print("有错误, 请检查: \n", e)

    return commit_result_list


# 去重操作
# 结构是数组内带字典，根据将不重复的字典值加入列表中，达到去重的作用
def delete_duplicate_str(data, key):
    new_data = [] # 用于存储去重后的list
    values = []   # 用于存储当前已有的值
    for dic in data:
        if dic[key] not in values:
            new_data.append(dic)
            values.append(dic[key])
    return new_data


def personal_stats():
    """
    单个人统计信息
    :return:
    """
    ret = {}

    # 根据commitID去重，此处是为了解决分支合并后，不同分支内重复commitId导致统计不准确的问题
    # 单个commitId只统计一次
    commit_result_list = get_gitlab()
    result_no_duplicated = delete_duplicate_str(commit_result_list, "commitId")

    print("去重后的数据为：", result_no_duplicated)

    # 循环统计数据
    for ele in result_no_duplicated:
        key = ele["projectName"] + ele["authorName"] + ele["branch"]
        if key not in ret:
            ret[key] = ele
            ret[key]["commitTotal"] = 1
        else:
            ret[key]["additions"] += ele["additions"]
            ret[key]["deletions"] += ele["deletions"]
            ret[key]["commitNum"] += ele["commitNum"]
            ret[key]["commitTotal"] += 1

    result_list = []
    single_per_statistic = []
    for key, v in ret.items():
        v["项目名"] = v.pop("projectName")
        v["开发者"] = v.pop("authorName")
        v["开发者邮箱"] = v.pop("authorEmail")
        v["分支"] = v.pop("branch")
        v["添加代码行数"] = v.pop("additions")
        v["删除代码行数"] = v.pop("deletions")
        v["提交总行数"] = v.pop("commitNum")
        v["提交次数"] = v["commitTotal"]
        result_list.append(v)

        # 可以对单个人员运行统计，在日志中打印，实现单个人员数据查看
        # 需要修改为人名信息
        if "lishuaishuai" == v["开发者"]:
            # print("-----------------------------")
            # print(v["项目名"])
            # print(v["开发者"])
            # print(v["分支"])
            # print(v["添加代码行数"])
            # print(v["删除代码行数"])
            # print(v["提交总行数"])
            # print(v["提交次数"])
            single_per_statistic.append(v)
            # print("-----------------------------")

    print("个人统计信息: ", single_per_statistic)

    name = []  # Git工具用户名
    additions = []  # 新增代码数
    deletions = []  # 删除代码数
    total = []  # 总计代码数
    res = {}

    # 生成元组
    for i in result_list:
        for key, value in i.items():
            if key == "开发者":
                name.append(value)
            if key == "添加代码行数":
                additions.append(value)
            if key == "删除代码行数":
                deletions.append(value)
            if key == "提交总行数":
                total.append(value)

    data = list(zip(name, additions, deletions, total))

    # 去重累加
    for j in data:
        name = j[0]
        additions = j[1]
        deletions = j[2]
        total = j[3]
        if name in res.keys():
            res[name][0] += additions
            res[name][1] += deletions
            res[name][2] += total
        else:
            res.update({name: [additions, deletions, total]})
    print("GitUsername           AddCodeline           DelCodeline            AllCodeline")
    result_array = []
    for k in res.keys():
        print(k + " " * str_format(k) + str(res[k][0]) + " " * str_format(str(res[k][0])) + str(res[k][1]) + " " * str_format(str(res[k][1])) + str(res[k][2]))
        # 汇总写入
        result_dict = {"UserID": str(k), "ADD_LINES": str(res[k][0]), "DEL_LINES": str(res[k][1]), "TOTAL_LINES": str(res[k][2]), "StartDate": str(day_of_start_time), "EndDate": str(day_of_end_time), "TYPE": "GIT", "SOURCE": source_url}
        result_array.append(result_dict)

    #print(result_list)
    #print(result_array)
    #result = json.dumps(result_array)
    #print(result)
    return result_array


def csv(csv_name):
    """
    csv
    """

    result = personal_stats()
    df = pd.DataFrame(result, columns=["UserID", "ADD_LINES", "DEL_LINES", "TOTAL_LINES", "StartDate", "EndDate", "TYPE", "SOURCE"])
    df.to_csv(csv_name, index=False, encoding="utf_8_sig")

    # 将获取的数据进行转换
    # result_json = json.dumps(result)
    print("数据信息为：", result)
    # 发送到对应服务中
    # send_result(url_remote, result)


if __name__ == "__main__":
    # 程序调用命令：
    # python python-gitlab-statistics.py "http://192.168.166.202:8181/" "JBpzNcTKFLzv_cqRYXLt" "day"
    print("调试开始时间111111111：", datetime.datetime.now())
    print(day_of_start_time, day_of_end_time)
    main_args(sys.argv)
    print("调试结束时间111111111：", datetime.datetime.now())

