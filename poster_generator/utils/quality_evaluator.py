"""
海报质量评估（导师链路第 5 环：海报质量评估）

本地 Pillow 图像指标评估，不调用任何外部 API（免费）：
- 清晰度 sharpness：边缘强度（FIND_EDGES 后灰度标准差）
- 对比度 contrast：灰度标准差
- 色彩丰富度 colorfulness：Hasler & Süsstrunk 色彩度量
- 饱和度 saturation：HSV 通道 S 均值
- 亮度适中度 brightness_balance：平均亮度越接近中间值越好
综合分 0-100，并给出等级与改进建议。评估对象为合成后的最终海报，
同时可用于背景图。指标为启发式归一化，适合毕设演示与横向对比，
不代表专业审美评分。
"""
import io
import logging

from PIL import Image, ImageFilter, ImageStat

logger = logging.getLogger('poster_generator')


def _open_image(image_source):
    """接受文件路径、Django FieldFile、BytesIO 或 PIL Image，返回 RGB Image"""
    if isinstance(image_source, Image.Image):
        return image_source.convert('RGB')
    if hasattr(image_source, 'open'):
        image_source.open()
    img = Image.open(image_source)
    img.load()
    if hasattr(image_source, 'seek'):
        try:
            image_source.seek(0)
        except Exception:
            pass
    return img.convert('RGB')


def evaluate_poster(image_source):
    """
    评估海报质量
    :return: {
        'score': 综合分 0-100,
        'level': '优秀'/'良好'/'一般'/'待改进',
        'metrics': {'sharpness':..,'contrast':..,'colorfulness':..,'saturation':..,'brightness_balance':..},
        'suggestions': [...]
    }
    评估失败时返回 score=None，不阻断生成流程。
    """
    try:
        img = _open_image(image_source)
    except Exception as e:
        logger.warning('质量评估打开图片失败：%s', e)
        return {'score': None, 'level': '未评估', 'metrics': {}, 'suggestions': ['图片无法读取，未完成质量评估']}

    try:
        gray = img.convert('L')
        gstat = ImageStat.Stat(gray)
        mean_l = gstat.mean[0]                    # 0-255
        std_l = gstat.stddev[0]                   # 对比度原始值

        # 清晰度：边缘图标准差，经验上 0-80 归一化
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_std = ImageStat.Stat(edges).stddev[0]
        sharpness = min(edge_std / 80.0, 1.0) * 100

        # 对比度：标准差 0-90 归一化
        contrast = min(std_l / 90.0, 1.0) * 100

        # 色彩丰富度（Hasler & Süsstrunk）
        small = img.resize((max(1, img.width // 4), max(1, img.height // 4)))
        px = list(small.getdata())
        n = len(px)
        rg = [r - g for r, g, b in px]
        yb = [0.5 * (r + g) - b for r, g, b in px]
        def _std(vals):
            m = sum(vals) / n
            return (sum((v - m) ** 2 for v in vals) / n) ** 0.5, m
        rg_std, rg_mean = _std(rg)
        yb_std, yb_mean = _std(yb)
        colorfulness_raw = (rg_std ** 2 + yb_std ** 2) ** 0.5 + 0.3 * (rg_mean ** 2 + yb_mean ** 2) ** 0.5
        colorfulness = min(colorfulness_raw / 80.0, 1.0) * 100

        # 饱和度：HSV 的 S 均值
        sat_mean = ImageStat.Stat(img.convert('HSV').split()[1]).mean[0]
        saturation = sat_mean / 255.0 * 100

        # 亮度适中度：均值越接近 128 越好，偏离 90 以上记 0
        brightness_balance = max(0.0, 1.0 - abs(mean_l - 128) / 90.0) * 100

        metrics = {
            'sharpness': round(sharpness, 1),
            'contrast': round(contrast, 1),
            'colorfulness': round(colorfulness, 1),
            'saturation': round(saturation, 1),
            'brightness_balance': round(brightness_balance, 1),
        }
        score = round(
            sharpness * 0.30 + contrast * 0.25 + colorfulness * 0.20
            + saturation * 0.10 + brightness_balance * 0.15, 1)

        if score >= 80:
            level = '优秀'
        elif score >= 65:
            level = '良好'
        elif score >= 50:
            level = '一般'
        else:
            level = '待改进'

        suggestions = []
        if sharpness < 50:
            suggestions.append('画面清晰度偏低，建议重新生成或提高生成步数')
        if contrast < 45:
            suggestions.append('画面对比度不足，文字与背景可能不够醒目')
        if colorfulness < 35:
            suggestions.append('色彩较单一，可尝试更高饱和的色彩方案')
        if brightness_balance < 50:
            suggestions.append('画面整体过亮或过暗，建议调整色彩方案')
        if not suggestions:
            suggestions.append('各项指标均衡，无需调整')

        return {'score': score, 'level': level, 'metrics': metrics, 'suggestions': suggestions}
    except Exception as e:
        logger.warning('质量评估计算失败：%s', e)
        return {'score': None, 'level': '未评估', 'metrics': {}, 'suggestions': ['质量评估计算失败']}
