"""
data_checker.py - 数据检查模块
功能：
1. 读取阈值配置
2. 检查数据是否超出预设阈值
3. 生成报警信息
4. 记录异常事件
"""
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.logger import Logger


class DataChecker:
    def __init__(self, thresholds_file: str = "config/thresholds.yaml"):
        """
        初始化数据检查器
        :param thresholds_file: 阈值配置文件
        """
        self.thresholds_file = thresholds_file
        self.logger = Logger(__name__)
        self.thresholds = self.load_thresholds()


    def load_thresholds(self) -> Dict[str,Any]:
        """
        从YAML文件加载阈值配置
        :return:
        阈值配置字典
        """
        try:
            if not self.thresholds_file.exists():
                self.logger.error(f"阈值文件不存在：{self.thresholds_file}")
                raise FileNotFoundError(f"阈值配置文件不存在{self.thresholds_file}")
            #按UTF-8格式打开并转换成字典
            with open(self.thresholds_file, "r", encoding='utf-8') as file:
                thresholds = yaml.safe_load(file)
            self.logger.info("成功加载阈值配置")
            return thresholds

        except yaml.YAMLError as e:
            self.logger.error(f"YAML解析错误: {e}")
            raise

        except Exception as e:
            self.logger.error(f"加载阈值配置失败: {e}")
            raise



    def check_all_thresholds(self,df: pd.DataFrame) -> pd.DataFrame:
        """
        检查所有阈值
        :param df:待检查的dataframe
        :return:包含所有报警信息的dataframe
        """
        all_alarms = []

        #检查温度
        temp_alarms = self.check_temperature(df)
        all_alarms.extend(temp_alarms)

        #检查电池电压
        voltage_alarms = self.check_battery_voltage(df)
        all_alarms.extend(voltage_alarms)

        #检查轨道参数
        orbit_alarms = self.check_orbit_parameters(df)
        all_alarms.extend(orbit_alarms)

        #转换为dataframe
        if all_alarms:
            alarms_df = pd.DataFrame(all_alarms)
            alarms_df = alarms_df.sort_values('timestamp')
            self.logger.info(f"总计发现{len(alarms_df)} 个报警")
            return alarms_df
        else:
            self.logger.info("无报警信息")
            return pd.DataFrame(columns=['timestamp', 'type', 'level', 'value', 'message'])



    def check_temperature(self,df:pd.DataFrame) -> List[Dict[str,Any]]:
        """
        检查温度数据
        :param df: 包含温度数据的dataframe
        :return:报警信息列表
        """
        alarms = []
        temp_thresholds = self.thresholds.get('temperature',{})

        if not temp_thresholds:
            self.logger.warning("阈值温度未配置")
            return alarms

        for idx,row in df.iterrows():
            timestamp = row['timestamp']
            temp = row['temperature']

            #高于40.0
            if temp > temp_thresholds.get('alarm_max',40.0):
                alarm_msg = f"温度严重超标: {temp}°C (超过报警上限 {temp_thresholds.get('alarm_max')}°C)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'temperature',
                    'level': 'alarm',
                    'value': temp,
                    'message': alarm_msg
                })
            #低于15.0
            elif temp < temp_thresholds.get('alarm_min', 15.0):
                alarm_msg = f"温度过低: {temp}°C (低于报警下限 {temp_thresholds.get('alarm_min')}°C)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'temperature',
                    'level': 'alarm',
                    'value': temp,
                    'message': alarm_msg
                })
            #高于38.0
            elif temp > temp_thresholds.get('warning_max', 38.0):
                alarm_msg = f"温度偏高: {temp}°C (超过警告上限 {temp_thresholds.get('warning_max')}°C)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'temperature',
                    'level': 'warning',
                    'value': temp,
                    'message': alarm_msg
                })
            #低于20.0
            elif temp < temp_thresholds.get('warning_min', 20.0):
                alarm_msg = f"温度偏低: {temp}°C (低于警告下限 {temp_thresholds.get('warning_min')}°C)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'temperature',
                    'level': 'warning',
                    'value': temp,
                    'message': alarm_msg
                })

        #总检查
        if alarms:
            self.logger.warning(f"温度检查发现 {len(alarms)} 个报警")
        else:
            self.logger.info("温度检查正常")

        return alarms



    def check_battery_voltage(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        检查电池电压数据
        Args:
            df: 包含电池电压数据的DataFrame
        Returns:
            报警信息列表
        """
        alarms = []
        voltage_thresholds = self.thresholds.get('battery_voltage', {})

        if not voltage_thresholds:
            self.logger.warning("电池电压阈值未配置")
            return alarms

        for idx, row in df.iterrows():
            timestamp = row['timestamp']
            voltage = row['battery_voltage']

            # 检查电压是否超过报警阈值
            if voltage > voltage_thresholds.get('alarm_max', 8.4):
                alarm_msg = f"电压严重超标: {voltage}V (超过报警上限 {voltage_thresholds.get('alarm_max')}V)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'battery_voltage',
                    'level': 'alarm',
                    'value': voltage,
                    'message': alarm_msg
                })
            elif voltage < voltage_thresholds.get('alarm_min', 7.0):
                alarm_msg = f"电压过低: {voltage}V (低于报警下限 {voltage_thresholds.get('alarm_min')}V)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'battery_voltage',
                    'level': 'alarm',
                    'value': voltage,
                    'message': alarm_msg
                })
            # 检查电压是否超过警告阈值
            elif voltage > voltage_thresholds.get('warning_max', 8.2):
                alarm_msg = f"电压偏高: {voltage}V (超过警告上限 {voltage_thresholds.get('warning_max')}V)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'battery_voltage',
                    'level': 'warning',
                    'value': voltage,
                    'message': alarm_msg
                })
            elif voltage < voltage_thresholds.get('warning_min', 7.3):
                alarm_msg = f"电压偏低: {voltage}V (低于警告下限 {voltage_thresholds.get('warning_min')}V)"
                alarms.append({
                    'timestamp': timestamp,
                    'type': 'battery_voltage',
                    'level': 'warning',
                    'value': voltage,
                    'message': alarm_msg
                })

        if alarms:
            self.logger.warning(f"电池电压检查发现 {len(alarms)} 个报警")
        else:
            self.logger.info("电池电压检查正常")

        return alarms

    def check_orbit_parameters(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        检查轨道参数数据
        Args:
            df: 包含轨道六根数的DataFrame
        Returns:
            报警信息列表
        """
        alarms = []
        orbit_thresholds = self.thresholds.get('orbit_parameters', {})

        if not orbit_thresholds:
            self.logger.warning("轨道参数阈值未配置")
            return alarms

        orbit_params = ['a', 'e', 'i', 'raan', 'argp', 'mean_anomaly']

        for idx, row in df.iterrows():
            timestamp = row['timestamp']

            for param in orbit_params:
                value = row.get(param)
                if value is None:
                    continue

                param_thresholds = orbit_thresholds.get(param, {})
                min_val = param_thresholds.get('min')
                max_val = param_thresholds.get('max')

                if min_val is not None and value < min_val:
                    alarm_msg = f"{param} 参数过低: {value} (低于下限 {min_val})"
                    alarms.append({
                        'timestamp': timestamp,
                        'type': f'orbit_{param}',
                        'level': 'alarm',
                        'value': value,
                        'message': alarm_msg
                    })
                elif max_val is not None and value > max_val:
                    alarm_msg = f"{param} 参数过高: {value} (超过上限 {max_val})"
                    alarms.append({
                        'timestamp': timestamp,
                        'type': f'orbit_{param}',
                        'level': 'alarm',
                        'value': value,
                        'message': alarm_msg
                    })

        if alarms:
            self.logger.warning(f"轨道参数检查发现 {len(alarms)} 个报警")
        else:
            self.logger.info("轨道参数检查正常")

        return alarms



    def generate_alarm_report(self,
                              df: pd.DataFrame,
                              save_to_file:bool = True,
                              output_path: str = "data/processed/alarm_report.txt") -> str:
        """
        生成报警报告
        :param df:待检查的DataFrame
        :param save_to_file: 是否保存到文件
        :param output_path: 输出文件路径
        :return: 报警文件字符串
        """
        #检查所有阈值
        alarms_df = self.check_all_thresholds(df)

        report_lines = ["=" * 60,
                        "卫星遥测数据报警报告",
                        "=" * 60,
                        f"数据时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}", f"数据总条数: {len(df)}",
                        f"报警总数: {len(alarms_df)}",
                        "-" * 60]

        if len(alarms_df) > 0:
            # 按级别统计
            level_counts = alarms_df['level'].value_counts()
            for level, count in level_counts.items():
                report_lines.append(f"{level.upper()} 级别报警: {count} 个")

            # 按类型统计
            type_counts = alarms_df['type'].value_counts()
            report_lines.append("-" * 60)
            report_lines.append("报警类型统计:")
            for alarm_type, count in type_counts.items():
                report_lines.append(f"  {alarm_type}: {count} 个")

            # 前10个报警详情
            report_lines.append("-" * 60)
            report_lines.append("前10个报警详情:")
            for idx, row in alarms_df.head(10).iterrows():
                report_lines.append(f"[{row['timestamp']}] {row['level'].upper()}: {row['message']}")

            if len(alarms_df) > 10:
                report_lines.append(f"... 还有 {len(alarms_df) - 10} 个报警未显示")
        else:
            report_lines.append("无报警信息 - 所有参数均在正常范围内")

        report_lines.append("=" * 60)

        report = "\n".join(report_lines)

        # 保存到文件（如果需要）
        if save_to_file and len(alarms_df) > 0:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.logger.info(f"报警报告已保存到: {output_path}")
            except Exception as e:
                self.logger.error(f"保存报警报告失败: {e}")

        # 输出到控制台
        print(report)

        return report
