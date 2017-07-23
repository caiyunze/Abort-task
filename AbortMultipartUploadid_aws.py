#!/usr/bin/env python
#coding=utf-8

import subprocess
import requests
import datetime
from hashlib import sha1
import hmac
import base64
import ConfigParser
import time
import hashlib
import os
import inspect
from BaseFunc import getfileinfo
from xml.etree import ElementTree
from BaseFunc import complete_xml_200,generate_token,compare_file_md5,compare_xml_tag,code_message_info
import multiprocessing
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append('..')
from BaseFunc import generate_token,compare_xml_tag,code_message_info,compare_xml_200,compare_xml_200_specialstring

#获取当前执行函数的名称
def get_current_function_name():
    return inspect.stack()[1][3]


#用例内容
class myUI_AbortMultipartuploadid():
    def __init__(self):
        self.cf = ConfigParser.ConfigParser()
        with open('Uploadslice.config') as file:
            self.cf.readfp(file)  # 读取文件信息
            self.bucket = self.cf.get('bucket', 'aws_bucket')  #
            #########################################文件名称#############
            self.minetype = self.cf.get('filename', 'minetype')#w无后缀的文件
            self.filename = self.cf.get('filename', 'filename')#文件名称,值有一个分片的文件，大小为12m
            self.filename_4m = self.cf.get('filename','filename_4m') #只有一个分片，且分片大小为4m
            self.filename_first_less4m = self.cf.get('filename','filename_first_less4m') #第一个分片的大小小于4m
            self.filename_last_less4m = self.cf.get('filename','filename_last_less4m') #最后一个分片的大小小于4m
            self.xmlfile = self.cf.get('filename','xmlfile')#xml文件名称
            self.errorxmlfile = self.cf.get('filename','errorxmlfile')
            ###########################################文件地址@###############
            self.filepath_4m = self.cf.get('filename','slicepath')#分片文件地址,只有一个分片文件,文件大小为4m
            self.filepath_first_less4m = self.cf.get('filename','filepath_first_less4m')#第一个分片文件大小小于4m
            self.filepath_last_less4m = self.cf.get('filename','filepath_last_less4m')#第一个分片文件大小小于4m
            self.slicepath = self.cf.get('filename','windows_path')#分片文件地址,只有一个分片文件
            self.moreslicepath = self.cf.get('filename','moreslicepath')#多个分片文件地址
            ##################################################################
            self.resource_path = self.cf.get('filename','resource_path') #原始文件，后面用于对比下载文件的md5值是否与其一致
            self.download_path = self.cf.get('download','savepath') +self.filename  #下载后的文件地址，后面用于比对是否和原文件一致
            self.s3_url = self.cf.get('urlinfo','aws_url')#s3 rul地址
            self.S3_ACCESS_KEY_ID = self.cf.get('key','aws_ak')
            self.S3_SECRET_ACCESS_KEY = self.cf.get('key','aws_sk')
            self.uploadid = ''
            ########################分片文件信息##############################
            self.slice_list = getfileinfo(self.slicepath)
            ######################列举参数####################################
            self.maxparts=3
            self.partnumbermarker=1
            ########获取http所需的GMT格式时间#################################
            GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
            self.date = datetime.datetime.utcnow().strftime(GMT_FORMAT)
            #获取自定义的xamzdate时间值##################################
            time.sleep(0.5)
            self.xamzdate = datetime.datetime.utcnow().strftime(GMT_FORMAT)
            ############初始化队列列荣#######################
            manager = multiprocessing.Manager()
            self.queue = manager.Queue()
            ###############设置返回success格式###################
            self.success= '\033[32m########################################\n                 SUCCESS\n########################################\033[0m'
            self.fail= '\033[31m########################################\n                 FAIL\n########################################\033[0m'
    '''
    三个初始化函数
    @1正常的请求初始化，获取uploadid ，并写入到配置文件中
    @2正确的分片上传请求，上传分片数据
    @3遍历要上传的分片，循环上传
    '''
    def InitialMultipartUpload_ok(self,objectname):
        '初始化，获取分片和合成使用到的uplaodid'
        resource='/'+self.bucket+'/'+objectname+'?uploads'
        print '>>>>resource信息：',resource
        contentType=''
        contentMD5=''
        method='POST'
        date=self.date
        #token的算是 HMAC_SHA1算法，然后再次进行base64加密
        #HMAC运算利用哈希算法，以一个密钥和一个消息为输入，生成一个消息摘要作为输出
        token = generate_token(method,contentMD5,contentType,date,resource,self.S3_ACCESS_KEY_ID,self.S3_SECRET_ACCESS_KEY)
        print '>>>>鉴权后的token信息:\n',token
        headers = {'Authorization':token,'Date':self.date}
        print '>>>>请求头部信息headers:\n',headers
        s3url = self.s3_url+resource
        print '>>>>请求的s3url:\n',self.s3_url
        rq = requests.post(url=s3url,headers=headers,timeout=30)
        status =  str(rq.status_code)
        print '响应头部信息：',rq.headers
        if status == '200':
            return_data = rq.text
            print rq.headers
            print '>>>>响应状态码：',status
            print '>>>>返回结果：\n', rq.text
            #获取当前执行得到upploadid，并写入配置文件
            cf = ConfigParser.ConfigParser()
            cfgfile =cf.read("MultipartUpload.config")
            rootxml = ElementTree.fromstring(return_data)
            for  child in rootxml.findall('{http://s3.amazonaws.com/doc/2006-03-01/}UploadId'):
                self.uploadid = child.text
                cf.set('uploadId','uploadid',child.text)
                cf.write(open("MultipartUpload.config",'w'))
            print '初始化的uploadid：',self.uploadid
        else:
            print '响应的错误码:',status
            print rq.text
            print self.fail
            return 'FAIL'

    def MultipartUpload_ok(self,objectname,slicepath,slicename,partnum):
        '分片上传，传入文件地址，文件名称objectname，上传的partnum'
        #进程共享数据
        partnum_etag_dict = {}
        #分段文件名称
        objectname = objectname #文件的名称
        print '>>>>本次上传的文件名称：',objectname
        file_path = slicepath+slicename
        print '>>>>分片文件地址信息：',slicepath
        m2 = hashlib.md5()
        #加载分段文件
        with open(file_path,'rb') as f:
            # md5值获取，如果文件太大，分行获取，防止内存加载过多
            d = f.read()
            m2.update(d)
            self.md5 = base64.b64encode(m2.hexdigest())
            #resource='/{0}/{1}'.format(self.bucket,objectname)
            resource = '/{0}/{1}?partNumber={2}&uploadId={3}'.format(self.bucket,objectname,partnum,self.uploadid)
            print '>>>>resource信息:',resource
            contentType=''
            contentMD5=''
            method='PUT'
            #token的算是 HMAC_SHA1算法，然后再次进行base64加密
            #HMAC运算利用哈希算法，以一个密钥和一个消息为输入，生成一个消息摘要作为输出
            stringToSign='{0}\n{1}\n{2}\n{3}\n{4}'.format(method,contentMD5,contentType,self.date,resource)
            print '>>>>校验信息：',stringToSign
            my_sign = hmac.new(self.S3_SECRET_ACCESS_KEY,stringToSign,sha1).digest()
            signature = base64.b64encode(my_sign)
            #获取最后的token
            token = '{0} {1}:{2}'.format('AWS',self.S3_ACCESS_KEY_ID,signature)
            print '>>>>token信息：',token
            print '>>>>uploadid信息',self.uploadid
            #头部信息###############
            headers = {'Authorization': token,  'Date': self.date}
            print '>>>>headers:', headers
            ######组合url地址######################################################
            s3url = '{0}{1}'.format(self.s3_url,resource)
            print '>>>>s3url:', s3url
            #####put 上传分段文件数据##############################################
            rq = requests.put(s3url,data=d ,headers=headers,timeout=300)
            status = str(rq.status_code)
            print '>>>>返回状态码：',status
            #分片上传响应etag值在头部中
            return_header =  rq.headers
            print '>>>>返回头部结果：', return_header
            #对返回状态码做判断，并返回比对结果
            if status == '200':
                etag = return_header['ETag']
                partnum_etag_dict['PartNumber']=str(partnum)
                partnum_etag_dict['ETag']=etag.strip('"')
                print '>>>>头部获取到的[etag]信息：',etag
                self.queue.put(str(partnum_etag_dict))
                print self.success
                return 'SUCCESS'
            else:
                print rq.text
                print self.fail
                return 'FAIL'

       #多线程执行分片上传任务

    def run_upload(self,objectname,slicepath):
        '遍历所有要上传你的分片，并上传分片文件'
        self.InitialMultipartUpload_ok(objectname)
        xml_etag = []
        threads=[]
        #对返回的分片文件名称进行排序，从小到大
        slice_list = getfileinfo(slicepath)
        slice_list_sorted = sorted(slice_list[0].keys())
        print slice_list_sorted
        for index,key in enumerate(slice_list_sorted):
            result = self.MultipartUpload_ok(objectname,slicepath,key,index+1)
        if result == 'SUCCESS':
            while self.queue.qsize():
                xml_etag.append(eval(self.queue.get()))
            print '>>>>待写入的partnum和etag信息：',xml_etag
        else:
            print '分片上传失败，无法合成文件'

    '''
    @正常的请求:列举分片数据，url请求资源带 uploadid&max-parts=max&part-number-marker=marker
    返回所有分片数据
    '''
    def test_AbortMultipartUploadid(self):
            'LIST 上传的分片信息，鉴权的子资源只有bucketname,objectname,uploadid，URL需要带上所有参数信息\
            同时处理先后顺序为：upload-id, max-parts,part-number-marker'
            #self.run_upload(self.filename,self.slicepath)
            uploadid = 'VIVKlbJlIz17TkWsrPT07Vcvd27GU7X3Ya3qt2Kqna47rpHd25o2aqvAsBUPKB8u1XEkPzKosiBmMBi8724S2A--'
            #打印当前执行函数的名称
            print '>>>>当前执行函数名称:',"%s.%s"%(self.__class__.__name__,get_current_function_name())
            resource= '/{0}/{1}?uploadId={2}'.format(self.bucket,self.filename,uploadid )
            #'/'+self.bucket+'/'+self.filename+'?uploads'
            print '>>>>resource信息：',resource
            contentType=''
            contentMD5=''
            method='DELETE'
            date=self.date
            #token的算是 HMAC_SHA1算法，然后再次进行base64加密
            #HMAC运算利用哈希算法，以一个密钥和一个消息为输入，生成一个消息摘要作为输出
            token = generate_token(method,contentMD5,contentType,date,resource,self.S3_ACCESS_KEY_ID,self.S3_SECRET_ACCESS_KEY)
            print '>>>>鉴权后的token信息:\n',token
            headers = {'Authorization':token,'Date':self.date}
            print '>>>>请求头部信息headers:\n',headers
            s3url = self.s3_url+resource
            print '>>>>请求的s3url:\n',s3url
            rq = requests.delete(url=s3url,headers=headers)
            status =  str(rq.status_code)
            print '返回状态码 ',status
            print '响应头部信息：',rq.headers
            return_data = rq.text #接口返回的内容
            #result = compare_xml_200(return_data,status,self.bucket,self.filename)
            print return_data
            if status == '204':
                print self.success
                result = 'SUCCESS'
            else:
                print self.fail
                result = 'FAIL'
            return result

if __name__ == '__main__':
    aa = myUI_AbortMultipartuploadid()
    #aa.InitialMultipartUpload_ok('test.mp4')
    aa.test_AbortMultipartUploadid()

