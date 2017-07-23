#!/usr/bin/env python
#coding=utf-8

'''
@author: wujx
@file: JenkinsWorker2.py
@time: 2017-4-6
'''

import importlib
import os
import types
import unittest
from BaseFunc import excuteSuiteExportReport,analysisResult

# '''
# @分片接口初始化自动化测试脚本
# '''
# def InitialMultipart():
#     '''
#      Function: give one module name, this code will find those class prefixed with "myUT_"
#                and run their functions whose name is prefixed with 'test_' automatically
#                Here, in this module, you can add as many class as possible as long as their name
#                convenctions are followed.
#     2017-4-6
#     '''
#     #动态导入用例模块
#     module=importlib.import_module("uploadpart")
#     module_dir=dir(module)
#     print("module_dir content %s"%module_dir)
#     suite = unittest.TestSuite()
#     for element in module_dir:
#             #过滤要执行的类内容
#             if(isinstance(element, object) and (element.startswith('myUI_'))):
#                 print("%s is class"%(element))
#                 TestSuitClass = getattr(module, element)
#                 for method in dir(TestSuitClass):
#                     #过滤test_开头的用例函数名
#                     if method.startswith("test_"):
#                         print("method name is %s"%method)
#                         suite.addTest(TestSuitClass(method))
#     #执行用例集合
#     test_result = excuteSuiteExportReport('index.html', suite)
#     analysisResult(test_result)


'''
@分片上传自动化脚本
'''
def uploadpart():
    '''
     Function: give one module name, this code will find those class prefixed with "myUT_"
               and run their functions whose name is prefixed with 'test_' automatically
               Here, in this module, you can add as many class as possible as long as their name
               convenctions are followed.
    2017-4-6
    '''
    #动态导入用例模块
    module=importlib.import_module("AbortMultipartUpload")
    module_dir=dir(module)
    print("module_dir content %s"%module_dir)
    suite = unittest.TestSuite()
    for element in module_dir:
            #过滤要执行的类内容
            if(isinstance(element, object) and (element.startswith('myUI_'))):
                print("%s is class"%(element))
                TestSuitClass = getattr(module, element)
                for method in dir(TestSuitClass):
                    #过滤test_开头的用例函数名
                    if method.startswith("test_"):
                        print("method name is %s"%method)
                        suite.addTest(TestSuitClass(method))
    #执行用例集合
    test_result = excuteSuiteExportReport('AbortMultipartUpload.html', suite)
    analysisResult(test_result)



if __name__== '__main__':
        uploadpart()