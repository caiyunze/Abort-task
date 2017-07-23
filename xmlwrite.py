#!/usr/bin/env python
#coding=utf-8

import xml.dom.minidom
import os
curDir = os.path.abspath('.') + os.path.sep
filePath = curDir + 'MultipartUpload_bigregion_html' + os.path.sep
def writexml(managerList,filename):
  #在内存中创建一个空的文档
  doc = xml.dom.minidom.Document()
  #创建一个根节点Managers对象
  root = doc.createElement('CompleteMultipartUpload')
  #设置根节点的属性
  # root.setAttribute('company', 'xx科技')
  # root.setAttribute('address', '科技软件园')
  #将根节点添加到文档对象中
  doc.appendChild(root)
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
  with open(filePath+filename, 'wb') as fp:
    doc.writexml(fp, indent='', addindent='', newl='', encoding="utf-8")

if __name__ =='__main__':
  managerList = [{'PartNumber' : '1',  'ETag' : 'IajWyFBDFCLuFh6LLqvBSKtIhcc='},
                 {'PartNumber' : '2', 'ETag' : 'p1pTV6xUCSNTSCoNocwNTu7Eeyw='}]
  ['{\'PartNumber\': \'0\', \'ETag\': \'"IajWyFBDFCLuFh6LLqvBSKtIhccbkYfGjUoCdhNkf7oTX2CSuWOMjw=="\'}',
   '{\'PartNumber\': \'1\', \'ETag\': \'"ISqQ_71FP7Kn4R7Tp7hT7aumc-GhAZFuA8RqEFQaKwCTvU94AgDdaQ=="\'}']

  #开始写xml文档
  writexml(managerList,'aa.xml')
