# 计算器后端项目
## 项目介绍
前后端分离计算器后端，使用FastAPI+SQLite，使用逆波兰表达式解析计算，禁止eval，提供四则运算、历史记录持久化、删除记录接口。
## 技术栈
Python, FastAPI, SQLAlchemy, SQLite
## 环境启动
1. 创建虚拟环境 python -m venv venv
2. 激活虚拟环境 venv\Scripts\activate
3. pip install fastapi uvicorn pydantic sqlalchemy
4. 运行：python main.py
后端地址：http://127.0.0.1:8000
接口文档：http://127.0.0.1:8000/docs
## API
POST /api/calculate 提交表达式计算
GET /api/history 获取历史记录
DELETE /api/history/{id} 删除指定历史
## 数据库
SQLite数据库自动生成 calculator.db，无需手动建表
