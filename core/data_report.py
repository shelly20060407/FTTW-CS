"""
data_report.py - 数据报告生成模块
功能：
1. 生成周期性的数据报告
2. 生成汇总报告
3. 保存报告到不同格式的文件
4. 格式化统计信息
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Union, List
import json
import csv

# 导入其他模块的函数
try:
    from core.data_analysis import calculate_statistics, fit_temperature_trend, detect_outliers, \
        analyze_orbit_parameters
except ImportError:
    # 如果导入失败，提供空函数占位
    def calculate_statistics(df):
        return {}


    def fit_temperature_trend(df):
        return {}


    def detect_outliers(df):
        return {}


    def analyze_orbit_parameters(df):
        return {}


def generate_cycle_report(df: pd.DataFrame,
                          cycle_size: int = 10,
                          include_stats: bool = True,
                          include_alarms: bool = True) -> List[Dict[str, Any]]:
    """
    生成周期报告

    Args:
        df: 原始数据DataFrame
        cycle_size: 每个周期的数据条数
        include_stats: 是否包含统计信息
        include_alarms: 是否包含报警信息（需要data_checker模块）

    Returns:
        list: 每个周期的报告字典列表
    """
    if df.empty:
        return []

    # 确保数据按时间排序
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp').reset_index(drop=True)

    cycle_reports = []
    total_cycles = (len(df) + cycle_size - 1) // cycle_size

    for cycle_num in range(total_cycles):
        start_idx = cycle_num * cycle_size
        end_idx = min((cycle_num + 1) * cycle_size, len(df))

        cycle_df = df.iloc[start_idx:end_idx]

        if cycle_df.empty:
            continue

        # 创建周期报告
        report = {
            'cycle_number': cycle_num + 1,
            'data_range': f"{start_idx + 1}-{end_idx}",
            'total_records': len(cycle_df),
            'timestamp_range': {},
            'statistics': {},
            'warnings': [],
            'summary': ''
        }

        # 时间范围
        if 'timestamp' in cycle_df.columns:
            timestamps = cycle_df['timestamp'].dropna()
            if not timestamps.empty:
                report['timestamp_range'] = {
                    'start': timestamps.min().strftime('%Y-%m-%d %H:%M:%S'),
                    'end': timestamps.max().strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_seconds': (timestamps.max() - timestamps.min()).total_seconds()
                }

        # 统计信息
        if include_stats:
            stats = calculate_statistics(cycle_df)
            report['statistics'] = stats

            # 提取关键统计指标
            key_metrics = {}
            for param in ['temperature', 'battery_voltage', 'a', 'e', 'i']:
                if param in stats:
                    key_metrics[param] = {
                        'mean': stats[param].get('mean', 0),
                        'min': stats[param].get('min', 0),
                        'max': stats[param].get('max', 0),
                        'std': stats[param].get('std', 0)
                    }

            report['key_metrics'] = key_metrics

        # 报警信息（如果有data_checker模块）
        if include_alarms:
            try:
                from core.data_checker import check_all_thresholds
                alarms = check_all_thresholds(cycle_df)
                report['alarm_count'] = len(alarms)
                report['alarms'] = alarms[:5]  # 只保留前5个报警
            except ImportError:
                report['alarm_count'] = 0
                report['alarms'] = []

        # 温度趋势分析
        if 'temperature' in cycle_df.columns and len(cycle_df) > 3:
            trend = fit_temperature_trend(cycle_df)
            if trend:
                report['temperature_trend'] = {
                    'direction': trend.get('trend', '未知'),
                    'slope': trend.get('slope', 0),
                    'r_squared': trend.get('r_squared', 0)
                }

        # 异常值检测
        outliers = detect_outliers(cycle_df, method='iqr')
        if outliers:
            report['outlier_count'] = outliers.get('summary', {}).get('total_outliers', 0)

        # 生成总结文本
        summary_lines = []
        summary_lines.append(f"周期 {cycle_num + 1} 报告:")
        summary_lines.append(f"数据范围: 第 {start_idx + 1} 到 {end_idx} 条")

        if report['timestamp_range']:
            summary_lines.append(
                f"时间范围: {report['timestamp_range']['start']} 到 {report['timestamp_range']['end']}")

        if 'key_metrics' in report:
            for param, metrics in report['key_metrics'].items():
                if param == 'temperature':
                    summary_lines.append(
                        f"平均温度: {metrics['mean']:.2f}°C (范围: {metrics['min']:.1f}-{metrics['max']:.1f}°C)")
                elif param == 'battery_voltage':
                    summary_lines.append(
                        f"平均电压: {metrics['mean']:.2f}V (范围: {metrics['min']:.2f}-{metrics['max']:.2f}V)")

        if 'temperature_trend' in report:
            trend_dir = report['temperature_trend']['direction']
            summary_lines.append(f"温度趋势: {trend_dir}")

        if 'alarm_count' in report:
            summary_lines.append(f"报警数量: {report['alarm_count']}")

        if 'outlier_count' in report:
            summary_lines.append(f"异常值数量: {report['outlier_count']}")

        report['summary'] = '\n'.join(summary_lines)

        cycle_reports.append(report)

    return cycle_reports


def create_summary_report(df: pd.DataFrame,
                          cycle_reports: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    创建汇总报告

    Args:
        df: 原始数据DataFrame
        cycle_reports: 可选的周期报告列表，如果为None则自动生成

    Returns:
        dict: 汇总报告字典
    """
    if df.empty:
        return {"error": "没有可用的数据生成报告"}

    from datetime import datetime
    import numpy as np

    # 记录报告生成状态和时间
    report_status = {
        "generated_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "status": "success",
        "data_records": len(df)
    }

    # 获取时间范围
    time_range = {}
    if 'timestamp' in df.columns:
        try:
            timestamps = df['timestamp'].dropna()
            if not timestamps.empty:
                start_time = timestamps.min()
                end_time = timestamps.max()
                duration_hours = (end_time - start_time).total_seconds() / 3600

                time_range = {
                    'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_hours': round(duration_hours, 2)
                }
        except Exception as e:
            print(f"时间范围计算失败: {e}")

    # 如果需要，先生成周期报告
    if cycle_reports is None:
        try:
            cycle_reports = generate_cycle_report(df, cycle_size=min(20, len(df) // 5 or 10))
            report_status["cycle_reports_generated"] = len(cycle_reports)
        except Exception as e:
            print(f"生成周期报告失败: {e}")
            cycle_reports = []

    # 基本统计信息
    stats = {}
    try:
        stats = calculate_statistics(df)
        report_status["statistics_calculated"] = True
    except Exception as e:
        print(f"计算统计信息失败: {e}")

    # 温度趋势分析
    temp_trend = {}
    if 'temperature' in df.columns:
        try:
            temp_trend = fit_temperature_trend(df)
            report_status["trend_analysis_done"] = True
        except Exception as e:
            print(f"温度趋势分析失败: {e}")

    # 异常值检测
    outliers = {}
    try:
        outliers = detect_outliers(df, method='iqr')
        report_status["outliers_detected"] = True
    except Exception as e:
        print(f"异常值检测失败: {e}")

    # 轨道参数分析
    orbit_analysis = {}
    try:
        orbit_analysis = analyze_orbit_parameters(df)
        report_status["orbit_analysis_done"] = True
    except Exception as e:
        print(f"轨道参数分析失败: {e}")

    # 报警信息
    alarms = []
    alarm_count = 0
    try:
        from core.data_checker import check_all_thresholds
        alarms = check_all_thresholds(df)
        alarm_count = len(alarms)
        report_status["alarms_checked"] = True
        report_status["total_alarms"] = alarm_count
    except ImportError:
        print("core.data_checker模块未找到，跳过报警检查")
    except Exception as e:
        print(f"报警检查失败: {e}")

    # 构建汇总报告
    summary = {
        'report_metadata': report_status,
        'report_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_overview': {
            'total_records': len(df),
            'data_columns': list(df.columns),
            'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
            'time_range': time_range
        },
        'statistics_summary': {},
        'trends_analysis': {},
        'anomalies_summary': {},
        'orbit_analysis_summary': {},
        'alarms_summary': {},
        'cycle_reports_summary': {},
        'recommendations': []
    }

    # 统计摘要
    key_params = ['temperature', 'battery_voltage', 'a', 'e', 'i']
    for param in key_params:
        if param in stats:
            try:
                std = stats[param].get('std', 0)
                mean = stats[param].get('mean', 1)
                stability_threshold = std / (abs(mean) if mean != 0 else 1)

                summary['statistics_summary'][param] = {
                    'mean': stats[param].get('mean'),
                    'min': stats[param].get('min'),
                    'max': stats[param].get('max'),
                    'std': stats[param].get('std'),
                    'stability': '稳定' if stability_threshold < 0.1 else '不稳定'
                }
            except Exception as e:
                print(f"统计参数 {param} 处理失败: {e}")

    # 趋势分析
    if temp_trend:
        try:
            summary['trends_analysis']['temperature'] = {
                'direction': temp_trend.get('trend', '未知'),
                'slope': temp_trend.get('slope', 0),
                'r_squared': temp_trend.get('r_squared', 0),
                'current_value': temp_trend.get('current_temperature')
            }
        except Exception as e:
            print(f"趋势分析处理失败: {e}")

    # 异常值摘要
    if outliers and 'summary' in outliers:
        try:
            summary['anomalies_summary'] = {
                'total_outliers': outliers['summary'].get('total_outliers', 0),
                'columns_with_outliers': outliers['summary'].get('columns_with_outliers', [])
            }
        except Exception as e:
            print(f"异常值摘要处理失败: {e}")

    # 轨道分析摘要
    if orbit_analysis:
        try:
            summary['orbit_analysis_summary'] = {
                'parameters_analyzed': list(orbit_analysis.keys()),
                'stability': orbit_analysis.get('orbit_stability', {}).get('stability_assessment', '未知')
            }
        except Exception as e:
            print(f"轨道分析摘要处理失败: {e}")

    # 报警摘要
    alarms_by_type = {}
    if alarms:
        try:
            for alarm in alarms:
                alarm_type = alarm.get('type', 'unknown')
                alarms_by_type[alarm_type] = alarms_by_type.get(alarm_type, 0) + 1
        except Exception as e:
            print(f"报警类型统计失败: {e}")

    summary['alarms_summary'] = {
        'total_alarms': alarm_count,
        'alarms_by_type': alarms_by_type
    }

    # 周期报告摘要
    if cycle_reports:
        try:
            total_cycle_records = sum(r.get('total_records', 0) for r in cycle_reports)
            cycles_with_alarms = sum(1 for r in cycle_reports if r.get('alarm_count', 0) > 0)

            summary['cycle_reports_summary'] = {
                'total_cycles': len(cycle_reports),
                'average_records_per_cycle': total_cycle_records / len(cycle_reports) if cycle_reports else 0,
                'cycles_with_alarms': cycles_with_alarms
            }
        except Exception as e:
            print(f"周期报告摘要处理失败: {e}")

    # 生成建议
    recommendations = []
    try:
        # 报警数量建议
        if alarm_count > len(df) * 0.1:  # 如果报警超过数据量的10%
            recommendations.append("🚨 报警数量较多，建议检查传感器或调整阈值")

        # 温度建议
        if 'temperature' in summary['statistics_summary']:
            temp_std = summary['statistics_summary']['temperature'].get('std', 0)
            if temp_std > 5:
                recommendations.append("🌡️ 温度波动较大，建议检查温控系统")

        # 电压建议
        if 'battery_voltage' in summary['statistics_summary']:
            voltage_min = summary['statistics_summary']['battery_voltage'].get('min', 8)
            if voltage_min < 7.2:
                recommendations.append("🔋 电池电压过低，建议检查电源系统")

        # 轨道稳定性建议
        if summary.get('orbit_analysis_summary', {}).get('stability') == '不稳定':
            recommendations.append("🛰️ 轨道参数不稳定，建议进行轨道修正")

        # 异常值建议
        if summary.get('anomalies_summary', {}).get('total_outliers', 0) > 10:
            recommendations.append("⚠️ 检测到较多异常值，建议检查数据质量")

        summary['recommendations'] = recommendations

    except Exception as e:
        print(f"生成建议失败: {e}")
        summary['recommendations'] = ["无法生成详细建议"]

    return summary


def save_report_to_file(report: Union[Dict[str, Any], List[Dict[str, Any]], str],
                        file_path: str,
                        format: str = 'txt',
                        encoding: str = 'utf-8') -> bool:
    """
    保存报告到文件

    Args:
        report: 报告内容，可以是字典、列表或字符串
        file_path: 文件路径
        format: 文件格式，支持 'txt', 'json', 'csv'
        encoding: 文件编码

    Returns:
        bool: 保存是否成功
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'txt':
            # 如果是字典或列表，转换为字符串
            if isinstance(report, (dict, list)):
                report_text = _format_report_to_text(report)
            else:
                report_text = str(report)

            with open(file_path, 'w', encoding=encoding) as f:
                f.write(report_text)

        elif format == 'json':
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        elif format == 'csv':
            if isinstance(report, dict):
                # 将字典展平为适合CSV的格式
                flattened = _flatten_dict(report)
                with open(file_path, 'w', newline='', encoding=encoding) as f:
                    writer = csv.writer(f)
                    for key, value in flattened.items():
                        writer.writerow([key, value])
            elif isinstance(report, list) and all(isinstance(r, dict) for r in report):
                # 如果报告是字典列表，保存为表格格式
                with open(file_path, 'w', newline='', encoding=encoding) as f:
                    if report:
                        fieldnames = report[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(report)
            else:
                raise ValueError("CSV格式需要字典或字典列表格式的报告")
        else:
            raise ValueError(f"不支持的格式: {format}")

        print(f"报告已保存到: {file_path} ({format.upper()}格式)")
        return True

    except Exception as e:
        print(f"保存报告失败: {e}")
        return False


def _format_report_to_text(report: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    """
    将报告格式化为文本

    Args:
        report: 报告内容

    Returns:
        str: 格式化后的文本
    """
    if isinstance(report, list):
        # 处理周期报告列表
        lines = ["=" * 70]
        lines.append("卫星遥测数据周期报告")
        lines.append("=" * 70)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"周期总数: {len(report)}")
        lines.append("=" * 70)

        for i, cycle_report in enumerate(report):
            lines.append(f"\n周期 {i + 1}:")
            lines.append("-" * 40)

            if 'summary' in cycle_report:
                lines.append(cycle_report['summary'])
            else:
                # 如果没有summary，手动生成
                lines.append(f"数据范围: {cycle_report.get('data_range', '未知')}")
                lines.append(f"记录数: {cycle_report.get('total_records', 0)}")

                if 'timestamp_range' in cycle_report:
                    tr = cycle_report['timestamp_range']
                    lines.append(f"时间: {tr.get('start', '未知')} 到 {tr.get('end', '未知')}")

                if 'alarm_count' in cycle_report:
                    lines.append(f"报警数: {cycle_report['alarm_count']}")

        return "\n".join(lines)

    elif isinstance(report, dict):
        # 处理汇总报告字典
        lines = ["=" * 70]
        lines.append("卫星遥测数据汇总报告")
        lines.append("=" * 70)
        lines.append(f"生成时间: {report.get('report_generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}")
        lines.append("=" * 70)

        # 数据概览
        lines.append("\n1. 数据概览")
        lines.append("-" * 40)
        overview = report.get('data_overview', {})
        lines.append(f"总记录数: {overview.get('total_records', 0)}")
        lines.append(f"数据列数: {len(overview.get('data_columns', []))}")

        time_range = overview.get('time_range', {})
        if time_range:
            lines.append(f"时间范围: {time_range.get('start', '未知')} 到 {time_range.get('end', '未知')}")
            lines.append(f"持续时间: {time_range.get('duration_hours', 0):.2f} 小时")

        # 统计摘要
        stats = report.get('statistics_summary', {})
        if stats:
            lines.append("\n2. 关键参数统计")
            lines.append("-" * 40)
            for param, values in stats.items():
                if param == 'temperature':
                    lines.append(
                        f"温度: 均值{values.get('mean', 0):.2f}°C, 范围[{values.get('min', 0):.1f}-{values.get('max', 0):.1f}°C], 稳定性: {values.get('stability', '未知')}")
                elif param == 'battery_voltage':
                    lines.append(
                        f"电压: 均值{values.get('mean', 0):.2f}V, 范围[{values.get('min', 0):.2f}-{values.get('max', 0):.2f}V], 稳定性: {values.get('stability', '未知')}")

        # 趋势分析
        trends = report.get('trends_analysis', {})
        if trends:
            lines.append("\n3. 趋势分析")
            lines.append("-" * 40)
            for param, trend in trends.items():
                lines.append(f"{param}: 趋势{trend.get('direction', '未知')}, R²={trend.get('r_squared', 0):.3f}")

        # 报警摘要
        alarms = report.get('alarms_summary', {})
        if alarms:
            lines.append("\n4. 报警摘要")
            lines.append("-" * 40)
            lines.append(f"总报警数: {alarms.get('total_alarms', 0)}")
            alarms_by_type = alarms.get('alarms_by_type', {})
            for alarm_type, count in alarms_by_type.items():
                lines.append(f"  {alarm_type}报警: {count}个")

        # 异常值摘要
        anomalies = report.get('anomalies_summary', {})
        if anomalies:
            lines.append("\n5. 异常值检测")
            lines.append("-" * 40)
            lines.append(f"总异常值: {anomalies.get('total_outliers', 0)}")

        # 轨道分析
        orbit = report.get('orbit_analysis_summary', {})
        if orbit:
            lines.append("\n6. 轨道分析")
            lines.append("-" * 40)
            lines.append(f"轨道稳定性: {orbit.get('stability', '未知')}")

        # 建议
        recommendations = report.get('recommendations', [])
        if recommendations:
            lines.append("\n7. 建议")
            lines.append("-" * 40)
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    else:
        return str(report)


def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    展平嵌套字典

    Args:
        d: 嵌套字典
        parent_key: 父键名
        sep: 分隔符

    Returns:
        dict: 展平后的字典
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(_flatten_dict(v, new_key, sep=sep))
        elif isinstance(v, list):
            # 处理列表，转换为字符串
            items[new_key] = str(v)
        else:
            items[new_key] = v
    return items


def format_statistics(stats: Dict[str, Any],
                      format_type: str = 'text') -> str:
    """
    格式化统计信息

    Args:
        stats: 统计信息字典
        format_type: 格式类型，支持 'text', 'markdown', 'html'

    Returns:
        str: 格式化后的统计信息
    """
    if not stats:
        return "无统计信息"

    if format_type == 'text':
        return _format_stats_to_text(stats)
    elif format_type == 'markdown':
        return _format_stats_to_markdown(stats)
    elif format_type == 'html':
        return _format_stats_to_html(stats)
    else:
        return _format_stats_to_text(stats)


def _format_stats_to_text(stats: Dict[str, Any]) -> str:
    """格式化为纯文本"""
    lines = ["统计信息:"]
    lines.append("=" * 60)

    for param, values in stats.items():
        if param in ['correlations', 'time_intervals']:
            continue

        if isinstance(values, dict) and 'mean' in values:
            lines.append(f"\n{param.upper()}:")
            lines.append(f"  均值: {values.get('mean', 'N/A'):.4f}")
            lines.append(f"  标准差: {values.get('std', 'N/A'):.4f}")
            lines.append(f"  最小值: {values.get('min', 'N/A'):.4f}")
            lines.append(f"  最大值: {values.get('max', 'N/A'):.4f}")
            lines.append(f"  中位数: {values.get('median', 'N/A'):.4f}")

    return "\n".join(lines)


def _format_stats_to_markdown(stats: Dict[str, Any]) -> str:
    """格式化为Markdown"""
    lines = ["# 统计信息"]
    lines.append("")

    lines.append("## 基本统计")
    lines.append("| 参数 | 均值 | 标准差 | 最小值 | 最大值 | 中位数 |")
    lines.append("|------|------|--------|--------|--------|--------|")

    for param, values in stats.items():
        if param in ['correlations', 'time_intervals']:
            continue

        if isinstance(values, dict) and 'mean' in values:
            row = f"| {param} | {values.get('mean', 0):.4f} | {values.get('std', 0):.4f} | "
            row += f"{values.get('min', 0):.4f} | {values.get('max', 0):.4f} | {values.get('median', 0):.4f} |"
            lines.append(row)

    return "\n".join(lines)


def _format_stats_to_html(stats: Dict[str, Any]) -> str:
    """格式化为HTML"""
    html = ["<html><head><title>统计信息</title></head><body>"]
    html.append("<h1>统计信息</h1>")

    html.append("<h2>基本统计</h2>")
    html.append(
        "<table border='1'><tr><th>参数</th><th>均值</th><th>标准差</th><th>最小值</th><th>最大值</th><th>中位数</th></tr>")

    for param, values in stats.items():
        if param in ['correlations', 'time_intervals']:
            continue

        if isinstance(values, dict) and 'mean' in values:
            html.append(f"<tr>")
            html.append(f"<td>{param}</td>")
            html.append(f"<td>{values.get('mean', 0):.4f}</td>")
            html.append(f"<td>{values.get('std', 0):.4f}</td>")
            html.append(f"<td>{values.get('min', 0):.4f}</td>")
            html.append(f"<td>{values.get('max', 0):.4f}</td>")
            html.append(f"<td>{values.get('median', 0):.4f}</td>")
            html.append(f"</tr>")

    html.append("</table>")
    html.append("</body></html>")

    return "\n".join(html)


# 使用示例
if __name__ == "__main__":
    print("数据报告模块测试")
    print("-" * 40)

    # 创建测试数据
    dates = pd.date_range(start='2026-01-01 10:00:00', periods=50, freq='1min')
    test_df = pd.DataFrame({
        'timestamp': dates,
        'temperature': np.random.normal(35, 5, 50),
        'battery_voltage': np.random.uniform(7.0, 8.0, 50),
        'a': np.full(50, 7000) + np.random.normal(0, 10, 50),
        'e': np.full(50, 0.001) + np.random.normal(0, 0.0001, 50),
        'i': np.full(50, 98.7) + np.random.normal(0, 0.1, 50),
        'raan': np.linspace(120, 130, 50),
        'argp': np.full(50, 45),
        'mean_anomaly': np.linspace(0, 360, 50)
    })

    print("1. 生成周期报告...")
    cycle_reports = generate_cycle_report(test_df, cycle_size=10)
    print(f"  生成 {len(cycle_reports)} 个周期报告")

    print("\n2. 生成汇总报告...")
    summary_report = create_summary_report(test_df, cycle_reports)
    print(f"  汇总报告包含 {len(summary_report)} 个部分")

    print("\n3. 格式化统计信息...")
    stats = calculate_statistics(test_df)
    formatted_stats = format_statistics(stats, 'text')
    print(formatted_stats[:200] + "...")

    print("\n4. 保存报告到文件...")
    # 保存文本格式
    success = save_report_to_file(summary_report, "test_summary.txt", "txt")
    print(f"  保存文本报告: {'成功' if success else '失败'}")

    # 保存JSON格式
    success = save_report_to_file(summary_report, "test_summary.json", "json")
    print(f"  保存JSON报告: {'成功' if success else '失败'}")

    print("\n测试完成!")