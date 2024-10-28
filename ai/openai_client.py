from openai import OpenAI

class OpenAIClient:
    def __init__(self, api_key, base_url):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def get_chat_response(self, message):
        # 调用OpenAI的API
        response = self.client.chat.completions.create(
            messages=[
                {"role": "user", "content": message}
            ],
            model="gpt-4o-mini"
        )
        # 检查返回的结果
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            # 返回AI的回复内容
            return response.choices[0].message.content
        else:
            # 如果没有得到回复，则返回一个默认信息
            return "Unable to get a response from AI."
