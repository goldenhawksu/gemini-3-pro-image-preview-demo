import base64
import requests
import json
import os
from typing import List, Dict, Optional, Union

# 配置
API_URL = "https://www.packyapi.com/v1beta/models/gemini-3-pro-image-preview:generateContent"
API_KEY = os.getenv("LOCAL_GEMINI_API_KEY", "YOUR_API_KEY_HERE")  # 从环境变量获取或直接替换

class GeminiImageChat:
    """Gemini 图片生成多轮对话客户端"""

    def __init__(self, api_key: str = None, api_url: str = API_URL):
        self.api_key = api_key or os.getenv("LOCAL_GEMINI_API_KEY")
        self.api_url = api_url
        self.conversation_history = []  # 存储对话历史
        self.thought_signature = None  # 存储思考签名

    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []
        self.thought_signature = None

    def _extract_image_data(self, response: dict) -> Optional[str]:
        """从响应中提取图片的 base64 数据"""
        for part in response.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'inlineData' in part:
                return part['inlineData']['data']
        return None

    def _extract_thought_signature(self, response: dict) -> Optional[str]:
        """从响应中提取思考签名"""
        return response.get('thought_signature')

    def _extract_thinking_images(self, response: dict) -> List[str]:
        """提取思考过程中的图片"""
        thinking_images = []
        for candidate in response.get('candidates', []):
            for part in candidate.get('content', {}).get('parts', []):
                if part.get('thought') and 'inlineData' in part:
                    thinking_images.append(part['inlineData']['data'])
        return thinking_images

    def _build_contents(self, prompt: str, image_data: Optional[List[str]] = None,
                       image_mime_types: Optional[List[str]] = None) -> List[Dict]:
        """构建请求的 contents 部分"""

        # 添加当前用户输入
        current_content = {
            "role": "user",
            "parts": []
        }

        # 添加当前用户的文本和图片
        current_content['parts'].append({"text": prompt})

        if image_data:
            for img_data, mime_type in zip(image_data, image_mime_types):
                current_content['parts'].append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": img_data
                    }
                })

        # 构建完整的 contents
        contents = self.conversation_history + [current_content]
        return contents

    def send_message(self,
                     prompt: str,
                     image_data: Optional[List[str]] = None,
                     image_mime_types: Optional[List[str]] = None,
                     aspect_ratio: str = "1:1",
                     image_size: str = "2K",
                     include_thinking: bool = False,
                     use_search: bool = False) -> Dict:
        """
        发送消息并获取回复

        Args:
            prompt: 用户输入的提示
            image_data: 图片的 base64 数据列表（可选）
            image_mime_types: 图片的 MIME 类型列表（可选）
            aspect_ratio: 宽高比
            image_size: 图片大小
            include_thinking: 是否包含思考过程
            use_search: 是否使用 Google 搜索

        Returns:
            包含响应文本、图片数据和元数据的字典
        """

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # 构建请求体
        contents = self._build_contents(prompt, image_data, image_mime_types)

        payload = {
            "contents": contents,
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }

        # 添加图片配置
        payload["generationConfig"]["imageConfig"] = {
            "aspectRatio": aspect_ratio,
            "imageSize": image_size
        }

        # 添加搜索工具
        if use_search:
            payload["tools"] = [{"google_search": {}}]

        response = requests.post(self.api_url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"错误: {response.status_code}")
            print(response.text)
            raise Exception(f"API请求失败: {response.status_code}")

        result = response.json()

        # 提取图片数据
        image_data = self._extract_image_data(result)

        # 提取思考签名
        self.thought_signature = self._extract_thought_signature(result)

        # 提取思考过程中的图片（可选）
        thinking_images = []
        if include_thinking:
            thinking_images = self._extract_thinking_images(result)

        # 保存用户消息到历史（修复上下文丢失 bug）
        user_message = {
            "role": "user",
            "parts": [{"text": prompt}]
        }
        if image_data:
            for img_data, mime_type in zip(image_data, image_mime_types):
                user_message['parts'].append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": img_data
                    }
                })
        self.conversation_history.append(user_message)

        # 保存对话历史
        if 'candidates' in result and result['candidates']:
            assistant_response = {
                "role": "assistant",
                "parts": []
            }

            # 添加思考过程图片
            if thinking_images:
                for img in thinking_images:
                    assistant_response['parts'].append({
                        "inlineData": {"mime_type": "image/png", "data": img},
                        "thought": True
                    })

            # 添加最终响应文本
            for part in result['candidates'][0]['content']['parts']:
                if 'text' in part:
                    assistant_response['parts'].append({"text": part['text']})
                elif 'inlineData' in part:
                    assistant_response['parts'].append({
                        "inlineData": part['inlineData'],
                        "thought": False
                    })

            self.conversation_history.append(assistant_response)

        return {
            "text": result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', ''),
            "image_data": image_data,
            "thinking_images": thinking_images,
            "thought_signature": self.thought_signature,
            "grounding_metadata": result.get('groundingMetadata'),
            "raw_response": result
        }

    def generate_image(self,
                       prompt: str,
                       aspect_ratio: str = "1:1",
                       image_size: str = "2K",
                       save_path: Optional[str] = None) -> Optional[str]:
        """
        生成图片（便捷方法）

        Returns:
            base64编码的图片数据或保存的文件路径
        """
        response = self.send_message(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            image_size=image_size
        )

        if response['image_data'] and save_path:
            save_base64_image(response['image_data'], save_path)
            return save_path

        return response['image_data']

    def edit_image_iteratively(self,
                               input_image_path: str,
                               edit_prompt: str,
                               output_path: str = "edited_image.png",
                               aspect_ratio: str = "1:1",
                               image_size: str = "2K") -> str:
        """
        迭代编辑图片

        Args:
            input_image_path: 输入图片路径
            edit_prompt: 编辑指令
            output_path: 输出文件路径
            aspect_ratio: 宽高比
            image_size: 图片大小

        Returns:
            保存的文件路径
        """
        with open(input_image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        mime_type = "image/png" if input_image_path.lower().endswith('.png') else "image/jpeg"

        response = self.send_message(
            prompt=edit_prompt,
            image_data=[img_base64],
            image_mime_types=[mime_type],
            aspect_ratio=aspect_ratio,
            image_size=image_size
        )

        if response['image_data']:
            save_base64_image(response['image_data'], output_path)
            return output_path

        raise Exception("未生成图片")

    def create_multi_image_composite(self,
                                     prompt: str,
                                     image_paths: List[str],
                                     output_path: str = "composite.png",
                                     aspect_ratio: str = "5:4",
                                     image_size: str = "2K") -> str:
        """
        使用多张参考图片合成新图片

        Args:
            prompt: 合成指令
            image_paths: 参考图片路径列表（最多14张）
            output_path: 输出文件路径
            aspect_ratio: 宽高比
            image_size: 图片大小

        Returns:
            保存的文件路径
        """
        if len(image_paths) > 14:
            raise ValueError("最多支持14张参考图片")

        image_data = []
        image_mime_types = []

        for path in image_paths:
            with open(path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
            image_data.append(img_base64)
            mime_type = "image/png" if path.lower().endswith('.png') else "image/jpeg"
            image_mime_types.append(mime_type)

        response = self.send_message(
            prompt=prompt,
            image_data=image_data,
            image_mime_types=image_mime_types,
            aspect_ratio=aspect_ratio,
            image_size=image_size
        )

        if response['image_data']:
            save_base64_image(response['image_data'], output_path)
            return output_path

        raise Exception("未生成图片")

    def continue_conversation(self,
                              follow_up_prompt: str,
                              include_history: bool = True,
                              aspect_ratio: str = "1:1",
                              image_size: str = "2K") -> Dict:
        """
        基于之前对话继续会话

        Args:
            follow_up_prompt: 后续提示
            include_history: 是否包含历���对话
            aspect_ratio: 宽高比
            image_size: 图片大小

        Returns:
            响应数据
        """
        if not include_history:
            self.reset_conversation()

        return self.send_message(
            prompt=follow_up_prompt,
            aspect_ratio=aspect_ratio,
            image_size=image_size
        )


def save_base64_image(base64_data: str, output_path: str):
    """保存base64图片数据到文件"""
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(base64_data))


# ============================================================================
# 以下是原有的单次请求函数，保持向后兼容
# ============================================================================

def generate_image_from_text(prompt, aspect_ratio="1:1", image_size="2K"):
    """
    从文本提示生成图片（单次请求）

    Args:
        prompt: 文本描述
        aspect_ratio: 宽高比 ("1:1", "16:9", "4:3", "3:2", "9:16", "21:9")
        image_size: 图片大小 ("1K", "2K", "4K")

    Returns:
        base64编码的图片数据
    """

    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
                "imageSize": image_size
            }
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()

        # 从响应中提取base64图片数据
        for part in result.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'inlineData' in part:
                return part['inlineData']['data']

        raise Exception("未找到图片数据")
    else:
        print(f"错误: {response.status_code}")
        print(response.text)
        raise Exception(f"API请求失败: {response.status_code}")


