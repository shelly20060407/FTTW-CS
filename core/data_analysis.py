"""
data_analysis.py - 数据分析模块
功能：
1. 计算基本统计信息
2. 温度趋势拟合
3. 异常值检测
4. 轨道参数分析
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple, List


def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    计算基本统计信息
    Args:
        df: 包含卫星遥测数据的DataFrame
    Returns:
        dict: 包含各参数的统计信息
    """
    if df.empty:
        return {}

    stats_dict = {}

    # 数值列的基本统计
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        # 基础统计量
        col_data = df[col].dropna()
        if len(col_data) > 0:
            stats_dict[col] = {
                'count': int(len(col_data)),
                'mean': float(col_data.mean()),
                'std': float(col_data.std()),
                'min': float(col_data.min()),
                '25%': float(col_data.quantile(0.25)),
                'median': float(col_data.median()),
                '75%': float(col_data.quantile(0.75)),
                'max': float(col_data.max()),
                'range': float(col_data.max() - col_data.min()),
                'variance': float(col_data.var()),
                'skewness': float(col_data.skew()),
                'kurtosis': float(col_data.kurtosis()),
                'missing': int(df[col].isnull().sum()),
                'missing_percentage': float(df[col].isnull().sum() / len(df) * 100)
            }

    # 时间相关统计
    if 'timestamp' in df.columns and not df['timestamp'].isnull().all():
        time_diff = df['timestamp'].diff().dropna()
        if len(time_diff) > 0:
            stats_dict['time_intervals'] = {
                'mean_interval_seconds': float(time_diff.dt.total_seconds().mean()),
                'std_interval_seconds': float(time_diff.dt.total_seconds().std()),
                'min_interval_seconds': float(time_diff.dt.total_seconds().min()),
                'max_interval_seconds': float(time_diff.dt.total_seconds().max())
            }

    # 相关性分析
    if len(numeric_cols) > 1:
        correlation_matrix = df[numeric_cols].corr()
        # 获取强相关性（绝对值大于0.7）
        strong_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    strong_correlations.append({
                        'variable1': numeric_cols[i],
                        'variable2': numeric_cols[j],
                        'correlation': float(corr_value)
                    })

        stats_dict['correlations'] = {
            'matrix': correlation_matrix.to_dict(),
            'strong_correlations': strong_correlations
        }

    return stats_dict


def fit_temperature_trend(df: pd.DataFrame, degree: int = 2) -> Dict[str, Any]:
    """
    温度趋势拟合
    Args:
        df: 包含温度数据的DataFrame
        degree: 多项式拟合的阶数，默认为2（二次拟合）
    Returns:
        dict: 包含拟合结果和趋势信息
    """
    if df.empty or 'temperature' not in df.columns:
        return {}

    # 确保温度数据没有NaN
    temp_data = df['temperature'].dropna()
    if len(temp_data) < 2:
        return {}

    # 创建时间序列（使用索引作为x值）
    x = np.arange(len(temp_data))
    y = temp_data.values

    # 多项式拟合
    coefficients = np.polyfit(x, y, degree)
    polynomial = np.poly1d(coefficients)

    # 计算拟合值
    y_fit = polynomial(x)

    # 计算拟合误差
    residuals = y - y_fit
    r_squared = 1 - np.sum(residuals**2) / np.sum((y - np.mean(y))**2)

    # 计算趋势（使用线性部分）
    if degree >= 1:
        slope = coefficients[-2]  # 线性项系数
        trend = "上升" if slope > 0.01 else "下降" if slope < -0.01 else "平稳"
    else:
        slope = 0
        trend = "平稳"

    # 预测未来几个点（如果数据足够）
    if len(temp_data) > 10:
        x_future = np.arange(len(temp_data), len(temp_data) + 5)
        future_predictions = polynomial(x_future)
    else:
        future_predictions = []

    result = {
        'coefficients': coefficients.tolist(),
        'r_squared': float(r_squared),
        'trend': trend,
        'slope': float(slope) if degree >= 1 else 0.0,
        'mean_residual': float(np.mean(np.abs(residuals))),
        'max_residual': float(np.max(np.abs(residuals))),
        'current_temperature': float(y[-1]) if len(y) > 0 else None,
        'average_temperature': float(np.mean(y)),
        'temperature_range': float(np.max(y) - np.min(y)),
        'future_predictions': future_predictions.tolist() if hasattr(future_predictions, 'tolist') else future_predictions
    }

    return result


