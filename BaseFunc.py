#!/usr/bin/env python
#coding=utf-8

import sys
import os
import datetime
import hmac
import base64
import HTMLTestRunner
from hashlib import sha1
import hashlib
import xml.dom.minidom
from xml.etree import ElementTree
import urllib
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


'''
@GMT格式的时间获取
'''
def getdate():
    # 获取http所需的GMT格式时间##############
    GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
    date = datetime.datetime.utcnow().strftime(GMT_FORMAT)
    return date

'''
@GMT格式的时间,16分钟之前的
'''
def getdate_before():
    ######### 获取http所需16分钟前的GMT格式时间##############################
    GMT_FORMAT_before = '%a, %d %b %Y %H:%M:%S GMT'
    date_before = (datetime.datetime.utcnow()-datetime.timedelta(minutes=16)).strftime(GMT_FORMAT_before)
    return date_before

'''
@获取上传数据的MD5值
'''
def get_md5_value(src):
    myMd5 = hashlib.md5()
    myMd5.update(src)
    myMd5_Digest = base64.b64encode(myMd5.digest())
    print '计算出来的MD5值为：', myMd5_Digest
    return myMd5_Digest


'''
@计算上传文件的etag值，用于比对接口返回的etag是否一样
接口返回的是32位MD5 值
@src传入的数据是读取到的文件内容
'''
def get_etag(src):
    myMd5 = hashlib.md5()
    myMd5.update(src)
    myMd5_etag ='\"'+ myMd5.hexdigest()+'\"'
    print '计算出来的MD5值为：', myMd5_etag
    return myMd5_etag


'''
鉴权信息组合，生成最后头部需要的token 信息
@method,请求的方式，post或是get等
@contentMD5,文件的md5值，需要经过base64加密后的
@contentType
@date ,时间日期，格式为GMT
@CanonicalizedResource，接口子资源信息
@sk,用户Sk
@ak,用户AK
@CanonicalizedOBSHeaders='',额外的参数，如x-amz-date，默认为空
'''
def generate_token(method,contentMD5,contentType,date ,CanonicalizedResource,ak,sk,CanonicalizedOBSHeaders=''):
    if CanonicalizedOBSHeaders == '':
        # token的算是 HMAC_SHA1算法，然后再次进行base64加密
        # HMAC运算利用哈希算法，以一个密钥和一个消息为输入，生成一个消息摘要作为输出
        stringToSign = method + '\n' + contentMD5+'\n' + contentType+'\n' + date + '\n' + CanonicalizedResource
        print u'鉴权信息stringToSign: ', stringToSign
        my_sign = hmac.new(sk, stringToSign, sha1).digest()
        signature = base64.b64encode(my_sign)
        token = 'AWS' + ' ' + ak + ':' + signature
    else:
        # token的算是 HMAC_SHA1算法，然后再次进行base64加密
        # HMAC运算利用哈希算法，以一个密钥和一个消息为输入，生成一个消息摘要作为输出
        stringToSign = method + '\n' + contentMD5+'\n' + contentType+'\n' + date + '\n' +'x-amz-date:'+CanonicalizedOBSHeaders+ '\n' + CanonicalizedResource
        print u'鉴权信息stringToSign: ', stringToSign
        my_sign = hmac.new(sk, stringToSign, sha1).digest()
        signature = base64.b64encode(my_sign)
        token = 'AWS' + ' ' + ak + ':' + signature
    print u'生成token信息：', token
    return token

