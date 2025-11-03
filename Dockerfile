
FROM  ghcr.io/rachelos/py3.13.1:latest
# 安装系统依赖
WORKDIR /app

# ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=https://mirrors.huaweicloud.com/repository/pypi/simple

# 复制Python依赖文件
# 复制后端代码
COPY requirements.txt .
RUN pip3 install -r requirements.txt 

COPY . .

RUN rm -rf ./web_ui
RUN rm -rf db.db
COPY ./config.example.yaml  ./config.yaml
RUN chmod +x ./start.sh
# 暴露端口
EXPOSE 8001
# 启动命令
# CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "8001"]
# CMD ["python", "main.py"]
CMD ["./start.sh"]