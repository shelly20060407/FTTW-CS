"""
plot_static.py - 静态图表可视化模块
功能：
1. 绘制温度变化曲线
2. 绘制电池电压变化曲线
3. 绘制轨道参数变化图
4. 绘制统计图表
5. 保存图表到文件
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec

# 设置中文显示和图表样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-darkgrid')


def plot_temperature(df: pd.DataFrame,
                     thresholds: Optional[Dict[str, float]] = None,
                     figsize: Tuple[int, int] = (12, 6),
                     save_path: Optional[str] = None) -> plt.Figure:
    """
    绘制温度变化曲线

    Args:
        df: 包含温度数据的DataFrame
        thresholds: 温度阈值字典，包含 'high' 和 'low' 键
        figsize: 图表大小
        save_path: 保存路径，如果提供则保存图表

    Returns:
        plt.Figure: 图表对象
    """
    if df.empty or 'temperature' not in df.columns:
        print("警告: 数据为空或没有温度列")
        return None

    fig, ax = plt.subplots(figsize=figsize)

    # 确保数据按时间排序
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')
        x = df['timestamp']
        x_label = '时间'
    else:
        x = range(len(df))
        x_label = '数据点序号'

    # 绘制温度曲线
    ax.plot(x, df['temperature'],
            color='#FF6B6B', linewidth=2,
            marker='o', markersize=4,
            label='温度 (°C)')

    # 绘制阈值线（如果提供了阈值）
    if thresholds:
        if 'high' in thresholds:
            ax.axhline(y=thresholds['high'], color='red',
                       linestyle='--', linewidth=2,
                       label=f'高温阈值: {thresholds["high"]}°C', alpha=0.7)

        if 'low' in thresholds:
            ax.axhline(y=thresholds['low'], color='blue',
                       linestyle='--', linewidth=2,
                       label=f'低温阈值: {thresholds["low"]}°C', alpha=0.7)

    # 设置图表属性
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel('温度 (°C)', fontsize=12)
    ax.set_title('卫星温度变化曲线', fontsize=16, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # 设置x轴格式（如果是时间序列）
    if 'timestamp' in df.columns:
        fig.autofmt_xdate()

    # 添加统计信息文本框
    temp_stats = df['temperature'].describe()
    stats_text = (f"平均值: {temp_stats['mean']:.2f}°C\n"
                  f"最大值: {temp_stats['max']:.2f}°C\n"
                  f"最小值: {temp_stats['min']:.2f}°C\n"
                  f"标准差: {temp_stats['std']:.2f}°C")

    # 将文本框放在右上角
    ax.text(0.98, 0.98, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=10)

    plt.tight_layout()

    # 保存图表
    if save_path:
        save_plots_to_file(fig, save_path)

    return fig


def plot_voltage(df: pd.DataFrame,
                 thresholds: Optional[Dict[str, float]] = None,
                 figsize: Tuple[int, int] = (12, 6),
                 save_path: Optional[str] = None) -> plt.Figure:
    """
    绘制电压变化曲线

    Args:
        df: 包含电压数据的DataFrame
        thresholds: 电压阈值字典
        figsize: 图表大小
        save_path: 保存路径

    Returns:
        plt.Figure: 图表对象
    """
    if df.empty or 'battery_voltage' not in df.columns:
        print("警告: 数据为空或没有电压列")
        return None

    fig, ax = plt.subplots(figsize=figsize)

    # 确保数据按时间排序
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')
        x = df['timestamp']
        x_label = '时间'
    else:
        x = range(len(df))
        x_label = '数据点序号'

    # 绘制电压曲线
    ax.plot(x, df['battery_voltage'],
            color='#4ECDC4', linewidth=2,
            marker='s', markersize=4,
            label='电池电压 (V)')

    # 绘制阈值线
    if thresholds:
        if 'high' in thresholds:
            ax.axhline(y=thresholds['high'], color='red',
                       linestyle='--', linewidth=2,
                       label=f'高压阈值: {thresholds["high"]}V', alpha=0.7)

        if 'low' in thresholds:
            ax.axhline(y=thresholds['low'], color='blue',
                       linestyle='--', linewidth=2,
                       label=f'低压阈值: {thresholds["low"]}V', alpha=0.7)

    # 设置图表属性
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel('电池电压 (V)', fontsize=12)
    ax.set_title('卫星电池电压变化曲线', fontsize=16, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # 设置x轴格式
    if 'timestamp' in df.columns:
        fig.autofmt_xdate()

    # 添加统计信息文本框
    voltage_stats = df['battery_voltage'].describe()
    stats_text = (f"平均值: {voltage_stats['mean']:.2f}V\n"
                  f"最大值: {voltage_stats['max']:.2f}V\n"
                  f"最小值: {voltage_stats['min']:.2f}V\n"
                  f"标准差: {voltage_stats['std']:.2f}V")

    ax.text(0.98, 0.98, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
            fontsize=10)

    plt.tight_layout()

    # 保存图表
    if save_path:
        save_plots_to_file(fig, save_path)

    return fig


def plot_orbit_parameters(df: pd.DataFrame,
                          figsize: Tuple[int, int] = (16, 12),
                          save_path: Optional[str] = None) -> plt.Figure:
    """
    绘制轨道参数图

    Args:
        df: 包含轨道参数的DataFrame
        figsize: 图表大小
        save_path: 保存路径

    Returns:
        plt.Figure: 图表对象
    """
    # 定义轨道参数及其单位
    orbit_params = [
        ('a', '半长轴 (km)', 'a', '半长轴'),
        ('e', '偏心率', 'e', '偏心率'),
        ('i', '轨道倾角 (°)', 'i', '轨道倾角'),
        ('raan', '升交点赤经 (°)', 'Ω', '升交点赤经'),
        ('argp', '近地点幅角 (°)', 'ω', '近地点幅角'),
        ('mean_anomaly', '平近点角 (°)', 'M', '平近点角')
    ]

    # 检查哪些参数存在
    available_params = [(name, ylabel, symbol, title) for name, ylabel, symbol, title in orbit_params
                        if name in df.columns]

    if not available_params:
        print("警告: 没有找到轨道参数数据")
        return None

    # 创建子图网格
    n_params = len(available_params)
    n_cols = min(3, n_params)
    n_rows = (n_params + n_cols - 1) // n_cols

    fig = plt.figure(figsize=figsize)

    # 设置整体标题
    fig.suptitle('卫星轨道六根数变化图', fontsize=20, fontweight='bold', y=1.02)

    # 颜色列表
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

    for idx, (param_name, ylabel, symbol, title) in enumerate(available_params):
        ax = plt.subplot(n_rows, n_cols, idx + 1)

        # 确保数据按时间排序
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            x = df_sorted['timestamp']
        else:
            x = range(len(df))

        # 绘制轨道参数曲线
        color_idx = idx % len(colors)
        ax.plot(x, df[param_name],
                color=colors[color_idx], linewidth=1.5,
                marker='.', markersize=2,
                label=f'{symbol} = {title}')

        # 设置子图属性
        ax.set_title(f'{title} ({symbol})', fontsize=12, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=10)

        if idx >= n_params - n_cols:  # 最后一行显示x轴标签
            if 'timestamp' in df.columns:
                ax.set_xlabel('时间', fontsize=10)
                # 旋转x轴标签避免重叠
                for label in ax.get_xticklabels():
                    label.set_rotation(45)
                    label.set_fontsize(8)
            else:
                ax.set_xlabel('数据点序号', fontsize=10)

        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=8)

        # 添加统计信息
        param_data = df[param_name].dropna()
        if len(param_data) > 0:
            mean_val = param_data.mean()
            std_val = param_data.std()

            # 在子图左上角添加统计信息
            ax.text(0.02, 0.98,
                    f'均值: {mean_val:.4f}\n标准差: {std_val:.4f}',
                    transform=ax.transAxes,
                    verticalalignment='top',
                    fontsize=8,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    plt.tight_layout()

    # 保存图表
    if save_path:
        save_plots_to_file(fig, save_path)

    return fig


def plot_statistics(df: pd.DataFrame,
                    figsize: Tuple[int, int] = (16, 10),
                    save_path: Optional[str] = None) -> plt.Figure:
    """
    绘制统计图表

    Args:
        df: 包含数据的DataFrame
        figsize: 图表大小
        save_path: 保存路径

    Returns:
        plt.Figure: 图表对象
    """
    if df.empty:
        print("警告: 数据为空")
        return None

    # 选择要绘制的数值列
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # 移除可能不需要的列
    exclude_cols = ['hour', 'minute', 'day_of_week', 'is_night']
    plot_cols = [col for col in numeric_cols if col not in exclude_cols]

    # 限制最多绘制6个参数
    if len(plot_cols) > 6:
        # 优先选择温度、电压和轨道参数
        priority_cols = ['temperature', 'battery_voltage', 'a', 'e', 'i']
        plot_cols = [col for col in priority_cols if col in plot_cols]
        plot_cols = plot_cols[:6]

    if not plot_cols:
        print("警告: 没有可绘制的数值列")
        return None

    # 创建图表
    fig = plt.figure(figsize=figsize)
    fig.suptitle('卫星遥测数据统计图表', fontsize=20, fontweight='bold', y=1.02)

    # 创建2行3列的子图网格
    gs = gridspec.GridSpec(2, 3, height_ratios=[2, 1])

    # 第一行：直方图
    for idx, col in enumerate(plot_cols[:3]):
        ax = plt.subplot(gs[0, idx])

        # 绘制直方图
        data = df[col].dropna()
        if len(data) > 0:
            ax.hist(data, bins=30, color='#4ECDC4', alpha=0.7, edgecolor='black')
            ax.set_title(f'{col} 分布直方图', fontsize=12, fontweight='bold')
            ax.set_xlabel(col, fontsize=10)
            ax.set_ylabel('频数', fontsize=10)
            ax.grid(True, alpha=0.3)

            # 添加统计信息
            stats_text = (f'样本数: {len(data)}\n'
                          f'均值: {data.mean():.4f}\n'
                          f'标准差: {data.std():.4f}')

            ax.text(0.02, 0.98, stats_text,
                    transform=ax.transAxes,
                    verticalalignment='top',
                    fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # 第二行：箱线图和散点图
    if len(plot_cols) > 3:
        # 箱线图
        ax_box = plt.subplot(gs[1, 0])
        box_data = [df[col].dropna() for col in plot_cols[:min(6, len(plot_cols))]]
        box_labels = plot_cols[:min(6, len(plot_cols))]

        bp = ax_box.boxplot(box_data, labels=box_labels, patch_artist=True)

        # 设置箱线图颜色
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        for patch, color in zip(bp['boxes'], colors[:len(box_data)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax_box.set_title('参数箱线图', fontsize=12, fontweight='bold')
        ax_box.set_ylabel('数值', fontsize=10)
        ax_box.grid(True, alpha=0.3)

        # 散点图（温度 vs 电压）
        if 'temperature' in df.columns and 'battery_voltage' in df.columns:
            ax_scatter = plt.subplot(gs[1, 1])

            temp_data = df['temperature'].dropna()
            voltage_data = df['battery_voltage'].dropna()

            # 确保数据长度一致
            min_len = min(len(temp_data), len(voltage_data))
            if min_len > 0:
                ax_scatter.scatter(temp_data[:min_len], voltage_data[:min_len],
                                   c='#FF6B6B', alpha=0.6, s=30)

                ax_scatter.set_xlabel('温度 (°C)', fontsize=10)
                ax_scatter.set_ylabel('电池电压 (V)', fontsize=10)
                ax_scatter.set_title('温度-电压散点图', fontsize=12, fontweight='bold')
                ax_scatter.grid(True, alpha=0.3)

        # 时间序列子图（如果有时间戳）
        if 'timestamp' in df.columns and len(plot_cols) >= 3:
            ax_ts = plt.subplot(gs[1, 2])

            # 绘制前3个参数的时间序列
            for i, col in enumerate(plot_cols[:3]):
                df_sorted = df.sort_values('timestamp')
                ax_ts.plot(df_sorted['timestamp'], df_sorted[col],
                           label=col, linewidth=1, alpha=0.7)

            ax_ts.set_xlabel('时间', fontsize=10)
            ax_ts.set_ylabel('数值', fontsize=10)
            ax_ts.set_title('多参数时间序列', fontsize=12, fontweight='bold')
            ax_ts.legend(loc='upper right', fontsize=8)
            ax_ts.grid(True, alpha=0.3)

            # 旋转x轴标签
            for label in ax_ts.get_xticklabels():
                label.set_rotation(45)
                label.set_fontsize(8)

    plt.tight_layout()

    # 保存图表
    if save_path:
        save_plots_to_file(fig, save_path)

    return fig


def save_plots_to_file(fig: plt.Figure,
                       filename: str,
                       dpi: int = 300,
                       formats: List[str] = None) -> Dict[str, str]:
    """
    保存图表到文件

    Args:
        fig: matplotlib图表对象
        filename: 文件名（可以包含路径）
        dpi: 图像分辨率
        formats: 保存格式列表，默认为 ['png', 'pdf']

    Returns:
        dict: 保存的文件路径字典
    """
    if formats is None:
        formats = ['png', 'pdf']

    saved_files = {}

    # 确保目录存在
    file_path = Path(filename)
    file_dir = file_path.parent
    file_dir.mkdir(parents=True, exist_ok=True)

    # 提取基础文件名（不带扩展名）
    base_name = file_path.stem

    for fmt in formats:
        save_path = file_dir / f"{base_name}.{fmt}"

        try:
            fig.savefig(save_path,
                        format=fmt,
                        dpi=dpi,
                        bbox_inches='tight',
                        facecolor='white',  # 确保背景为白色
                        edgecolor='none')

            saved_files[fmt] = str(save_path)
            print(f"图表已保存为 {fmt} 格式: {save_path}")

        except Exception as e:
            print(f"保存 {fmt} 格式失败: {e}")

    return saved_files


def plot_all(df: pd.DataFrame,
             output_dir: str = "data/processed/plots",
             thresholds: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, str]:
    """
    绘制所有图表

    Args:
        df: 包含数据的DataFrame
        output_dir: 输出目录
        thresholds: 阈值配置字典

    Returns:
        dict: 保存的文件路径字典
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    # 获取温度阈值
    temp_thresholds = None
    if thresholds and 'temperature' in thresholds:
        temp_thresholds = thresholds['temperature']

    # 获取电压阈值
    voltage_thresholds = None
    if thresholds and 'battery_voltage' in thresholds:
        voltage_thresholds = thresholds['battery_voltage']

    print("开始生成静态图表...")

    try:
        # 1. 温度图表
        print("生成温度图表...")
        fig_temp = plot_temperature(df, temp_thresholds)
        if fig_temp:
            temp_files = save_plots_to_file(fig_temp, output_path / "temperature_plot")
            saved_files['temperature'] = temp_files
            plt.close(fig_temp)

    except Exception as e:
        print(f"生成温度图表失败: {e}")

    try:
        # 2. 电压图表
        print("生成电压图表...")
        fig_voltage = plot_voltage(df, voltage_thresholds)
        if fig_voltage:
            voltage_files = save_plots_to_file(fig_voltage, output_path / "voltage_plot")
            saved_files['voltage'] = voltage_files
            plt.close(fig_voltage)

    except Exception as e:
        print(f"生成电压图表失败: {e}")

    try:
        # 3. 轨道参数图表
        print("生成轨道参数图表...")
        fig_orbit = plot_orbit_parameters(df)
        if fig_orbit:
            orbit_files = save_plots_to_file(fig_orbit, output_path / "orbit_parameters")
            saved_files['orbit'] = orbit_files
            plt.close(fig_orbit)

    except Exception as e:
        print(f"生成轨道参数图表失败: {e}")

    try:
        # 4. 统计图表
        print("生成统计图表...")
        fig_stats = plot_statistics(df)
        if fig_stats:
            stats_files = save_plots_to_file(fig_stats, output_path / "statistics")
            saved_files['statistics'] = stats_files
            plt.close(fig_stats)

    except Exception as e:
        print(f"生成统计图表失败: {e}")

    print("图表生成完成!")
    return saved_files