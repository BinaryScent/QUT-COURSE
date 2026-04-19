# coding: utf-8
import os.path

HOST = 'https://raw.githubusercontent.com/'
OWNER = 'BinaryScent'  #'USTC-Courses'  #'mbinary'#
REPO = 'QUT-COURSE'
BRANCH = 'main'
NAME = 'README.md'  # index.html

PATH = os.path.join(HOST, OWNER, REPO, BRANCH)

WALKDIR = os.path.abspath('.')

TARDIR = 'docs'
if not os.path.exists(TARDIR):
    TARDIR = 'docs'

IGNORE = ['utils', 'docs', '__pycache__', '_config.yml','images', 'web', 'courses']

DOWNLOAD = 'https://download-directory.github.io/?url=https://github.com/' + OWNER + '/' + REPO + '/tree/' + BRANCH + '/'

HTML = '''
<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">
    <title> 青岛理工大学课程资源</title>
</head>
# 青岛理工大学课程资源

<div>
  <h2>
    <a href="../index.html">&nbsp;&nbsp;<i class="fas fa-backward"></i>&nbsp;</a>
    :/{cur}
  </h2>
</div>

## 说明
- 列表根据拼音排序
- 点击 Files 的链接下载二进制文件
- 或者打开文本文件(markdown 文件经过渲染)

<h2> Directories &nbsp; <a href="{DOWNLOAD}" style="color:red;text-decoration:underline;" target="_black"><i class="fas fa-download"></i></a></h2>

<ul>{dirLst}</ul>

## Files
<ul>{fileLst}</ul>

---
<div style="text-decration:underline;display:inline">
  <a href="https://github.com/BinaryScent/QUT-COURSE.git" target="_blank" rel="external"><i class="fab fa-github"></i>&nbsp; GitHub</a>
  <a href="mailto:far411524@gmail.com?subject=反馈与建议" style="float:right" target="_blank" rel="external"><i class="fas fa-envelope"></i>&nbsp; Feedback</a>
</div>
---

{readme}
'''

#* 非zip, 非以'.'开头的文件多于 3 个的目录下都有个 zip 文件：`-DIRECTORY 目录下的\d+个文件.zip`,包含当前目录下的一些文件, 这样方便大家一键下载. (在 git commit前, 运行 `./before__commit.sh`可以自动生成)

README = r'''
![](images/logo.png)

# 青岛理工大学课程资源

[![Stars](https://img.shields.io/github/stars/BinaryScent/QUT-COURSE.svg?label=Stars&style=social)](https://github.com/BinaryScent/QUT-COURSE/stargazers)
[![Forks](https://img.shields.io/github/forks/BinaryScent/QUT-COURSE.svg?label=Forks&style=social)](https://github.com/BinaryScent/QUT-COURSE/network/members)
[![build](https://github.com/BinaryScent/QUT-COURSE/workflows/build/badge.svg)]()
[![repo-size](https://img.shields.io/github/repo-size/BinaryScent/QUT-COURSE.svg)]()
[![License](https://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

>>本仓库旨在为青岛理工大学提供开放课程资源，打造共享平台，欢迎青理学子贡献。

# 目录索引
* [版权说明](#版权说明)
* [反馈方式](#反馈方式)
* [资料下载](#资料下载)
* [资料结构](#资料结构)
* [课程目录](#课程目录)
* [贡献](#贡献)

# 版权说明
本仓库分享资料遵守其创作者之规定, 由同学自愿投稿，仅接收学生原创的或者获得授权的资源。

对无特别声明的资料，谨以[知识共享署名 - 非商业性使用 - 相同方式共享 4.0 国际许可协议](http://creativecommons.org/licenses/by-nc-sa/4.0/) 授权。![](https://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png)

请创作者及公众监督，如有资料违反许可协议，请告知我们改正错误。

# 反馈方式
- [issue](https://github.com/BinaryScent/QUT-COURSE/issues/new)
- <a href="mailto:far411524@gmail.com?subject=QUT-Course-FeedBack">email</a>

# 资料下载
[戳我(●'◡'●)](https://BinaryScent.github.io/QUT-COURSE)

# 资料结构
课程放在对应的开课学院下，所以先确定自己的开课学院，再确定课程名
课程目录结构如下：
```
course(课程名)
├ homeworks(作业)
├ labs(实验)
├ exams(考试)
├ notes(笔记)
└ README.md
```

# 课程目录
**根据拼音字母排序**, 可以通过在此页面搜索课程名快速定位。

{index}

# 贡献

>感谢您的贡献 :smiley:

- 仅接受学生原创的或者获得授权的资源
- GitHub 上不能直接上传大于 100Mb 的文件。对于超过 100 Mb 的文件，可以存在网盘，然后在 README.md 中贴上链接
- 文件内容的改动会使 git 重新上传, 在没有必要的情况下, 不要对二进制文件做任何更改.

'''
