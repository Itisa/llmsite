# -*- coding: utf-8 -*-

import json
import os
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Generator, List, Optional

import tornado.ioloop
import tornado.web
import requests

from openai import OpenAI
from volcenginesdkarkruntime import Ark
import logging
logging.basicConfig(
    filename="AIserver.log", 
    filemode="a",
    level=logging.INFO, # 保存所有级别日志
    format="%(asctime)s - %(levelname)s - %(message)s"
)

HOST = "127.0.0.1"
PORT = 8888
LOCAL_HOST = "127.0.0.1"
try:
    from llmsite.local_settings import AI_SERVER_PORT, AI_SERVER_HOST, LOCAL_HOST
    PORT = AI_SERVER_PORT
    HOST = AI_SERVER_HOST.replace("http://","").replace("https://","")
except Exception as e:
    print("Using default HOST and PORT:",HOST,PORT)

MAX_WORKERS = 2
MAX_QUEUE_SIZE = 100
REQUEST_TIMEOUT = 120
RETENTION_SECONDS = 300
TALK_TEST = True
LOCAL_SERVER_PORT = 8000
from AIserver_settings import *

API_CONFIG_PATH = "./mainsite/api_config.json"
if os.path.isfile(API_CONFIG_PATH):
# if False:
    with open(API_CONFIG_PATH,"r",encoding="utf-8") as f:
        api_config = json.load(f)
else:
    api_config = None
    print("\033[91m[Warning]\033[0m api_config.json 文件不存在，LLM API 未配置！")

@dataclass
class Task:
    cid: str
    params: List[Any]
    messages: List[Dict[str, str]]
    reasoning_content: str = ""   # 已接收的推理流式片段拼接
    content : str = ""            # 已接收的流式片段拼接
    model_name: str = ""
    model_type: str = ""  # RS / CH
    status: str = "queueing"  # queueing -> reasoning -> content -> done/failed
    error: Optional[str] = None

    def update(self, **kwargs):
        """
        更新 dataclass 中的字段。
        只会更新已定义的字段，避免传入无效的 key。
        """
        for f in fields(self):
            if f.name in kwargs:
                setattr(self, f.name, kwargs[f.name])

