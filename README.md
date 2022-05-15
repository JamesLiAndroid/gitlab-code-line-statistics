# gitlab-code-line-statistics
gitlab api接口代码统计

运行环境：python 3.8

主要功能：统计前一天或者前一个月的代码提交行数，例如今天运行，统计昨天的所有用户的提交的有效行数！

解释：

1. 从项目到分支再到单次commit进行统计，需要去除merge操作，去除merge操作后重复commitId的问题
2. kpi项目，后续可以对接研发平台接口信息上传数据，这里只是生成csv文件，csv文件作为一个依据，可以在接口不能用的时候也能看到统计数据
3. 提供按天和按月统计，公司内以天为单位统计，最终从研发平台汇总数据

参考地址：

1. https://fairysen.com/542.html
2. https://www.infoq.cn/article/tmqsgtww26ki0js0svkk