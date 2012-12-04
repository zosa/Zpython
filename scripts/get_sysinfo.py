#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Created on 2012-7-10

@author: devops@qq.com
@version: v3
'''



import subprocess
import os
import socket
import fcntl
import struct
import time

os.putenv("LANG","en_US.UTF-8")

#下列变量请根据实际情况修改

nic = "eth0"    #服务器主网卡
backdir = "/data/backup/rman/"    #备份数据的根目录
width = 110    #分割线的总长度

niclist = os.listdir('/sys/class/net/')    #服务器所有网卡列表

def get_size(filename):
    '''计算filename的大小,保留一位小数,小数位超过两位,就自动进位。
	'''
    import math
    a = (os.path.getsize(filename) / 1024 / 1024.0)
    size = "%.1f" % (math.ceil(a * 10) / 10)
	#from decimal import *
	#Decimal(str(a)).quantize(Decimal('.1'), rounding=ROUND_UP)
    return size

def get_dir_info(path):
    for root,dirlist,filelist in os.walk(path):
        for filename in filelist:
            print(os.path.join(root,filename), get_size(os.path.join(root,filename)))

def get_ip_address(ifname):
    '''获取本机网卡ip
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
	
def get_nic_flow(nic):
    '''获取当前网卡流量
    '''
    fd = open("/proc/net/dev", "r")
    for line in fd.readlines():
        if line.find(nic) > 0:
            field = line.split()
            recv = field[1]
            send = field[9]
    fd.close()
    return (float(recv), float(send))  
    #print("%s: recv: %.3f MB, send %.3f MB" % (nic, float(recv)/1024/1024, float(send)/1024/1024))

def put_nic_flow(nic,sec):
    '''通过get_nic_flow获取网卡指定时间(sec)内的流量并输出
    '''
    (recv, send) = get_nic_flow(nic) 
    time.sleep(int(sec))
    (new_recv, new_send) = get_nic_flow(nic)
    print("%s: recv: %.3f MB, send %.3f MB" % (nic, (new_recv -recv)/1024/1024, (new_send - send)/1024/1024))
    (recv, send) = (new_recv, new_send)
	

def get_info(cmd,text,width=110):
    '''通过subprocess.call直接执行系统命令
    '''
    print(text).center(width,'=')
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    pipe = p.stdout.readlines()
    for i in pipe:
        print(i)
	
def popen_info(cmd):
    '''通过subprocess.Popen执行系统命令,并获取输出
    '''
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
	#p.wait()        #等待进程结束
    pipe = p.stdout.readlines()
    return pipe
	
print("服务器 " + get_ip_address(nic)).center(width,'=')

#一、硬件统计
##1、品牌、型号、序列号
get_info('dmidecode  | grep  -A26 "System Information$"','服务器品牌、型号、序列号(dmidecode  | grep  -A26 "System Information$")')
##2、CPU信息
###2.1、物理CPU个数
get_info('cat /proc/cpuinfo | grep "physical id" | sort | uniq | wc -l','服务器物理CPU个数(cat /proc/cpuinfo | grep "physical id" | sort | uniq | wc -l)')

###2.2、每个物理CPU中core的个数(即核数)
get_info('cat /proc/cpuinfo | grep "cpu cores" | uniq','每个物理CPU中core的个数(cat /proc/cpuinfo | grep "cpu cores" | uniq)')

###2.3、逻辑CPU的个数
get_info('cat /proc/cpuinfo | grep "processor" | wc -l','逻辑CPU的个数(cat /proc/cpuinfo | grep "processor" | wc -l)')
##3、内存
###3.1、LINUX下查看内存频率

get_info('dmidecode | grep -A16 "Memory Device"  | grep -v "Unknown" | grep Speed','查看内存频率(dmidecode | grep -A16 "Memory Device"  | grep -v "Unknown" | grep Speed)')
###3.2、LINUX下查看内存物理个数及容量
get_info('dmidecode | grep -A16 "Memory Device"  | grep -v "No Module Installed" | grep -v "Range Size" | grep Size','查看内存物理个数及容量')


###3.3、查看内存的插槽数，已经使用多少插槽。每条内存多大，已使用内存多大
#get_info('dmidecode | grep -P -A5 "Memory\s+Device"|grep Size|grep -v Range','查看内存的插槽数，已经使用多少插槽。每条内存多大，已使用内存多大')

###3.4、查看内存支持的最大内存容量
#get_info('dmidecode | grep -P "Maximum\s+Capacity"','查看内存支持的最大内存容量')

##4、硬盘

#二、运维信息检查
##(一)系统检查

###1、操作系统版本及内核信息( uname -onrm)
get_info("uname -onrm","操作系统版本及内核信息( uname -onrm)")

###2、检查系统负载情况(uptime)
get_info("uptime","系统负载情况(uptime)")


###3、检查系统CPU使用情况(top) 系统进程信息
topinfo = popen_info("top -bn1")
print("系统CPU使用情况(top -bn1)").center(width,'=')
print(topinfo[2])
print("系统进程信息(top -bn1)").center(width,'=')
print(topinfo[1])

	
###4、检查系统内存使用情况(free –m)
get_info('free -m', "系统内存使用情况(free –m)")

###5、采用vmstat检查系统资源整体使用情况(vmstat 1 10)
get_info("vmstat 1 10", "系统资源整体使用情况(vmstat 1 10)")

###6、检查系统前一天的用户登陆情况(last | grep `date -d yesterday +"%b"` | grep `date -d yesterday +"%a"` )
get_info('last| grep "$(date -d yesterday +"%a %b")"', '系统前一天的用户登陆情况(last| grep "$(date -d yesterday +"%a %b")")')


###7、检查系统一个月的用户登陆情况(last | grep `date +%b`)
get_info('last | grep "$(date +%b)"', '系统系统一个月的用户登陆(last | grep `date +%b`)')


##(二)磁盘检查

###1、检查系统磁盘空间使用情况(df -h)。
get_info('df -h','系统磁盘空间使用情况(df -h)')
    
#2、磁盘IO繁忙度检查(iostat 5 3)
get_info('iostat 5 3', '磁盘IO情况(iostat 5 3)')
	
##(三)网络检查

###1、网卡状态检查(ifconfig -a)

get_info('ifconfig -a',"网卡状态检查(ifconfig -a)")

###2、系统路由表（route -n）
get_info('route -n',"系统路由表（route -n）")

###3、主机端口开放情况(netstat -ntlup)
get_info('netstat -ntlup',"主机端口开放情况(netstat -ntlup)")

###4、检查网络状况(netstat -i)
get_info('netstat -i',"检查网络状况(netstat -i)")


###5、检查Tcp连接状态(netstat -n | awk '/^tcp/ {++S[$NF]} END {for(a in S) print a,S[a]}')
get_info("netstat -n | awk '/^tcp/ {++S[$NF]} END {for(a in S) print a,S[a]}'","检查Tcp连接状态(netstat -n | awk '/^tcp/ {++S[$NF]} END {for(a in S) print a,S[a]}')")

###6、检查当前网卡流量
print("检查当前网卡流量").center(width,'=')
put_nic_flow(nic,1)

#(四)数据备份检查
#1、递归显示备份目录下的所有目录及子目录下的文件内容(ls -lsShR 目标目录)
get_info("ls -lsShR %s" % backdir,"检查数据备份情况(ls -lsShR %s)" % backdir)

