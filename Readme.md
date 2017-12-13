# Sanpangzi Net Tool
### 介绍
一款简单的网络工具，仿照nc编写，参考《python黑帽子编程》中部分代码
### 功能
- 建立交互shell
- 上传文件
- 远程执行命令

### 使用方法
#### 服务端使用
```
sangpangzi.py -t 192.168.0.1 -p 5555 -l
```
#### 客户端使用
- **建立交互shell**
```
sanpangzi.py -t 192.168.0.1 -p 5555 -c
```

- **上传文件**
```
anpangzi.py -t 192.168.0.1 -p 5555 -u C:\\test.exe -d /www/
```
- **远程执行命令**
```
sanpangzi.py -t 192.168.0.1 -p 5555 -e "cat /etc/passwd"
```
