"""
Dify API 测试脚本
用于测试 Dify Workflow / Chatflow / Agent 应用的 API 调用。
"""

import os
import json
import requests


class DifyClient:
    """Dify API 客户端。"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("DIFY_API_KEY", "")
        self.base_url = base_url or os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def run_workflow(self, inputs: dict, user: str = "test-user") -> dict:
        """调用 Workflow 应用。"""
        url = f"{self.base_url}/workflows/run"
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user,
        }
        resp = requests.post(url, headers=self._headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

    def send_chat_message(
        self, query: str, user: str = "test-user", conversation_id: str = ""
    ) -> dict:
        """调用 Chatflow / Agent 应用。"""
        url = f"{self.base_url}/chat-messages"
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": user,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        resp = requests.post(url, headers=self._headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


def test_jd_parser(client: DifyClient, jd_text: str) -> dict:
    """测试 JD 解析器应用。"""
    print("\n[TEST] 测试 JD 解析器...")
    result = client.run_workflow(inputs={"jd_content": jd_text})
    print(f"  输出: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
    return result


def test_resume_matcher(client: DifyClient, resume: str, jd: str) -> dict:
    """测试简历匹配器应用。"""
    print("\n[TEST] 测试简历匹配器...")
    result = client.run_workflow(inputs={
        "resume_content": resume,
        "jd_content": jd,
    })
    print(f"  输出: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
    return result


def test_interview_coach(client: DifyClient, jd: str, resume: str) -> dict:
    """测试面试教练应用。"""
    print("\n[TEST] 测试面试教练...")
    prompt = f"""
## 目标职位
{jd}

## 我的简历
{resume}

## 模式：question_generation
请根据以上信息生成面试问题。
"""
    result = client.send_chat_message(query=prompt)
    print(f"  输出: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
    return result


if __name__ == "__main__":
    # 示例用法
    print("Dify API 测试脚本")
    print("请设置环境变量 DIFY_API_KEY 和 DIFY_BASE_URL 后运行。")