'''
xml文件生成
@managerList：part和etag值的对应关系列表
@xmlfilename：要保存的xml文件名称
'''
def write_to_xml(managerList,xmlfilename):
  #在内存中创建一个空的文档
  doc = xml.dom.minidom.Document()
  #创建一个根节点Managers对象
  root = doc.createElement('CompleteMultipartUpload')
  #将根节点添加到文档对象中
  doc.appendChild(root)
  #遍历节点信息，设置根节点的属性
  for i in managerList :
    nodeManager = doc.createElement('Part')
    nodeName = doc.createElement('PartNumber')
    #给叶子节点name设置一个文本节点，用于显示文本内容
    nodeName.appendChild(doc.createTextNode(str(i['PartNumber'])))
    nodeAge = doc.createElement("ETag")
    nodeAge.appendChild(doc.createTextNode(str(i["ETag"])))
    #将各叶子节点添加到父节点Manager中，
    #最后将Manager添加到根节点Managers中
    nodeManager.appendChild(nodeName)
    nodeManager.appendChild(nodeAge)
    root.appendChild(nodeManager)
  fp = open('E:\\'+xmlfilename, 'wb')
  doc.writexml(fp, indent='\t', addindent='\t', newl='\n', encoding="utf-8")
  fp.close()


'''
生成html格式的测试报告公共方法
@xmlfilename,html文件名称
@suite，测试用例集合
'''
def excuteSuiteExportReport(reportFileName, suite):
    fr = open(reportFileName,'wb')
    report = HTMLTestRunner.HTMLTestRunner(stream=fr,title='测试报告',description='测试报告详情')
    suit_result = report.run(suite)
    print type(suit_result)
    return suit_result


'''
获取分片上传文件信息
@filepath 分片文件存放地址
'''
def getfileinfo(filepath):
    from os.path import getsize,join
    #获取分片文件的信息,返回每个片的大小，及总文件大小
    file_dict = {}
    total_size = 0
    tmp_num = 0
    try:
        for root, dirs, files in os.walk(filepath):
            print files
            if files == None:
                print '没有文件'
            else:
                for i in files:
                    file_0 = getsize(join(root,i))
                    file_dict[i] = file_0
                    total_size +=file_0
                    tmp_num +=1
        return file_dict,total_size
    except OSError,e:
        print '文件地址找不到文件！'
        print e



'''
判别用例的执行结果，用于Jenkins上执行结果颜色显示
@test_result ：unnitest执行用例结果信息
'''
def analysisResult(test_result):
    failure_count = test_result.failure_count
    error_count = test_result.error_count
    print(u"用例执行失败个数为%s"%failure_count)
    print(u"用例执行错误个数为%s"%error_count)
    if failure_count == 0 and error_count == 0:
        print u"正常退出"
    else:
        print u"异常退出"
        raise Exception(u"用例执行失败")


'''
错误信息xml文件的内容信息解析,取出指定的tag值
@xmldata xml字符串信息
@return_status 返回的状态码
@expected_status 预期的状态码
@expected_Code 预期的返回码
@expected_Message 预期返回的message
'''
def compare_xml_tag(xmldata,return_status,expected_status,expected_Code,expected_Message):
    success= '########################################\n                 SUCCESS\n########################################'
    fail= '########################################\n                 FAIL\n########################################'
    if xmldata!='':
        if return_status == expected_status:
            print u'>>>>正确返回的status:{0}'.format(return_status)
            rootxml = ElementTree.fromstring(xmldata)
            for code_data in  rootxml.findall("Code"):
                code_data_text = code_data.text
                if code_data!=''and code_data_text==expected_Code:
                    print u'>>>>正确返回的code:{0}'.format(code_data_text)
                    for message_data in rootxml.findall("Message"):
                        message_data_text = message_data.text
                        if message_data!=''and message_data_text==expected_Message:
                            print u'>>>>正确返回的message:{0}'.format(message_data_text)
                            print success
                            return 'SUCCESS'
                        else:
                            print u'>>>>返回的message与预期不符,正确的message:{0},错误的message:{1}'.format(expected_Message,message_data_text)
                            print fail
                            return 'FAIL'
                else:
                    print u'>>>>返回错误码与预期不符，正确的code:{0},错误的code:{1}'.format(expected_Code,code_data_text)
                    print fail
                    return 'FAIL'
        else:
            print u'>>>>返回的status状态码与预期不一致,正确的status;{0},错误的status:{1}'.format(expected_status,return_status)
            print fail
            return 'FAIL'
    else:
        print u'>>>>获取到的xml内容为空！'
        print fail
        return 'FAIL'


