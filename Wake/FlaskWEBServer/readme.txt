
运行环境：
source fresh_env/bin/activate

运行python，用fresh_nev中的python，如下：
./fresh_env/bin/python WEB/app.py

app.py中用到了’轻量级的 Python Web 应用框架‘： Flask

为什么我们用了 Flask？
1. 跨域问题：
直接从浏览器访问 Ollama API 会遇到跨域限制
Flask 作为中间层可以解决这个问题
2. 流式输出：
Flask 可以很好地处理 Server-Sent Events
实现打字机效果更容易
3. 扩展性：
可以添加更多功能（历史记录、用户管理等）
可以集成其他服务

其它替代方案：
1. 使用 Node.js + Express：
2. 使用 Deno：
3. 使用 Nginx 反向代理：
server {
    location /api/ {
        proxy_pass http://localhost:11434/;
    }
}

最简单的方案：（但是如果要增加语音识别，就不行了，因为’拓展受限‘）
如果只是本地使用，可以使用浏览器扩展（如 CORS Unblock）解决跨域问题，然后直接用纯 HTML + JavaScript 实现，不需要任何后端。
您的使用场景更偏向于哪种？我可以给出更具体的实现建议。