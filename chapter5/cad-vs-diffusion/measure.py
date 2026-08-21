"""法兰盘三角网格关键尺寸的程序化测量（基于 trimesh）。

测量对象：有中心圆盘 + 4 个均布通孔的回转件。
- 外径：XY 包围盒最大边长
- 厚度：Z 向高度
- 安装孔：Z 向中截面轮廓分析（外轮廓的内环即通孔）
- 安装面平整度：顶/底面区域顶点相对最小二乘拟合平面的 RMS 偏差

路线 B（3D 生成模型）的网格可能无孔、尺寸严重跑偏、表面坑洼——
这些都是实验要如实呈现的结果，测量函数对此只报告、不修饰。
"""
from __future__ import annotations

import math

import numpy as np
import trimesh


def load_mesh(path: str) -> trimesh.Trimesh:
    """加载 STL/GLB/OBJ，Scene 合并为单一 Trimesh。"""
    obj = trimesh.load(path, force=None)
    if isinstance(obj, trimesh.Scene):
        geoms = [g for g in obj.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not geoms:
            raise ValueError(f"场景中无三角网格: {path}")
        return trimesh.util.concatenate(geoms)
    return obj


def _fit_plane_rms(points: np.ndarray) -> float:
    """点到最小二乘拟合平面距离的 RMS（mm）。"""
    if len(points) < 3:
        return float("nan")
    centroid = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - centroid, full_matrices=False)
    normal = vh[-1]
    dists = np.abs((points - centroid) @ normal)
    return float(np.sqrt(np.mean(dists**2)))


def _detect_holes(mesh: trimesh.Trimesh, center_xy: np.ndarray, z_mid: float):
    """Z 向中截面轮廓分析：返回孔列表 [{diameter_mm, radius_mm}]。"""
    holes = []
    try:
        section = mesh.section(
            plane_origin=[center_xy[0], center_xy[1], z_mid],
            plane_normal=[0, 0, 1],
        )
    except Exception:
        return holes
    if section is None:
        return holes
    try:
        path2d, to_2d = section.to_planar()
    except Exception:
        return holes
    if not path2d.polygons_full:
        return holes
    # 网格中心在截面平面内的 2D 投影
    c3 = np.array([center_xy[0], center_xy[1], z_mid, 1.0])
    c2 = (to_2d @ c3)[:2]
    largest = max(path2d.polygons_full, key=lambda p: p.area)
    import shapely
    for ring in largest.interiors:
        # shapely LinearRing 的 .area 恒为 0，需转为 Polygon
        hole_poly = shapely.Polygon(ring)
        if hole_poly.area <= 0:
            continue
        r = math.sqrt(hole_poly.area / math.pi)
        c = hole_poly.centroid
        holes.append(
            {
                "diameter_mm": 2.0 * r,
                "radius_mm": float(math.hypot(c.x - c2[0], c.y - c2[1])),
            }
        )
    return holes


def measure_flange(mesh: trimesh.Trimesh, spec: dict) -> dict:
    """测量法兰网格并与 spec 比对，返回量值与偏差。"""
    bounds = mesh.bounds
    ext = bounds[1] - bounds[0]
    center_xy = (bounds[0][:2] + bounds[1][:2]) / 2.0
    z_lo, z_hi = float(bounds[0][2]), float(bounds[1][2])
    z_mid = 0.5 * (z_lo + z_hi)

    measured = {
        "outer_diameter_mm": float(max(ext[0], ext[1])),
        "thickness_mm": float(ext[2]),
    }

    holes = _detect_holes(mesh, center_xy, z_mid)
    measured["hole_count_detected"] = len(holes)
    measured["holes"] = holes
    if holes:
        measured["hole_diameter_mm"] = float(np.mean([h["diameter_mm"] for h in holes]))
        measured["hole_circle_diameter_mm"] = float(2.0 * np.mean([h["radius_mm"] for h in holes]))
    else:
        measured["hole_diameter_mm"] = None
        measured["hole_circle_diameter_mm"] = None

    # 安装面平整度：顶/底 5% 厚度区域内的顶点
    band = 0.05 * float(ext[2])
    v = mesh.vertices
    top = v[v[:, 2] >= z_hi - band]
    bottom = v[v[:, 2] <= z_lo + band]
    rms_top = _fit_plane_rms(top) if len(top) else float("nan")
    rms_bottom = _fit_plane_rms(bottom) if len(bottom) else float("nan")
    measured["mounting_face_flatness_rms_mm"] = float(np.nanmax([rms_top, rms_bottom]))
    measured["mesh_watertight"] = bool(mesh.is_watertight)
    measured["mesh_face_count"] = int(len(mesh.faces))

    # 与规格比对
    deviations = {}
    for key, skey in [
        ("outer_diameter_mm", "outer_diameter_mm"),
        ("thickness_mm", "thickness_mm"),
        ("hole_diameter_mm", "hole_diameter_mm"),
        ("hole_circle_diameter_mm", "hole_circle_diameter_mm"),
    ]:
        val = measured.get(key)
        target = spec[skey]
        if val is None:
            deviations[key] = {"spec": target, "measured": None, "abs_error_mm": None,
                               "rel_error_pct": None}
        else:
            deviations[key] = {
                "spec": target,
                "measured": round(val, 4),
                "abs_error_mm": round(val - target, 4),
                "rel_error_pct": round((val - target) / target * 100.0, 3),
            }
    deviations["hole_count"] = {
        "spec": spec["hole_count"],
        "measured": measured["hole_count_detected"],
        "match": measured["hole_count_detected"] == spec["hole_count"],
    }
    measured["deviations"] = deviations
    return measured