'''
初始化获取uploadid 接口200返回数据解析
@xmldata xml字符串信息
@return_status 返回的状态码
@expected_bucket 预期的空间
@expected_key 预期返回的文件名称
'''
def compare_xml_200(xmldata,return_status,expected_bucket,expected_key):
    success= '########################################\n                 SUCCESS\n########################################'
    fail= '########################################\n                 FAIL\n########################################'
    if xmldata!='':
        if return_status == '200':
            print  u'>>>>正确返回的status:{0}'.format(return_status)
            rootxml = ElementTree.fromstring(xmldata)
            for bucket_data in  rootxml.findall("{http://wcs.chinanetcenter.com/document}Bucket"):
                bucket_data_text = bucket_data.text
                if bucket_data!=''and bucket_data_text==expected_bucket:
                    print u'>>>>正确返回的bucket:{0}'.format(bucket_data_text)
                    rootxml = ElementTree.fromstring(xmldata)
                    for key_data in rootxml.findall("{http://wcs.chinanetcenter.com/document}Key"):
                        key_data_text = key_data.text
                        if key_data!=''and key_data_text==expected_key:
                            print u'>>>>正确返回的key:{0}'.format(key_data_text)
                            rootxml = ElementTree.fromstring(xmldata)
                            for uploadid_data in rootxml.findall("{http://wcs.chinanetcenter.com/document}UploadId"):
                                uploadid_data_text = uploadid_data.text
                                if uploadid_data_text!='':
                                    print u'>>>>正确返回的uploadid:{0}'.format(uploadid_data_text)
                                    print success
                                    return 'SUCCESS'
                                else:
                                    print fail
                                    return 'FAIL'
                        else:
                            print u'>>>>返回的key与预期不符,正确的key:{0},错误的key:{1}'.format(expected_key,key_data_text)
                            print fail
                            return 'FAIL'
                else:
                    print u'>>>>返回错空间与预期不符，正确的bucket:{0},错误的bucket:{1}'.format(expected_bucket,bucket_data_text)
                    print fail
                    return 'FAIL'
        else:
            print u'>>>>返回的status状态码与预期不一致,正确的status;200,错误的status:{0}'.format(return_status)
            print fail
            return 'FAIL'
    else:
        print u'>>>>获取到的xml内容为空！'
        print fail
        return 'FAIL'


'''
错误信息xml文件的内容信息解析,取出指定的tag值.该方法用于处理空格这种特殊字符接口返回和实际文件无法匹配问题
@xmldata xml字符串信息
@return_status 返回的状态码
@expected_bucket 预期的空间
@expected_key 预期返回的文件名称
'''
def compare_xml_200_specialstring(xmldata,return_status,expected_bucket,expected_key):
    success= '########################################\n                 SUCCESS\n########################################'
    fail= '########################################\n                 FAIL\n########################################'
    if xmldata!='':
        if return_status == '200':
            print  u'>>>>正确返回的status:{0}'.format(return_status)
            rootxml = ElementTree.fromstring(xmldata)
            for bucket_data in  rootxml.findall("{http://wcs.chinanetcenter.com/document}Bucket"):
                bucket_data_text = bucket_data.text
                if bucket_data!=''and urllib.quote(bucket_data_text)==expected_bucket:
                    print u'>>>>正确返回的bucket:{0}'.format(bucket_data_text)
                    rootxml = ElementTree.fromstring(xmldata)
                    for key_data in rootxml.findall("{http://wcs.chinanetcenter.com/document}Key"):
                        key_data_text = key_data.text
                        if key_data!=''and urllib.quote(key_data_text)==expected_key:
                            print u'>>>>正确返回的key:{0}'.format(key_data_text)
                            rootxml = ElementTree.fromstring(xmldata)
                            for uploadid_data in rootxml.findall("{http://wcs.chinanetcenter.com/document}UploadId"):
                                uploadid_data_text = uploadid_data.text
                                if uploadid_data_text!='':
                                    print u'>>>>正确返回的uploadid:{0}'.format(uploadid_data_text)
                                    print success
                                    return 'SUCCESS'
                                else:
                                    print fail
                                    return 'FAIL'
                        else:
                            print u'>>>>返回的message与预期不符,正确的message:{0},错误的message:{1}'.format(expected_key,key_data_text)
                            print fail
                            return 'FAIL'
                else:
                    print u'>>>>返回错误码与预期不符，正确的code:{0},错误的code:{1}'.format(expected_bucket,bucket_data_text)
                    print fail
                    return 'FAIL'
        else:
            print u'>>>>返回的status状态码与预期不一致,正确的status;200,错误的status:{0}'.format(return_status)
            print fail
            return 'FAIL'
    else:
        print u'>>>>获取到的xml内容为空！'
        print fail
        return 'FAIL'


