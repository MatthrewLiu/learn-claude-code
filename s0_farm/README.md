## 试一下

**准备**（首次运行）：

```sh
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY 和 MODEL_ID
```

**运行**：

```sh
普通控制台模式
python s0_farm/code.py

启动后端服务模式
python .\s0_farm\code.py --serve --host 127.0.0.1 --port 8008
```

试试这些 prompt：

1. `给地块浇水`
2. `明天让张三去给东边的地块浇水`
3. `你会干啥`
