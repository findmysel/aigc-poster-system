"""
个性化提示词生成器
基于用户画像生成优化的提示词
"""
from django.core.cache import cache


class PromptGenerator:
    """基于用户画像的提示词生成器"""
    
    # 风格映射表
    STYLE_KEYWORDS = {
        'minimalist': 'minimalist design, clean, simple, elegant, white space, geometric',
        'vintage': 'vintage style, retro, classic, nostalgic, aged texture, antique',
        'modern': 'modern design, contemporary, sleek, professional, trendy',
        'colorful': 'vibrant colors, colorful, energetic, bold, dynamic',
        'dark': 'dark theme, moody, dramatic, noir, sophisticated, black background',
        'fresh': 'fresh, natural, organic, light, airy, clean, green',
        'tech': 'futuristic, technology, digital, cyber, neon, high-tech',
        'hand_drawn': 'hand drawn, illustration, artistic, sketch, watercolor',
        '3d': '3D render, three-dimensional, depth, realistic, volumetric',
        'gradient': 'gradient, smooth transitions, colorful blend, modern gradient',
    }
    
    # 色彩映射表
    COLOR_KEYWORDS = {
        'warm': 'warm colors, red, orange, yellow, cozy, inviting',
        'cool': 'cool colors, blue, green, purple, calm, professional',
        'neutral': 'neutral colors, beige, gray, brown, balanced, versatile',
        'vibrant': 'vibrant, saturated colors, bright, eye-catching, bold',
        'monochrome': 'monochrome, black and white, grayscale, elegant, classic',
        'pastel': 'pastel colors, soft pink, light blue, mint, gentle, soothing',
    }
    
    # 内容类型映射
    CONTENT_TEMPLATES = {
        'promotion': {
            'prefix': 'promotional poster for sales and discounts',
            'elements': 'price tags, sale badges, discount stickers, shopping elements',
        },
        'event': {
            'prefix': 'event announcement poster',
            'elements': 'date, time, location icons, decorative elements',
        },
        'brand': {
            'prefix': 'brand identity poster',
            'elements': 'logo placement, brand colors, professional typography',
        },
        'social': {
            'prefix': 'social media post design',
            'elements': 'engaging visuals, share buttons, hashtags, trendy style',
        },
        'poster': {
            'prefix': 'artistic poster design',
            'elements': 'artistic composition, creative layout, visual impact',
        },
        'business': {
            'prefix': 'business professional poster',
            'elements': 'corporate style, professional layout, contact info',
        },
        'personal': {
            'prefix': 'personal creative poster',
            'elements': 'personal touch, lifestyle, authentic, relatable',
        },
        'holiday': {
            'prefix': 'holiday greeting poster',
            'elements': 'festive decorations, seasonal elements, celebratory',
        },
    }
    
    # 年龄段特征
    AGE_CHARACTERISTICS = {
        'teen': 'youthful, trendy, energetic, bold, modern',
        'young': 'fresh, dynamic, contemporary, stylish',
        'adult': 'professional, balanced, sophisticated, refined',
        'middle': 'elegant, classic, trustworthy, established',
        'senior': 'traditional, clear, simple, readable, warm',
    }
    
    def __init__(self, user_profile):
        """
        初始化生成器
        :param user_profile: UserProfile对象
        """
        self.profile = user_profile
    
    def generate_image_prompt(self, user_description='', content_type='', style_override=''):
        """
        生成图像生成提示词
        :param user_description: 用户输入的描述
        :param content_type: 内容类型
        :param style_override: 风格覆盖
        :return: 优化后的提示词
        """
        profile_id = getattr(self.profile, 'id', 'unknown')
        cache_key = f"img_prompt:{profile_id}:{content_type}:{style_override}:{user_description[:30]}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        components = []

        # 1. 用户描述（最高优先级）
        if user_description:
            components.append(user_description)

        # 2. 内容类型
        ct = content_type or self.profile.preferred_content
        if ct and ct in self.CONTENT_TEMPLATES:
            components.append(self.CONTENT_TEMPLATES[ct]['prefix'])
            components.append(self.CONTENT_TEMPLATES[ct]['elements'])
        else:
            components.append('professional poster design')
        
        # 3. 风格
        style = style_override or self.profile.preferred_style
        if style and style in self.STYLE_KEYWORDS:
            components.append(self.STYLE_KEYWORDS[style])
        
        # 4. 色彩
        color = self.profile.preferred_color
        if color and color in self.COLOR_KEYWORDS:
            components.append(self.COLOR_KEYWORDS[color])
        
        # 5. 年龄段特征
        age = self.profile.age_group
        if age and age in self.AGE_CHARACTERISTICS:
            components.append(self.AGE_CHARACTERISTICS[age])
        
        # 6. 通用质量标签
        components.append('high quality, detailed, 4K, professional design')

        result = ', '.join(filter(None, components))
        cache.set(cache_key, result, timeout=3600)
        return result
    
    def generate_copy_prompt(self, topic='', content_type='', tone=''):
        """
        生成文案生成提示词
        :param topic: 主题
        :param content_type: 内容类型
        :param tone: 语气
        :return: 文案生成提示词
        """
        profile_id = getattr(self.profile, 'id', 'unknown')
        cache_key = f"copy_prompt:{profile_id}:{content_type}:{tone}"
        cached = cache.get(cache_key)
        if cached:
            return cached.format(topic=topic or 'general promotion')

        ct = content_type or self.profile.preferred_content or 'general'
        
        # 根据用户画像确定语气
        if not tone:
            if self.profile.age_group in ['teen', 'young']:
                tone = 'casual, engaging, trendy'
            elif self.profile.occupation in ['business', 'finance', 'it']:
                tone = 'professional, concise, impactful'
            else:
                tone = 'friendly, approachable, clear'
        
        prompt_template = f"""Generate a short, catchy poster copy for a {ct} poster.
Topic: {{topic}}
Tone: {tone}

Requirements:
- Main headline: 5-10 words
- Optional subheadline: 8-15 words
- Call to action: 3-5 words
- Language: Chinese (Simplified)

Return in JSON format:
{{{{
    "headline": "main title",
    "subheadline": "subtitle",
    "cta": "call to action"
}}}}
"""
        cache.set(cache_key, prompt_template, timeout=3600)
        return prompt_template.format(topic=topic or 'general promotion')
    
    def generate_negative_prompt(self):
        """生成负面提示词（排除不需要的元素）"""
        return 'low quality, blurry, distorted, ugly, deformed, text error, watermark, signature, cropped, out of frame'
    
    def generate_sample_prompts(self, count=3):
        """生成示例提示词供用户预览"""
        samples = []
        sample_descriptions = [
            '夏季新品上市',
            '年终大促销活动',
            '创意艺术展览',
        ]
        
        for i in range(min(count, len(sample_descriptions))):
            prompt = self.generate_image_prompt(sample_descriptions[i])
            samples.append({
                'description': sample_descriptions[i],
                'prompt': prompt
            })
        
        return samples
    
    def adjust_prompt_by_feedback(self, original_prompt, feedback_params):
        """
        根据用户反馈调整提示词
        :param original_prompt: 原提示词
        :param feedback_params: 反馈参数
        :return: 调整后的提示词
        """
        adjustments = []
        
        if feedback_params.get('adjust_style'):
            adjustments.append('different style, improved composition')
        
        if feedback_params.get('adjust_color'):
            adjustments.append('better color harmony, enhanced colors')
        
        if feedback_params.get('adjust_layout'):
            adjustments.append('improved layout, better composition')
        
        if feedback_params.get('adjust_copy'):
            adjustments.append('different concept, alternative approach')
        
        if adjustments:
            return original_prompt + ', ' + ', '.join(adjustments)
        
        return original_prompt