'''
upload 分片上传200返回解析
@header_data 返回的头部信息
@return_status 返回的状态码
'''
def upload_200_header(header_data,return_status):
    success= '########################################\n                 SUCCESS\n########################################'
    fail= '########################################\n                 FAIL\n########################################'
    if header_data!='':
        print u'>>>>返回的头部信息:{0}'.format(header_data)
        if return_status == '200':
            print  u'>>>>正确返回的status:{0}'.format(return_status)
            etag = header_data['ETag']
            if etag =='':
                print u'>>>>返回的头部信息中，etag值为空！'
                print fail
                return 'FAIL'
            else:
                print u'>>>>返回的头部etag值为:{0}'.format(etag)
                print success
                return 'SUCCESS'
        else:
            print u'>>>>返回的status状态码与预期不一致,正确的status;200,错误的status:{0}'.format(return_status)
            print fail
            return 'FAIL'
    else:
        print u'>>>>获取到的xml内容为空！'
        print fail
        return 'FAIL'


'''
complete合成接口200返回数据解析
@xmldata xml字符串信息
@return_status 返回的状态码
@expected_bucket 预期的空间
@expected_key 预期返回的文件名称
'''
def complete_xml_200(xmldata,return_status,expected_bucket,expected_key):
    success= '########################################\n                 SUCCESS\n########################################'
    fail= '########################################\n                 FAIL\n########################################'
    if xmldata!='':
        if return_status == '200':
            print  u'>>>>正确返回的status:{0}'.format(return_status)
            rootxml = ElementTree.fromstring(xmldata)
            for bucket_data in  rootxml.findall("{http://wcs.chinanetcenter.com/document}Bucket"):
                bucket_data_text = bucket_data.text
                if bucket_data!=''and bucket_data_text==expected_bucket:
                    print u'>>>>正确返回的bucket:{0}'.format(bucket_data_text)
                    rootxml = ElementTree.fromstring(xmldata)
                    for key_data in rootxml.findall("{http://wcs.chinanetcenter.com/document}Key"):
                        key_data_text = key_data.text
                        if key_data!=''and key_data_text==expected_key:
                            print u'>>>>正确返回的key:{0}'.format(key_data_text)
                            rootxml = ElementTree.fromstring(xmldata)
                            for ETag_data in rootxml.findall("{http://wcs.chinanetcenter.com/document}ETag"):
                                ETag_data_text = ETag_data.text
                                if ETag_data_text!='':
                                    print u'>>>>正确返回的ETag:{0}'.format(ETag_data_text)
                                    print success
                                    return 'SUCCESS'
                                else:
                                    print fail
                                    return 'FAIL'
                        else:
                            print u'>>>>返回的key与预期不符,正确的key:{0},错误的key:{1}'.format(expected_key,key_data_text)
                            print fail
                            return 'FAIL'
                else:
                    print u'>>>>返回错空间与预期不符，正确的bucket:{0},错误的bucket:{1}'.format(expected_bucket,bucket_data_text)
                    print fail
                    return 'FAIL'
        else:
            print u'>>>>返回的status状态码与预期不一致,正确的status;200,错误的status:{0}'.format(return_status)
            print fail
            return 'FAIL'
    else:
        print u'>>>>获取到的xml内容为空！'
        print fail
        return 'FAIL'



