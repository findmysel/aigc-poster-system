"""
文案生成器
集成智谱 GLM-4-Flash API（免费额度）
"""
import json
import re
from django.conf import settings


class CopyGenerator:
    """文案生成器"""

    def __init__(self):
        self.api_key = getattr(settings, 'ZHIPUAI_API_KEY', '')
        self.model = 'glm-4-flash'

    def generate_copy(self, topic='', content_type='promotion', tone='professional', user_profile=None):
        """
        生成海报文案
        :param topic: 主题
        :param content_type: 内容类型
        :param tone: 语气风格
        :param user_profile: 用户画像
        :return: {'success': bool, 'data': copy_dict}
        """
        if not self.api_key:
            return {'success': True, 'data': self._generate_mock_copy(topic, content_type)}

        system_prompt = """你是一个专业的海报文案生成助手。请为海报生成简短、有吸引力的文案。
请严格按照JSON格式返回，包含以下字段：
- headline: 主标题（5-10字）
- subheadline: 副标题（8-15字）
- cta: 行动号召（3-5字）
- description: 简短描述（20-30字）

只返回JSON，不要其他解释。示例：
{"headline": "夏日清凉特惠", "subheadline": "全场五折起，限时抢购", "cta": "立即购买", "description": "炎炎夏日，为您精选清凉好物，限时特惠中"}"""

        user_prompt = f"请为以下内容生成海报文案：\n主题：{topic or '创意海报'}\n内容类型：{content_type}\n语气风格：{tone}"
        if user_profile:
            user_prompt += f"\n目标用户：{user_profile.age_group}岁{user_profile.get_gender_display()}"

        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            raw = response.choices[0].message.content
            copy_data = self._fill_defaults(self._parse_response(raw))
            return {'success': True, 'data': copy_data}
        except Exception:
            return {'success': True, 'data': self._generate_mock_copy(topic, content_type)}

    def regenerate_copy(self, original_copy, feedback, content_type='promotion'):
        """
        根据反馈重新生成文案
        :param original_copy: 原文案（dict）
        :param feedback: 用户反馈描述
        :param content_type: 内容类型
        :return: {'success': bool, 'data': copy_dict}
        """
        if not self.api_key:
            return {'success': True, 'data': self._generate_mock_copy(feedback, content_type)}

        system_prompt = """你是一个专业的海报文案生成助手。请根据用户的反馈修改文案。
只返回JSON，格式：{"headline": "", "subheadline": "", "cta": "", "description": ""}"""

        original_str = json.dumps(original_copy, ensure_ascii=False)
        user_prompt = f"原文案：{original_str}\n\n用户反馈：{feedback}\n\n请根据反馈修改文案，内容类型：{content_type}"

        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            raw = response.choices[0].message.content
            copy_data = self._fill_defaults(self._parse_response(raw))
            return {'success': True, 'data': copy_data}
        except Exception:
            return {'success': True, 'data': self._generate_mock_copy(feedback, content_type)}

    def _parse_response(self, content):
        """解析 GLM 返回的 JSON，失败时降级为纯文本拆分"""
        # 提取 ```json ... ``` 代码块
        match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        # 直接尝试解析整体 JSON
        try:
            return json.loads(content)
        except Exception:
            pass
        # 降级：将文本内容塞入字段
        text = content.strip()
        return self._fill_defaults({
            'headline': text[:20] if text else '精彩内容',
            'subheadline': text[20:50] if len(text) > 20 else '欢迎关注',
            'cta': '立即了解',
            'description': text[:80] if text else '',
        })

    @staticmethod
    def _fill_defaults(copy_data):
        """文案字段缺失时用默认值补全（需求 5.3.3）"""
        defaults = {
            'headline': '精彩内容',
            'subheadline': '欢迎关注',
            'cta': '立即了解',
            'description': '更多精彩内容，敬请期待。',
        }
        if not isinstance(copy_data, dict):
            return defaults
        for key, value in defaults.items():
            if not copy_data.get(key):
                copy_data[key] = value
        return copy_data

    def _generate_mock_copy(self, topic, content_type):
        """无 API key 或 API 失败时的模板降级"""
        templates = {
            'promotion': {
                'headline': '限时特惠',
                'subheadline': '全场商品低至5折',
                'cta': '立即抢购',
                'description': '精选好物，限时优惠，错过等一年！',
            },
            'event': {
                'headline': '精彩活动',
                'subheadline': '邀您共同参与',
                'cta': '报名参加',
                'description': '精彩内容等你来，与志同道合的朋友一起！',
            },
            'brand': {
                'headline': '品质之选',
                'subheadline': '匠心打造每一刻',
                'cta': '了解更多',
                'description': '专注品质，用心服务，为您创造美好生活。',
            },
            'social': {
                'headline': '分享时刻',
                'subheadline': '记录美好生活',
                'cta': '点击分享',
                'description': '生活需要仪式感，记录每一个精彩瞬间。',
            },
        }
        return templates.get(content_type, templates['promotion'])


