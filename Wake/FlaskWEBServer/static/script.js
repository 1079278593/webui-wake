document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    let currentController = null;  // 用于存储当前的 AbortController

    // 设置输入状态
    function setInputState(enabled) {
        userInput.disabled = !enabled;
        sendButton.disabled = !enabled;
        if (!enabled) {
            sendButton.style.backgroundColor = '#cccccc';
            sendButton.style.cursor = 'not-allowed';
        } else {
            sendButton.style.backgroundColor = '#007AFF';
            sendButton.style.cursor = 'pointer';
        }
    }

    // 清理当前请求
    function cleanup() {
        if (currentController) {
            currentController.abort();
            currentController = null;
        }
        setInputState(true);
    }

    // 页面卸载时清理
    window.addEventListener('beforeunload', cleanup);

    // 处理发送消息
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // 如果有正在进行的请求，先中断它
        cleanup();

        // 禁用输入
        setInputState(false);

        // 添加用户消息到聊天界面
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message';
        const userContent = document.createElement('div');
        userContent.className = 'message-content';
        userContent.textContent = message;
        userMessageDiv.appendChild(userContent);
        chatMessages.appendChild(userMessageDiv);
        
        // 清空输入框
        userInput.value = '';

        // 创建AI消息容器
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'message ai-message';
        
        // 创建思考过程容器（初始不添加到DOM）
        const thinkingContent = document.createElement('div');
        thinkingContent.className = 'message-content thinking';
        thinkingContent.style.display = 'none';
        
        // 创建答案容器
        const answerContent = document.createElement('div');
        answerContent.className = 'message-content answer';
        aiMessageDiv.appendChild(answerContent);
        
        chatMessages.appendChild(aiMessageDiv);

        try {
            // 创建新的 AbortController
            currentController = new AbortController();

            // 发送POST请求并接收流式响应
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message }),
                signal: currentController.signal
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let isThinking = false;
            let hasThinkingContent = false;

            while (true) {
                const {done, value} = await reader.read();
                
                if (done) {
                    // 如果结束时没有思考内容，确保思考容器不显示
                    if (!hasThinkingContent) {
                        thinkingContent.remove();
                    }
                    cleanup();
                    break;
                }

                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.error) {
                                answerContent.textContent = '抱歉，出现了一个错误：' + data.error;
                                thinkingContent.remove();
                                cleanup();
                                return;
                            } else if (data.done) {
                                cleanup();
                                return;
                            } else if (data.response) {
                                const text = data.response;
                                
                                // 检测是否在思考过程中
                                if (text.includes('<think>')) {
                                    isThinking = true;
                                    // 只在第一次遇到思考内容时添加容器
                                    if (!hasThinkingContent) {
                                        aiMessageDiv.insertBefore(thinkingContent, answerContent);
                                        thinkingContent.style.display = 'block';
                                    }
                                } else if (text.includes('</think>')) {
                                    isThinking = false;
                                    // 清空思考内容，准备显示答案
                                    const cleanedThinkingText = thinkingContent.textContent.replace(/<\/?think>/g, '').trim();
                                    if (cleanedThinkingText) {
                                        hasThinkingContent = true;
                                        thinkingContent.textContent = cleanedThinkingText;
                                    } else {
                                        thinkingContent.remove();
                                    }
                                } else {
                                    if (isThinking) {
                                        thinkingContent.textContent += text;
                                    } else {
                                        answerContent.textContent += text;
                                    }
                                }
                                
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        } catch (e) {
                            console.error('解析响应时出错:', e);
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('请求被中断');
            } else {
                console.error('请求出错:', error);
                answerContent.textContent = '抱歉，发生了一个错误，请稍后重试。';
                thinkingContent.remove();
            }
            cleanup();
        }

        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 事件监听器
    sendButton.addEventListener('click', sendMessage);
    
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !userInput.disabled) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 自动调整文本框高度
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
    });
}); 