def generate_image_with_reference(prompt, image_paths, aspect_ratio="1:1", image_size="2K"):
    """
    使用参考图片生成或编辑图片（单次请求）

    Args:
        prompt: 文本���述
        image_paths: 参考图片路径列表
        aspect_ratio: 宽高比
        image_size: 图片大小

    Returns:
        base64编码的图片数据
    """

    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    # 将图片转换为base64
    parts = [{"text": prompt}]
    for image_path in image_paths:
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            mime_type = "image/png" if image_path.lower().endswith('.png') else "image/jpeg"
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_base64
                }
            })

    payload = {
        "contents": [{
            "parts": parts
        }],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
                "imageSize": image_size
            }
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()

        for part in result.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'inlineData' in part:
                return part['inlineData']['data']

        raise Exception("未找到图片数据")
    else:
        print(f"错误: {response.status_code}")
        print(response.text)
        raise Exception(f"API请求失败: {response.status_code}")


def save_image_with_search(prompt, output_path, aspect_ratio="16:9"):
    """
    使用Google搜索接地的图片生成（用于获取实时信息）

    Args:
        prompt: 包含实时信息的提示
        output_path: 输出文件路径
        aspect_ratio: 宽高比
    """

    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio
            }
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()

        # 保存grounding信息以供参考
        if 'groundingMetadata' in result:
            print("搜索接地元数据:")
            print(json.dumps(result['groundingMetadata'], indent=2, ensure_ascii=False))

        for part in result.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'inlineData' in part:
                save_base64_image(part['inlineData']['data'], output_path)
                return

        raise Exception("未找到图片数据")
    else:
        print(f"错误: {response.status_code}")
        print(response.text)
        raise Exception(f"API请求失败: {response.status_code}")