def detect_outliers(df: pd.DataFrame, method: str = 'iqr', threshold: float = 1.5) -> Dict[str, List]:
    """
    异常值检测

    Args:
        df: 包含数据的DataFrame
        method: 检测方法，可选 'iqr'（四分位距） 或 'zscore'（Z分数）
        threshold: 检测阈值

    Returns:
        dict: 包含各列的异常值信息
    """
    if df.empty:
        return {}

    outliers_dict = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        data = df[col].dropna()
        if len(data) < 10:  # 数据太少不进行异常值检测
            continue

        if method == 'iqr':
            # IQR方法（箱线图方法）
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            # 找出异常值
            outlier_mask = (data < lower_bound) | (data > upper_bound)
            outlier_indices = data[outlier_mask].index.tolist()
            outlier_values = data[outlier_mask].tolist()

        elif method == 'zscore':
            # Z分数方法
            z_scores = np.abs(stats.zscore(data))
            outlier_mask = z_scores > threshold

            outlier_indices = data[outlier_mask].index.tolist()
            outlier_values = data[outlier_mask].tolist()
        else:
            continue

        if outlier_indices:
            # 获取对应的时间戳
            timestamps = []
            if 'timestamp' in df.columns:
                for idx in outlier_indices:
                    if idx in df.index:
                        timestamps.append(df.loc[idx, 'timestamp'])
                    else:
                        timestamps.append(None)
            else:
                timestamps = [None] * len(outlier_indices)

            outliers_dict[col] = {
                'count': len(outlier_indices),
                'percentage': len(outlier_indices) / len(data) * 100,
                'indices': outlier_indices,
                'values': outlier_values,
                'timestamps': timestamps,
                'method': method,
                'threshold': threshold,
                'lower_bound': float(lower_bound) if method == 'iqr' else None,
                'upper_bound': float(upper_bound) if method == 'iqr' else None
            }

    # 总统计
    if outliers_dict:
        total_outliers = sum([info['count'] for info in outliers_dict.values()])
        outliers_dict['summary'] = {
            'total_outliers': total_outliers,
            'columns_with_outliers': list(outliers_dict.keys()),
            'method': method
        }

    return outliers_dict


