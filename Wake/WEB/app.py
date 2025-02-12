from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import logging
import functools

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def stream_with_context(generator):
    try:
        yield from generator()
    except GeneratorExit:
        app.logger.info("Client closed connection")
    except Exception as e:
        app.logger.error(f"Stream error: {str(e)}")
    finally:
        app.logger.info("Stream ended")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    app.logger.info(f"Received message: {user_message}")
    
    def generate():
        try:
            # 准备发送给Ollama的请求
            ollama_data = {
                "model": "deepseek-r1:1.5b",
                "prompt": user_message,
                "stream": True
            }
            
            app.logger.info("Sending request to Ollama")
            response = requests.post(OLLAMA_API_URL, json=ollama_data, stream=True)
            app.logger.info(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        chunk = json_response.get('response', '')
                        if chunk:
                            yield f"data: {json.dumps({'response': chunk})}\n\n"
                # 确保流正确结束
                yield "data: {\"done\": true}\n\n"
            else:
                app.logger.error(f"Ollama error: {response.text}")
                yield f"data: {json.dumps({'error': 'Failed to get response from Ollama'})}\n\n"
        except Exception as e:
            app.logger.error(f"Exception occurred: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            app.logger.info("Response stream completed")
    
    return Response(stream_with_context(generate), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000) 