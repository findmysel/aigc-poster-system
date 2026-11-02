"""
海报合成器
将图片和文案合成为最终海报
"""
from PIL import Image, ImageDraw, ImageFont
import io
from django.core.files.base import ContentFile


# 跨平台中文字体候选（Windows 微软雅黑 / Linux Noto CJK / macOS 苹方）
FONT_CANDIDATES = [
    "msyh.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]


def load_cjk_font(size):
    """按候选顺序加载中文字体，全部失败时用 PIL 默认字体"""
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


class PosterComposer:
    """海报合成器"""
    
    # 布局模板配置
    LAYOUTS = {
        'center': {
            'text_position': 'center',
            'text_align': 'center',
            'padding': 50,
        },
        'bottom': {
            'text_position': 'bottom',
            'text_align': 'center',
            'padding': 30,
        },
        'top': {
            'text_position': 'top',
            'text_align': 'center',
            'padding': 30,
        },
        'overlay': {
            'text_position': 'overlay',
            'text_align': 'center',
            'padding': 40,
        },
    }
    
    def __init__(self, background_image):
        """
        初始化合成器
        :param background_image: 背景图像（Django ImageFieldFile）
        """
        self.background = Image.open(background_image)
        self.draw = ImageDraw.Draw(self.background)
        self.width, self.height = self.background.size
    
    def compose(self, copy_data, layout='center', text_color='#FFFFFF', 
                headline_size=60, subheadline_size=36, cta_size=28, description_size=24):
        """
        合成海报
        :param copy_data: 文案数据 {'headline': '', 'subheadline': '', 'cta': ''}
        :param layout: 布局类型
        :param text_color: 文字颜色
        :param headline_size: 主标题字号
        :param subheadline_size: 副标题字号
        :param cta_size: CTA字号
        :return: ContentFile对象
        """
        layout_config = self.LAYOUTS.get(layout, self.LAYOUTS['center'])
        
        # 加载中文字体（跨平台候选，见 load_cjk_font）
        font_headline = load_cjk_font(headline_size)
        font_subheadline = load_cjk_font(subheadline_size)
        font_cta = load_cjk_font(cta_size)
        font_description = load_cjk_font(description_size)
        
        # 根据布局计算位置
        if layout_config['text_position'] == 'center':
            y_position = self.height // 2
        elif layout_config['text_position'] == 'bottom':
            y_position = self.height - 200
        elif layout_config['text_position'] == 'top':
            y_position = 150
        else:  # overlay
            y_position = self.height // 2
        
        # 绘制半透明背景（如果布局为overlay）
        if layout == 'overlay':
            overlay = Image.new('RGBA', self.background.size, (0, 0, 0, 128))
            self.background = Image.alpha_composite(
                self.background.convert('RGBA'), 
                overlay
            )
            self.draw = ImageDraw.Draw(self.background)
        
        # 绘制主标题
        headline = copy_data.get('headline', '')
        if headline:
            bbox = self.draw.textbbox((0, 0), headline, font=font_headline)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            self._draw_text_with_shadow(x, y_position - 60, headline, font_headline, text_color)
        
        # 绘制副标题
        subheadline = copy_data.get('subheadline', '')
        if subheadline:
            bbox = self.draw.textbbox((0, 0), subheadline, font=font_subheadline)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            self._draw_text_with_shadow(x, y_position + 20, subheadline, font_subheadline, text_color)
        
        # 绘制描述文字（需求 5.3.2 步骤6：主标题、副标题、CTA 和描述都要合成）
        description = copy_data.get('description', '')
        desc_lines = 0
        if description:
            max_width = self.width - 80
            lines = []
            current = ''
            for ch in description:
                trial = current + ch
                bbox = self.draw.textbbox((0, 0), trial, font=font_description)
                if bbox[2] - bbox[0] > max_width and current:
                    lines.append(current)
                    current = ch
                else:
                    current = trial
            if current:
                lines.append(current)
            for idx, line in enumerate(lines[:2]):
                bbox = self.draw.textbbox((0, 0), line, font=font_description)
                x = (self.width - (bbox[2] - bbox[0])) // 2
                self._draw_text_with_shadow(x, y_position + 76 + idx * (description_size + 8), line, font_description, text_color)
            desc_lines = min(len(lines), 2)

        # 绘制CTA按钮背景
        cta = copy_data.get('cta', '')
        if cta:
            bbox = self.draw.textbbox((0, 0), cta, font=font_cta)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            button_padding_x = 40
            button_padding_y = 15
            button_width = text_width + button_padding_x * 2
            button_height = text_height + button_padding_y * 2
            
            button_x = (self.width - button_width) // 2
            button_y = y_position + 100 + (desc_lines * 40 if desc_lines else 0)
            
            # 绘制按钮背景
            self.draw.rounded_rectangle(
                [button_x, button_y, button_x + button_width, button_y + button_height],
                radius=10,
                fill='#FF6B6B'
            )
            
            # 绘制CTA文字
            text_x = button_x + button_padding_x
            text_y = button_y + button_padding_y - 5
            self.draw.text((text_x, text_y), cta, font=font_cta, fill='#FFFFFF')
        
        # 保存为JPEG
        output = io.BytesIO()
        if self.background.mode == 'RGBA':
            self.background = self.background.convert('RGB')
        self.background.save(output, format='JPEG', quality=95)
        output.seek(0)
        
        return ContentFile(output.getvalue(), name='composed_poster.jpg')
    
    def _draw_text_with_shadow(self, x, y, text, font, color, shadow_color='#00000088'):
        """绘制带阴影的文字"""
        # 绘制阴影
        self.draw.text((x+2, y+2), text, font=font, fill=shadow_color)
        # 绘制主文字
        self.draw.text((x, y), text, font=font, fill=color)
    
    def add_watermark(self, text='AIGC Poster', position='bottom-right', opacity=64):
        """添加水印"""
        font = load_cjk_font(20)
        
        # 创建水印层
        watermark = Image.new('RGBA', self.background.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if position == 'bottom-right':
            x = self.width - text_width - 20
            y = self.height - text_height - 20
        elif position == 'bottom-left':
            x = 20
            y = self.height - text_height - 20
        else:
            x = 20
            y = 20
        
        draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
        
        # 合并
        self.background = Image.alpha_composite(
            self.background.convert('RGBA'),
            watermark
        )
        self.draw = ImageDraw.Draw(self.background)
    
    def resize(self, width, height):
        """调整海报尺寸"""
        self.background = self.background.resize((width, height), Image.Resampling.LANCZOS)
        self.width, self.height = width, height
        self.draw = ImageDraw.Draw(self.background)


def compose_poster(background_image, copy_data, layout='center', **kwargs):
    """
    便捷函数：合成海报
    :param background_image: 背景图像
    :param copy_data: 文案数据
    :param layout: 布局类型
    :param kwargs: 其他参数
    :return: ContentFile对象
    """
    composer = PosterComposer(background_image)
    return composer.compose(copy_data, layout, **kwargs)
