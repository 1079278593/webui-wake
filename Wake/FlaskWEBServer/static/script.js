document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const voiceButton = document.getElementById('voice-button');
    let currentController = null;
    let isRecording = false;
    let currentDialogueId = null;
    let currentEventSource = null;

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

    // 设置语音按钮状态
    function setVoiceButtonState(recording) {
        isRecording = recording;
        if (recording) {
            voiceButton.classList.add('recording');
            voiceButton.textContent = '正在录音...';
        } else {
            voiceButton.classList.remove('recording');
            voiceButton.textContent = '对话';
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

    // 开始语音识别
    async function startVoiceRecognition() {
        if (isRecording) {
            await stopVoiceRecognition();
            return;
        }

        try {
            setVoiceButtonState(true);
            const response = await fetch('/start_voice', {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.error) {
                console.error('语音识别错误:', data.error);
                setVoiceButtonState(false);
                return;
            }

            currentDialogueId = data.dialogue_id;
            console.log('开始语音识别，对话ID:', currentDialogueId);
            
            // 关闭已存在的事件源
            if (currentEventSource) {
                currentEventSource.close();
            }
            
            // 创建新的事件源
            currentEventSource = new EventSource('/voice_events');
            
            currentEventSource.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                console.log('收到语音事件:', data);
                
                if (data.type === 'keepalive') {
                    // 忽略保持活动信号
                    return;
                }
                
                if (data.status === 'success' && data.text) {
                    console.log('收到语音识别文本:', data.text);
                    await sendMessage(data.text);
                } else if (data.status === 'error') {
                    console.error('语音识别错误:', data.error);
                    setVoiceButtonState(false);
                    currentEventSource.close();
                    currentEventSource = null;
                }
            };
            
            currentEventSource.onerror = (error) => {
                console.error('语音事件流错误:', error);
                setVoiceButtonState(false);
                if (currentEventSource) {
                    currentEventSource.close();
                    currentEventSource = null;
                }
            };
        } catch (error) {
            console.error('启动语音识别失败:', error);
            setVoiceButtonState(false);
        }
    }

    // 停止语音识别
    async function stopVoiceRecognition() {
        try {
            if (currentEventSource) {
                currentEventSource.close();
                currentEventSource = null;
            }
            
            await fetch('/stop_voice', {
                method: 'POST'
            });
            setVoiceButtonState(false);
        } catch (error) {
            console.error('停止语音识别失败:', error);
        }
    }

    // 处理发送消息
    async function sendMessage(message = null) {
        const messageText = message || userInput.value.trim();
        if (!messageText) return;

        // 如果有正在进行的请求，先中断它
        cleanup();

        // 禁用输入
        setInputState(false);

        // 添加用户消息到聊天界面
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message';
        const userContent = document.createElement('div');
        userContent.className = 'message-content';
        userContent.textContent = messageText;
        userMessageDiv.appendChild(userContent);
        chatMessages.appendChild(userMessageDiv);
        
        // 只有当消息来自输入框时才清空
        if (!message) {
            userInput.value = '';
        }

        // 创建AI消息容器
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'message ai-message';
        
        // 创建思考过程容器
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
                body: JSON.stringify({ 
                    message: messageText,
                    dialogue_id: currentDialogueId
                }),
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
                            } else if (data.status === 'interrupted') {
                                // 被中断时，保留已显示的内容，只添加中断标记
                                if (answerContent.textContent) {
                                    answerContent.textContent += ' [已中断]';
                                }
                                thinkingContent.remove();
                                cleanup();
                                return;
                            } else if (data.done) {
                                cleanup();
                                return;
                            } else if (data.response) {
                                const text = data.response;
                                
                                if (text.includes('<think>')) {
                                    isThinking = true;
                                    if (!hasThinkingContent) {
                                        aiMessageDiv.insertBefore(thinkingContent, answerContent);
                                        thinkingContent.style.display = 'block';
                                    }
                                } else if (text.includes('</think>')) {
                                    isThinking = false;
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
                            console.error('解析响应时出错:', e, '原始数据:', line);
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('请求被中断');
                if (answerContent.textContent) {
                    answerContent.textContent += ' [已中断]';
                }
            } else {
                console.error('发送消息失败:', error);
                answerContent.textContent = '发送消息失败，请重试。';
            }
        } finally {
            cleanup();
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // 事件监听器
    sendButton.addEventListener('click', () => sendMessage());
    voiceButton.addEventListener('click', startVoiceRecognition);
    
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 自动调整文本框高度
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
    });

    // 页面卸载时清理
    window.addEventListener('beforeunload', () => {
        cleanup();
        stopVoiceRecognition();
    });
}); 