'''
比对俩个文件的hash值是否一致
@path1 文件1
@path2 文件2
'''
def compare_file_md5(filepath1,filepath2):
    with open(filepath1,'rb') as f1:
          sha1_obj1 = sha1()
          sha1_obj1.update(f1.read())
          hash1 = sha1_obj1.hexdigest()

    with open(filepath2,'rb') as f2:
          sha1_obj2 = sha1()
          sha1_obj2.update(f2.read())
          hash2 = sha1_obj2.hexdigest()
    if hash1 == hash2:
        return 'SUCCESS'
    else:
        return 'FAIL'


'''
将返回的数据写入到xml文档，为后面对返回数据做比较
@filename 待写入的文件地址
@data 待写入的数据
'''
def writexml(filename,data):
    try:
        f=open(filename,'wb')
        f.write(data)
        f.close()
        return 0
    except IOError:
        print '无法生成文件！'
        return -1



'''
用于解析接口返回的xml内容，并对内容进行重新组合成lsit列表，方便比较
@filename 传入的文件地址信息
'''
#全局唯一标识
unique_id = 1
################处理解析后的数据
def analysis_xml(file_name):
    def walkData(root_node, level, result_list,*args):
        temp_list =[level, root_node.tag.replace('{http://wcs.chinanetcenter.com/document}',''),root_node.text]
        result_list.append(temp_list)
        #遍历每个子节点
        children_node = root_node.getchildren()
        #如果子节点为空，返回
        if len(children_node) == 0:
          return
        for child in children_node:
            walkData(child, level + 1, result_list)
    level = 1 #节点的深度从1开始
    result_list = [] #用于存储带有节点等级的解析数据
    #######################获取跟节点####################
    root = ET.parse(file_name).getroot()
    walkData(root, level, result_list)
    ###########删除时间标签内容##############
    for partinfo in result_list:
        if partinfo[1]=='LastModified':
            result_list.remove(partinfo)
        if partinfo[1] =='Initiated':
            result_list.remove(partinfo)

    return result_list


'''
@用于比较俩个列表的是否一致,并打印出不一致的地方；
'''
def comp_list(return_list,ture_list):
    if len(return_list) == len(ture_list):
        for i in range(0, len(return_list)):
            #两个列表对应元素相同，则直接过
            if return_list[i] == ture_list[i]:
                pass
            else:#两个列表对应元素不同，则输出对应的索引
                print '第%d 个元素不一致,正确的元素 %s,返回错误的元素 %s'%(i+1,ture_list[i],return_list[i])
                return 'FAIL'
    else:
        print '返回结果内容长度与预期的不一致.\n接口返回列表：%s,\n预期返回结果：%s'%(return_list,ture_list)
        return 'FAIL'


