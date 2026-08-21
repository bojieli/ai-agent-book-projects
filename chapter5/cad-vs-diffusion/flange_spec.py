"""实验 5-7 主线任务规格：法兰盘。

两条路线（代码生成 vs 3D 生成模型）共用这一份规格与变更请求。
所有尺寸单位 mm。
"""

FLANGE_SPEC_TEXT = (
    "法兰盘，外径 80mm，厚度 10mm，4 个均布 M5 安装孔（孔径 5.5mm），"
    "孔位圆直径 60mm"
)

CHANGE_REQUEST_TEXT = "安装孔从 M5 改为 M6（孔径 6.5mm）"

# 变更前的规格（M5）
SPEC_M5 = {
    "outer_diameter_mm": 80.0,
    "thickness_mm": 10.0,
    "hole_count": 4,
    "hole_diameter_mm": 5.5,
    "hole_circle_diameter_mm": 60.0,
}

# 变更后的规格（M6），其余尺寸不变
SPEC_M6 = dict(SPEC_M5, hole_diameter_mm=6.5)

# 变更请求下不应漂移的尺寸
UNCHANGED_KEYS = ["outer_diameter_mm", "thickness_mm", "hole_count", "hole_circle_diameter_mm"]

# 对照组任务
PLANT_PROMPT = "一盆绿植（带花盆的室内观叶植物），写实风格"