# ============================================================================
# 多轮对话示例
# ============================================================================

def example_conversational_image_generation():
    """多轮对话生成图片示例"""

    # 创建对话客户端
    chat = GeminiImageChat()

    # 第一轮：生成初始图片
    print("=== 第1轮：创建光合作用信息图 ===")
    response1 = chat.send_message(
        prompt="创建一个生动鲜艳的信息图，解释光合作用就像植物最喜欢的食谱。显示'食材'（阳光、水、CO2）和'成品'（糖/能量）。风格应该像彩色儿童烹饪书的一页，适合4年级学生。",
        aspect_ratio="16:9",
        image_size="2K"
    )

    if response1['image_data']:
        save_base64_image(response1['image_data'], "photosynthesis_v1.png")
        print(f"第一版图片已保存")
        print(f"响应文本: {response1['text']}")

    # 第二轮：要求修改为西班牙语
    print("\n=== 第2轮：修改为西班牙语 ===")
    response2 = chat.send_message(
        prompt="请将此信息图更新为西班牙语。不要更改图片的任何其他元素。",
        aspect_ratio="16:9",
        image_size="2K"
    )

    if response2['image_data']:
        save_base64_image(response2['image_data'], "photosynthesis_v2.png")
        print(f"第二版图片已保存")
        print(f"响应文本: {response2['text']}")

    # 第三轮：再次修改
    print("\n=== 第3轮：调整风格 ===")
    response3 = chat.send_message(
        prompt="保持西班牙语文本，但将颜色调整为更暖的色调（橙色和黄色为主）。",
        aspect_ratio="16:9",
        image_size="2K"
    )

    if response3['image_data']:
        save_base64_image(response3['image_data'], "photosynthesis_v3.png")
        print(f"第三版图片已保存")
        print(f"响应文本: {response3['text']}")

    return chat