def analyze_orbit_parameters(df: pd.DataFrame) -> Dict[str, Any]:
    """
    轨道参数分析

    Args:
        df: 包含轨道参数的DataFrame

    Returns:
        dict: 包含轨道参数的分析结果
    """
    if df.empty:
        return {}

    orbit_params = ['a', 'e', 'i', 'raan', 'argp', 'mean_anomaly']
    analysis_dict = {}

    for param in orbit_params:
        if param in df.columns:
            data = df[param].dropna()
            if len(data) > 0:
                analysis_dict[param] = {
                    'mean': float(data.mean()),
                    'std': float(data.std()),
                    'min': float(data.min()),
                    'max': float(data.max()),
                    'range': float(data.max() - data.min()),
                    'stability': '稳定' if data.std() / data.mean() < 0.01 else '不稳定'
                }

    # 轨道稳定性分析
    if 'a' in df.columns:
        a_data = df['a'].dropna()
        if len(a_data) > 1:
            # 计算轨道高度变化率
            if 'timestamp' in df.columns:
                time_diff = df['timestamp'].diff().dt.total_seconds().dropna()
                a_diff = a_data.diff().dropna()

                if len(time_diff) > 0 and len(a_diff) > 0:
                    # 确保长度一致
                    min_len = min(len(time_diff), len(a_diff))
                    if min_len > 0:
                        altitude_change_rate = a_diff.iloc[:min_len] / time_diff.iloc[:min_len]
                        analysis_dict['orbit_stability'] = {
                            'mean_altitude_change_rate': float(altitude_change_rate.mean()),
                            'max_altitude_change_rate': float(altitude_change_rate.max()),
                            'min_altitude_change_rate': float(altitude_change_rate.min()),
                            'stability_assessment': '稳定' if abs(altitude_change_rate.mean()) < 0.1 else '不稳定'
                        }

    # 轨道周期分析
    if 'a' in df.columns and 'altitude' not in df.columns:
        # 如果还没有计算轨道周期，这里计算
        earth_radius = 6371  # km
        df_copy = df.copy()
        df_copy['altitude'] = df_copy['a'] - earth_radius

        # 开普勒第三定律计算轨道周期
        G = 6.67430e-20  # 引力常数（km^3/kg/s^2）
        M_earth = 5.972e24  # 地球质量（kg）
        df_copy['orbit_period'] = 2 * np.pi * np.sqrt(df_copy['a']**3 / (G * M_earth))

        if 'orbit_period' in df_copy.columns:
            period_data = df_copy['orbit_period'].dropna()
            if len(period_data) > 0:
                analysis_dict['orbit_period'] = {
                    'mean': float(period_data.mean()),
                    'std': float(period_data.std()),
                    'min': float(period_data.min()),
                    'max': float(period_data.max()),
                    'mean_minutes': float(period_data.mean() / 60),
                    'mean_hours': float(period_data.mean() / 3600)
                }

    # 轨道参数相关性分析
    orbit_data = {}
    for param in orbit_params:
        if param in df.columns:
            orbit_data[param] = df[param]

    if len(orbit_data) >= 2:
        orbit_df = pd.DataFrame(orbit_data)
        orbit_corr = orbit_df.corr()

        analysis_dict['parameter_correlations'] = {
            'correlation_matrix': orbit_corr.to_dict(),
            'strong_correlations': []
        }

        # 找出强相关性
        for i in range(len(orbit_params)):
            for j in range(i+1, len(orbit_params)):
                param1 = orbit_params[i]
                param2 = orbit_params[j]
                if param1 in orbit_corr.columns and param2 in orbit_corr.columns:
                    corr = orbit_corr.loc[param1, param2]
                    if abs(corr) > 0.8:
                        analysis_dict['parameter_correlations']['strong_correlations'].append({
                            'param1': param1,
                            'param2': param2,
                            'correlation': float(corr),
                            'relationship': '强相关' if corr > 0 else '强负相关'
                        })

    return analysis_dict


def format_statistics_for_report(statistics: Dict[str, Any]) -> str:
    """
    格式化统计信息用于报告
    Args:
        statistics: 统计信息字典
    Returns:
        str: 格式化的报告字符串
    """
    if not statistics:
        return "无统计信息可用"

    lines = ["=" * 60,
             "数据分析报告",
             "=" * 60]

    # 基本统计信息
    if any(key not in ['correlations', 'orbit_stability', 'parameter_correlations'] for key in statistics.keys()):
        lines.append("\n基本统计信息:")
        lines.append("-" * 40)

        for param, stats in statistics.items():
            if param in ['correlations', 'time_intervals', 'orbit_stability', 'parameter_correlations']:
                continue

            lines.append(f"\n{param.upper()}:")
            lines.append(f"  样本数: {stats.get('count', 'N/A')}")
            lines.append(f"  均值: {stats.get('mean', 'N/A'):.4f}")
            lines.append(f"  标准差: {stats.get('std', 'N/A'):.4f}")
            lines.append(f"  最小值: {stats.get('min', 'N/A'):.4f}")
            lines.append(f"  最大值: {stats.get('max', 'N/A'):.4f}")
            lines.append(f"  范围: {stats.get('range', 'N/A'):.4f}")

    return "\n".join(lines)