class TemplateCopyProvider:
    """模板文案提供者（无需API）"""

    TEMPLATES = {
        'promotion': [
            {'headline': '限时特惠', 'subheadline': '全场商品低至5折起', 'cta': '立即抢购'},
            {'headline': '年中大促', 'subheadline': '好物推荐，省钱攻略', 'cta': '查看详情'},
            {'headline': '会员专享', 'subheadline': '专属折扣等你领取', 'cta': '领取优惠'},
        ],
        'event': [
            {'headline': '精彩活动', 'subheadline': '邀您共同参与', 'cta': '报名参加'},
            {'headline': '不容错过', 'subheadline': '年度盛典即将开启', 'cta': '预约席位'},
            {'headline': '线下聚会', 'subheadline': '与大咖面对面交流', 'cta': '立即报名'},
        ],
        'brand': [
            {'headline': '品质之选', 'subheadline': '匠心打造每一刻', 'cta': '了解更多'},
            {'headline': '值得信赖', 'subheadline': '十年专注，品质如一', 'cta': '关于我们'},
            {'headline': '创新引领', 'subheadline': '科技改变生活', 'cta': '探索产品'},
        ],
        'social': [
            {'headline': '分享时刻', 'subheadline': '记录美好生活', 'cta': '点击分享'},
            {'headline': '生活美学', 'subheadline': '发现身边的美好', 'cta': '关注更多'},
            {'headline': '达人推荐', 'subheadline': '精选好物每日更新', 'cta': '查看推荐'},
        ],
        'holiday': [
            {'headline': '节日快乐', 'subheadline': '愿您幸福安康', 'cta': '发送祝福'},
            {'headline': '新春大吉', 'subheadline': '万事如意迎新年', 'cta': '领取红包'},
            {'headline': '感恩有你', 'subheadline': '一路陪伴，感谢支持', 'cta': '表达感谢'},
        ],
    }

    DESCRIPTIONS = {
        'promotion': '精选好物限时优惠，错过等一年！',
        'event': '精彩内容等你来，与志同道合的朋友一起！',
        'brand': '专注品质，用心服务，为您创造美好生活。',
        'social': '生活需要仪式感，记录每一个精彩瞬间。',
        'holiday': '把最真挚的祝福，送给最重要的你。',
    }

    @classmethod
    def get_copy(cls, content_type, index=0):
        templates = cls.TEMPLATES.get(content_type, cls.TEMPLATES['promotion'])
        result = dict(templates[index % len(templates)])
        result.setdefault('description', cls.DESCRIPTIONS.get(content_type, cls.DESCRIPTIONS['promotion']))
        return result

    @classmethod
    def get_random_copy(cls, content_type):
        import random
        templates = cls.TEMPLATES.get(content_type, cls.TEMPLATES['promotion'])
        result = dict(random.choice(templates))
        result.setdefault('description', cls.DESCRIPTIONS.get(content_type, cls.DESCRIPTIONS['promotion']))
        return result