def example_iterative_image_editing():
    """迭代编辑图片示例"""

    chat = GeminiImageChat()

    print("=== 迭代编辑示例 ===")

    # 首先生成一张图片
    print("生成初始图片...")
    response1 = chat.generate_image(
        prompt="一只可爱的橘猫坐在沙发上",
        aspect_ratio="1:1",
        image_size="2K",
        save_path="cat_v1.png"
    )
    print(f"初始图片已保存")

    # 编辑第一轮：添加帽子
    print("\n第一轮编辑：添加帽子")
    chat.edit_image_iteratively(
        input_image_path="cat_v1.png",
        edit_prompt="给猫咪戴上一顶蓝色的针织帽",
        output_path="cat_v2.png"
    )
    print(f"已保存到 cat_v2.png")

    # 编辑第二轮：改变背景
    print("\n第二轮编辑：改变背景")
    chat.edit_image_iteratively(
        input_image_path="cat_v2.png",
        edit_prompt="将背景改为花园场景",
        output_path="cat_v3.png"
    )
    print(f"已保存到 cat_v3.png")

    # 编辑第三轮：添加玩具
    print("\n第三轮编辑：添加玩具")
    chat.edit_image_iteratively(
        input_image_path="cat_v3.png",
        edit_prompt="在图片中添加一个小毛线球",
        output_path="cat_v4.png"
    )
    print(f"已保存到 cat_v4.png")

    return chat


def example_conversational_with_search():
    """带搜索的多轮对话示例"""

    chat = GeminiImageChat()

    print("=== 搜索接地的多轮对话 ===")

    # 第一轮：获取当前天气
    print("第一轮：生成天气图表")
    response1 = chat.send_message(
        prompt="为旧金山未来5天的天气预报创建一个现代、简洁的天气图表。显示每天的天气状况和温度。",
        aspect_ratio="16:9",
        use_search=True
    )

    if response1['image_data']:
        save_base64_image(response1['image_data'], "weather_v1.png")
        print(f"天气图表已保存")
        if response1.get('grounding_metadata'):
            print("搜索数据来源:")
            print(json.dumps(response1['grounding_metadata'], indent=2, ensure_ascii=False))

    # 第二轮：基于之前的结果修改
    print("\n第二轮：修改样式")
    response2 = chat.send_message(
        prompt="将图表颜色改为深蓝色主题，并添加合适的图标",
        aspect_ratio="16:9"
    )

    if response2['image_data']:
        save_base64_image(response2['image_data'], "weather_v2.png")
        print(f"修改后的天气图表已保存")

    return chat


if __name__ == "__main__":
    # 运行多轮对话示例
    print("开始多轮对话生成示例...\n")

    # 示例1: 对话式信息图生成
    example_conversational_image_generation()

    # 示例2: 迭代编辑图片
    # example_iterative_image_editing()

    # 示例3: 搜索接地
    # example_conversational_with_search()

    print("\n示例完成！")