class TaskStore:
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    def add(self, task: Task):
        with self._lock:
            self._tasks[task.cid] = task

    def get(self, cid: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(cid)

    def update(self, cid: str, **kwargs):
        with self._lock:
            t = self._tasks.get(cid)
            if not t:
                return
            for k, v in kwargs.items():
                setattr(t, k, v)

    def delete(self, cid: str):
        with self._lock:
            self._tasks.pop(cid, None)

task_store = TaskStore()
task_queue: "queue.Queue[Task]" = queue.Queue(maxsize=MAX_QUEUE_SIZE)


class LLMClient:
    def _simulate_stream(self,task) -> Generator[str, None, None]:
        fake = f"[模拟回复] 你提交了数组内容摘要：{task.messages[-1]}. 下面是逐步生成的响应。呀，用户连续发了两个“你好”，可能是想测试我的反应或者网络有延迟重复发送了。考虑到对话历史很短，之前只是简单问候过，这次可以更活泼些打破重复问候的循环。用轻松的语气点破“重复打招呼”这个行为，加上表情符号让氛围更轻松。既然用户暂时没提出具体需求，可以主动提供几个常见话题方向，比如天气、音乐、书籍，用具体例子降低用户发起对话的门槛。最后用开放性问题引导用户说出真实需求，保持对话的开放性。"
        for ch in fake:
            time.sleep(0.02)
            yield ch

    def stream_chat(self, task):
        model = next((d for d in api_config if d.get("name") == task.model_name), None)
        # 如果找到就返回 dict，否则返回 None
        if model is None:
            logging.error(f"Model {task.model_name} not found in api_config.")
            return "Error: Model not configured"
        task.model_type = model.get("model_type")
        if TALK_TEST:
            t = 0
            reasoning_content = ""
            content = ""
            for chunk in self._simulate_stream(task):
                t += 1
                if task.model_type == "RS" and t < 100:
                    reasoning_content += chunk
                    try:
                        task.update(reasoning_content=reasoning_content,status="reasoning")
                    except Exception as e:
                        logging.error(f"Error updating task: {e}")
                else:
                    content += chunk
                    try:
                        task.update(content=content, status="content")
                    except Exception as e:
                        logging.error(f"Error updating task: {e}")
            return
        else:
            if model["model_origin"] == "DS":
                client = OpenAI(
                    api_key = model["api_key"],
                    base_url = model["base_url"],
                )
                
                response = client.chat.completions.create(
                    model = model["model"],
                    messages = task.messages,
                    stream = True,
                    temperature = task.params["temperature"],
                    top_p = task.params["top_p"],
                    max_tokens = task.params["max_tokens"],
                    frequency_penalty = task.params["frequency_penalty"],
                    presence_penalty = task.params["presence_penalty"],
                )
                
                for chunk in response:
                
                    if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
                        new_content = chunk.choices[0].delta.reasoning_content
                        task.reasoning_content += new_content
                        task.update(reasoning_content=task.reasoning_content,status="reasoning")
                    else:
                        new_content = chunk.choices[0].delta.content
                        task.content += new_content
                        task.update(content=task.content,status="reasoning")
            
            elif model["model_origin"] == "DB":
                client = Ark(
                    api_key = model["api_key"]
                )
                response = client.chat.completions.create(
                    model = model["model"],
                    messages = task.messages,
                    stream=True,
                    temperature = task.params["temperature"],
                    top_p = task.params["top_p"],
                    max_tokens = task.params["max_tokens"],
                    frequency_penalty = task.params["frequency_penalty"],
                    presence_penalty = task.params["presence_penalty"],
                )
                for chunk in response:
                    if not chunk.choices:
                        continue
                    new_content = chunk.choices[0].delta.content
                    task.content += new_content
                    task.update(content=task.content,status="content")
            elif model["model_origin"] == "OA":
                client = OpenAI(
                    api_key = model["api_key"],
                    base_url = model["base_url"],
                )
                
                response = client.chat.completions.create(
                    model = model["model"],
                    messages = task.messages,
                    stream = True,
                    temperature = task.params["temperature"],
                    top_p = task.params["top_p"],
                    max_tokens = task.params["max_tokens"],
                    frequency_penalty = task.params["frequency_penalty"],
                    presence_penalty = task.params["presence_penalty"],
                )
                for chunk in response:
                    if hasattr(chunk.choices[0],'finish_reason') and chunk.choices[0].finish_reason != None:
                        break
                    if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
                        new_content = chunk.choices[0].delta.reasoning_content
                        task.reasoning_content += new_content
                        task.update(reasoning_content=task.reasoning_content,status="reasoning")
                    else:
                        new_content = chunk.choices[0].delta.content
                        task.content += new_content
                        task.update(content=task.content,status="content")
llm_client = LLMClient()


class Worker(threading.Thread):
    daemon = True

    def run(self):
        while True:
            task: Task = task_queue.get()
            if task is None:  # 预留退出信号
                break
            # task_store.update(task.cid, status="running", started_at=time.time())
            try:
                llm_client.stream_chat(task)
                task_store.update(task.cid, status="done", finished_at=time.time())
            except Exception as e:
                logging.error(f"Error processing task {task.cid}: {e}")
                task_store.update(task.cid, status="failed", error=str(e), finished_at=time.time())
            finally:
                threading.Timer(
                    RETENTION_SECONDS,
                    lambda tid=task.cid: task_store.delete(tid)
                ).start()

                # 将对话内容写入数据库
                data = []
                if task.model_type == "RS":
                    data = [{
                            "cid": task.cid,
                            "role": "reasoning",
                            "content": task.reasoning_content,
                            "model_name": task.model_name,
                        }, {
                            "cid": task.cid,
                            "role": "assistant",
                            "content": task.content,
                            "model_name": task.model_name,
                        }
                    ]
                elif task.model_type == "CH":
                    data = [
                        {
                            "cid": task.cid,
                            "role": "assistant",
                            "content": task.content,
                            "model_name": task.model_name,
                        }
                    ]
                else:
                    logging.error(f"Unknown model type {task.model_type} for task {task.cid}")
            
                rsp = requests.post(f"http://{LOCAL_HOST}/site/update_communication_to_database",data=json.dumps(data),headers={"Content-Type":"application/json"})
                if rsp.status_code != 200:
                    logging.error(f"Failed to update comm reasoning for task {task.cid}: {rsp.status_code} reason {rsp.text}")
                task_queue.task_done()

def start_workers(n: int):
    for _ in range(n):
        Worker().start()


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        # 开发环境放开同源限制，生产请改白名单
        origin = self.request.headers.get("Origin", "*")
        self.set_header("Access-Control-Allow-Origin", origin if origin else "*")
        self.set_header("Vary", "Origin")
        self.set_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Max-Age", "600")

    def options(self, *args, **kwargs):
        # 处理 CORS 预检，避免 405
        self.set_status(204)
        self.finish()

    def write_json(self, obj: Dict[str, Any], status: int = 200):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.set_status(status)
        self.finish(json.dumps(obj, ensure_ascii=False))

class SubmitHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body.decode("utf-8"))
        except Exception:
            return self.write_json({"status": "error", "reason":"invalid json"}, 400)

        messages = data.get("messages")
        model_name = data.get("model_name")
        params = data.get("params", {})
        if not isinstance(messages, list) or not model_name:
            return self.write_json({"error": "body must include messages(list) and model_name(str)"}, 400)
        logging.info(f"Received task: messages={messages} \n, model_name={model_name} \n, params={params}")

        try:
            cid = data.get("cid")
            task = Task(cid=cid,messages=messages,model_name=model_name,params=params)
            task_store.add(task)
            task_queue.put(task, block=False)
        except queue.Full:
            return self.write_json({"status": "error", "reason":"queue full"}, 200)

        return self.write_json({"status":"ok","cid": cid})