'''
各类错误的code和message属性 类
'''
class  code_message_info():
    status_200 = '200' #正常返回的状态码
    status_501 = '501'#header头部带不支持参数返回的状态码
    code_501 = 'Not Implemented' #header头部带不支持参数返回码
    message_501 = 'A header you provided implies functionality that is not implemented.'#501 返回的message内容

    status_403= '403'
    code_403_SignatureDoesNotMatch = 'SignatureDoesNotMatch' #token鉴权失败
    message_403_SignatureDoesNotMatch = 'The request signature we calculated does not match the signature you provided. Check your WCS secret access key and signing method.'#token鉴权失败message
    code_403_AccessDenied ='AccessDenied'
    message_403_AccessDenied = 'WCS authentication requires a valid Date or x-amz-date header.'
    message_403_AccessDenied_2 ='Access Denied'
    message_403_AccessDenied_3 ='Access Denied '
    code_403_InvalidAccessKeyId ='InvalidAccessKeyId'
    message_403_InvalidAccessKeyId = 'The WCS Access Key Id you provided does not exist in our records.'

    status_400 ='400'
    code_400_InvalidDigest = 'InvalidDigest'
    message_400_InvalidDigest ='The Content-MD5 you specified is not valid.'
    code_400_UnexpectedContent = 'UnexpectedContent'
    message_400_UnexpectedContent ='This request does not support content.'
    code_400_KeyTooLong = 'KeyTooLong'
    message_400_KeyTooLong ='Your key is too long.'
    code_400_ExpiredToken = 'ExpiredToken'
    message_400_ExpiredToken ='The provided token has expired.'
    code_400_InvalidArgument = 'InvalidArgument'
    message_400_InvalidArgument ='WCS authorization header is invalid.  Expected WcsAccessKeyId:signature.'
    message_400_InvalidArgument_2= 'Authorization header is invalid -- one and only one \' \' (space) required.'
    message_400_InvalidArgument_3 =  'Unsupported Authorization Type.'
    message_400_InvalidArgument_4 =  'Invalid Argument.'
    message_400_InvalidArgument_5 ='Part number must be an integer between 1 and 10000, inclusive.'
    message_400_InvalidArgument_partNumberMaker='Argument partNumberMaker must be an integer between 0 and 1000.'
    message_400_InvalidArgument_maxParts='Argument maxParts must be an integer between 0 and 1000.'
    message_400_InvalidArgument_maxParts_2='Provided maxParts not an integer or within integer range.'
    message_400_InvalidArgument_partNumberMarker_2='Provided partNumberMarker not an integer or within integer range.'
    message_400_InvalidArgument_maxuploads='Argument maxUploads must be an integer between 0 and 1000.'
    message_400_InvalidArgument_maxuploads_string='Provided max-uploads not an integer or within integer range.'


    code_400_InvalidURI=  'InvalidURI'
    message_400_InvalidURI = 'Couldn\'t parse the specified URI.'
    code_400_InvalidObjectName=  'InvalidObjectName'
    message_400_InvalidObjectName = 'The specified object name is not valid.'
    code_400_BadRequest ='Bad Request'
    message_400_BadRequest ='You must specify at least one part.'
    message_400_BadRequest_2 = 'EntityTooSmall.'
    code_400_InvalidPart = 'InvalidPart'
    message_400_InvalidPart = 'One or more of the specified parts could not be found. The part might not have been uploaded, or the specified entity tag might not have matched the part\'s entity tag.'
    code_400_InvalidPartOrder='InvalidPartOrder'
    message_400_InvalidPartOrder ='The list of parts was not in ascending order.Parts list must specified in order by part number.'
    code_400_MalformedXML = 'MalformedXML'
    message_400_MalformedXML = 'The XML you provided was not well-formed or did not validate against our published schema.'

    status_404 = '404'
    code_404_NoSuchBucket ='NoSuchBucket'
    message_404_NoSuchBucket = 'The specified bucket does not exist.'
    code_404_NoSuchUpload =  'NoSuchUpload'
    message_404_NoSuchUpload  = 'The specified multipart upload doesnot exist. The upload ID might beinvalid, or the multipart upload mighthave been aborted or completed.'
    message_404_list_NoSuchUpload ='The specified upload does not exist. The upload ID may be invalid, or the upload may have been aborted or completed.'
    status_409 = '409'
    code_409_nvalidBucketState ='InvalidBucketState'
    message_409_nvalidBucketState = 'The request is not valid with the current state of the bucket.'

    status_405 = '405'
    code_405_NoSuchBucket ='Method Not Allowed'
    message_405_NoSuchBucket = 'The specified bucket does not exist.'



if __name__=='__main__':
    # string = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><InitiateMultipartUploadResult xmlns="http://wcs.chinanetcenter.com/document"><Bucket>caiyz-autotest1</Bucket><Key>momo.mp4</Key><UploadId>3d7f569a43c84440bcde7bf9292aea12</UploadId></InitiateMultipartUploadResult>'
    # filepath = 'F:\test_report'
    # print compare_xml_200(string,'200','caiyz-autotest1','momo.mp4')
    datafile = 'E:\diff_file\get_ListMultipartUpload_allresource.txt'
    diff_file = 'E:\diff_file\diff_ListMultipartUpload_allresource.txt'
    print comp_list([1,'qq',[3,5,'ww'],6],[1,'ee',[1,5,4],6,5])