class ContentHandler(BaseHandler):
    async def get(self):
        cid = self.get_query_argument("cid", None)
        query_type = self.get_query_argument("query_type", "content") # reasoning / content
        last_index = self.get_query_argument("last_index", "0")
        if not cid:
            return self.write_json({"error": "cid is required"}, 400)
        
        t = task_store.get(cid)
        if not t:
            return self.write_json({"error": "task not found"}, 404)
        if query_type not in ("reasoning", "content"):
            return self.write_json({"error": "query_type must be 'reasoning' or 'content'"}, 400)
        
        last_index = int(last_index)
        if query_type == "reasoning":
            new_content = t.reasoning_content[int(last_index):]
            if new_content:
                return self.write_json({"status": t.status,"reasoning_content": new_content,})
            else:
                return self.write_json({"status": t.status,"reasoning_content": "",})
        else:
            new_content = t.content[int(last_index):]
            if new_content:
                return self.write_json({"status": t.status,"content": new_content,})
            else:
                return self.write_json({"status": t.status,"content": "",})
        
class StatusHandler(BaseHandler):
    async def get(self):
        cid = self.get_query_argument("cid", None)
        if cid is None:
            return self.write_json({"status": "error","reason": "cid is required"})
        
        t = task_store.get(cid)
        if not t:
            return self.write_json({"status": "error","reason": "task not found"})

        return self.write_json({
            "status": "ok",
            "model_name": t.model_name,
            "model_type": t.model_type,
        })

class HealthHandler(BaseHandler):
    async def get(self):
        return self.write_json({"status": "ok","talk_test": TALK_TEST})

def make_app():
    return tornado.web.Application([
        (r"/submit", SubmitHandler),
        (r"/content", ContentHandler),
        (r"/status", StatusHandler),
        (r"/health", HealthHandler),
    ])

def main():
    try:
        rsp = requests.get(f"http://{LOCAL_HOST}/health/",timeout=1)
    except Exception as e:
        print(f"Error: Cannot reach local server at port {LOCAL_SERVER_PORT}. Please ensure the main server is running.")
        return
    start_workers(MAX_WORKERS)
    app = make_app()
    app.listen(PORT, address=HOST)  # 仅监听本机地址
    print(f"Server listening on http://{HOST}:{PORT}")
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
