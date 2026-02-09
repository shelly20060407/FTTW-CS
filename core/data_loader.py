# CSV读取和解析
from pathlib import Path
from typing import Dict, Any, Union
import numpy as np
import pandas as pd
from pandas import DataFrame
from utils.logger import Logger


class DataLoader:
    # 预期的CSV列名（可能之后会有改动）
    EXPECTED_COLUMNS = [
        'timestamp',  # 时间戳
        'temperature',  # 温度 (°C)
        'battery_voltage',  # 电池电压 (V)
        'a',  # 半长轴 (km)
        'e',  # 偏心率
        'i',  # 轨道倾角 (°)
        'raan',  # 升交点赤经 (°)
        'argp',  # 近地点幅角 (°)
        'mean_anomaly'  # 平近点角 (°)
    ]

    # 列的数据类型
    COLUMN_DTYPES = {
        'timestamp': 'datetime64[ns]',
        'temperature': 'float64',
        'battery_voltage': 'float64',
        'a': 'float64',
        'e': 'float64',
        'i': 'float64',
        'raan': 'float64',
        'argp': 'float64',
        'mean_anomaly': 'float64'
    }

    # 初始化数据加载器
    # data_dir: 原始数据目录
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.logger = Logger(__name__)
        self.data = None
        self.current_file = None
        # 创建数据目录（如果不存在）
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_csv(self, file_path: Union[str, Path], validate: bool = True, parse_dates: bool = True) -> pd.DataFrame:
        """
        :param file_path: CSV file path
        :param validate: 是否验证数据格式
        :param parse_dates: 是否解析时间戳
        :return: DataFrame
        """
        try:
            file_path = Path(file_path)
            self.logger.info(f"开始加载CSV文件：{file_path}")
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在：{file_path}")

            # 读取CSV文件
            # 先不指定parse_dates，后续处理中再解析
            df = pd.read_csv(file_path)

            # 清洗列名：去除可能的前后空格和引号
            df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")

            self.logger.info(f"加载的列名：{list(df.columns)}")

            # 验证数据
            if validate:
                df = self._validate_data(df)

            # 解析时间戳（如果存在且需要解析）
            if parse_dates and 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
                    # 检查是否所有时间戳都成功解析
                    null_timestamps = df['timestamp'].isnull().sum()
                    if null_timestamps > 0:
                        self.logger.warning(f"{null_timestamps} 个时间戳解析失败")
                except Exception as e:
                    self.logger.warning(f"时间戳解析失败：{e}")

            # 数据预处理
            df = self._preprocess_data(df)

            # 记录加载信息
            self.data = df
            self.current_file = file_path
            self.logger.info(f"成功加载数据：{len(df)} 行，{len(df.columns)}列")
            if 'timestamp' in df.columns:
                self.logger.info(f"数据时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
            return df

        except Exception as e:
            self.logger.error(f"CSV文件加载失败：{e}")
            raise

    def load_all_csvs(self, pattern: str = "*.csv", validate: bool = True) -> pd.DataFrame:
        """
        批量加载同一目录下所有CSV文件
        :param pattern: 文件是否匹配
        :param validate: 是否验证数据格式
        :return: 合并后的数据DataFrame
        """
        try:
            csv_files = list(self.data_dir.glob(pattern))
            # 搜寻所有pattern格式文件生成list
            if not csv_files:  # 没找到
                self.logger.warning(f"在目录{self.data_dir} 中未找到{pattern} 文件")
                return pd.DataFrame()
            # 找到了
            self.logger.info(f"找到{len(csv_files)} 个CSV文件")

            all_data = []
            for csv_file in csv_files:
                self.logger.info(f"加载文件：{csv_file.name}")
                df = self.load_csv(csv_file, validate=validate)
                all_data.append(df)

            # 合并所有数据
            if all_data:
                # 所有数据上下堆叠，并重新进行排序,在按照时间戳重新排序
                combined_df = pd.concat(all_data, ignore_index=True)
                if 'timestamp' in combined_df.columns:
                    combined_df = combined_df.sort_values('timestamp')
                self.logger.info(f"合并后的总数据量：{len(combined_df)}行")
                self.data = combined_df
                return combined_df
            else:
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"批量加载CSV文件失败：{e}")
            raise

    def _validate_data(self, df: pd.DataFrame) -> DataFrame:
        """
        验证数据完整性
        :param df: 原始DataFrame
        :return: 验证后的DataFrame
        """
        self.logger.info(f"验证数据，原始列名：{list(df.columns)}")

        # 检查必要的列
        missing_cols = [col for col in self.EXPECTED_COLUMNS if col not in df.columns]

        # 如果列名都不匹配，尝试匹配小写版本
        if len(missing_cols) == len(self.EXPECTED_COLUMNS):
            # 尝试匹配小写列名
            lowercase_mapping = {}
            for expected_col in self.EXPECTED_COLUMNS:
                for actual_col in df.columns:
                    if expected_col.lower() == actual_col.lower():
                        lowercase_mapping[actual_col] = expected_col
                        break

            if lowercase_mapping:
                df = df.rename(columns=lowercase_mapping)
                self.logger.info(f"通过小写匹配重命名列：{lowercase_mapping}")
                # 重新计算缺失列
                missing_cols = [col for col in self.EXPECTED_COLUMNS if col not in df.columns]

        if missing_cols:
            self.logger.info(f"CSV文件缺少以下列：{missing_cols}")

            # 尝试重命名常见列名变体
            column_mapping = {}
            for expected_col in missing_cols:
                # 不区分大小写，下划线
                for actual_col in df.columns:
                    if (expected_col.lower() == actual_col.lower() or
                            expected_col.replace('_', '').lower() == actual_col.replace(' ', '').replace('_',
                                                                                                         '').lower()):
                        column_mapping[actual_col] = expected_col
                        break

            if column_mapping:
                df = df.rename(columns=column_mapping)
                self.logger.info(f"已重命名列：{column_mapping}")
                # 进一步检测
                missing_cols = [col for col in self.EXPECTED_COLUMNS if col not in df.columns]

            # 对最新进行的缺失列进行检测，创建新的默认值
            for col in missing_cols:
                if col == 'timestamp':
                    # 为时间戳创建默认时间
                    df[col] = pd.date_range(start='2026-01-01', periods=len(df), freq='1min')
                    self.logger.warning(f"为缺失列{col}创建默认时间戳")
                else:
                    # 为其他列创建NaN值
                    df[col] = np.nan
                    self.logger.warning(f"为缺失列{col}创建默认值NaN")

        # 确保列顺序正确
        # 只保留预期列中存在的列
        existing_columns = [col for col in self.EXPECTED_COLUMNS if col in df.columns]
        df = df[existing_columns]

        # 检查数据完整性
        null_counts = df.isnull().sum()
        if null_counts.any():
            self.logger.warning(f"数据中存在空值:\n{null_counts[null_counts > 0]}")

        # 检查时间戳唯一性和顺序（如果存在）
        if 'timestamp' in df.columns:
            if df['timestamp'].duplicated().any():
                self.logger.warning("时间戳存在重复，正在处理中......")
                # 为重复时间戳添加微小增量
                duplicates = df['timestamp'].duplicated(keep=False)
                for idx in df[duplicates].index:
                    offset = pd.Timedelta(seconds=idx * 0.001)  # 毫秒级偏移
                    df.loc[idx, 'timestamp'] += offset

            # 按时间戳排序
            df = df.sort_values('timestamp')

        return df

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理
        :param df: 验证完整性后的DataFrame
        :return: 预处理后的DataFrame
        """
        # 设置正确的数据类型
        for col, dtype in self.COLUMN_DTYPES.items():
            if col in df.columns:
                try:  # 强制替换为预设数据类型
                    df[col] = df[col].astype(dtype)
                except Exception as e:
                    self.logger.warning(f"列{col}类型转换失败：{e}")

        # 计算衍生数据
        df = self._calculate_derived_features(df)

        # 重置索引
        df = df.reset_index(drop=True)

        return df

    def _calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算衍生特征
        :param df: 原始数据DataFrame
        :return: 包含衍生特征的DataFrame
        """

        # 计算轨道高度（假设地球半径为6371km）
        if 'a' in df.columns:
            df['altitude'] = df['a'] - 6371  # 轨道高度（km）

        # 计算轨道周期（开普勒第三定律）
        if 'a' in df.columns:
            G = 6.67430e-20  # 引力常数（km^3/kg/s^2）
            M_earth = 5.972e24  # 地球质量（kg）
            df['orbit_period'] = 2 * np.pi * np.sqrt(df['a'] ** 3 / (G * M_earth))  # 秒

        # 计算温度变化率
        if 'temperature' in df.columns and 'timestamp' in df.columns:
            time_diff = df['timestamp'].diff().dt.total_seconds()
            # 避免除零错误
            valid_time_diff = time_diff != 0
            df['temp_change_rate'] = np.nan
            df.loc[valid_time_diff, 'temp_change_rate'] = (
                    df.loc[valid_time_diff, 'temperature'].diff() /
                    time_diff[valid_time_diff]
            )
            df['temp_change_rate'] = df['temp_change_rate'].fillna(0)

        # 计算电压变化率
        if 'battery_voltage' in df.columns and 'timestamp' in df.columns:
            time_diff = df['timestamp'].diff().dt.total_seconds()
            # 避免除零错误
            valid_time_diff = time_diff != 0
            df['voltage_change_rate'] = np.nan
            df.loc[valid_time_diff, 'voltage_change_rate'] = (
                    df.loc[valid_time_diff, 'battery_voltage'].diff() /
                    time_diff[valid_time_diff]
            )
            df['voltage_change_rate'] = df['voltage_change_rate'].fillna(0)

        # 添加时间特征
        if 'timestamp' in df.columns:
            df['hour'] = df['timestamp'].dt.hour
            df['minute'] = df['timestamp'].dt.minute
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_night'] = ((df['hour'] >= 18) | (df['hour'] <= 6)).astype(int)

        return df

    def get_data_info(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        :return: 数据统计信息字典
        """
        if self.data is None:
            return {}

        info = {
            'file': str(self.current_file) if self.current_file else '未加载',
            'total_rows': len(self.data),
            'total_columns': len(self.data.columns),
            'data_quality': {
                'null_values': int(self.data.isnull().sum().sum()),
                'null_percentage': float(
                    self.data.isnull().sum().sum() / (len(self.data) * len(self.data.columns)) * 100),
                'duplicates': int(self.data.duplicated().sum())
            },
            'statistics': {}
        }

        # 添加时间范围（如果存在时间戳列）
        if 'timestamp' in self.data.columns:
            info['time_range'] = {
                'start': self.data['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': self.data['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_days': (self.data['timestamp'].max() - self.data['timestamp'].min()).days
            }

        # 数值列的统计信息
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            info['statistics'][col] = {
                'min': float(self.data[col].min()),
                'max': float(self.data[col].max()),
                'mean': float(self.data[col].mean()),
                'std': float(self.data[col].std()),
                'median': float(self.data[col].median())
            }

        return info

    def save_processed_data(self, output_dir: str = "data/processed",
                            file_name: str = "processed_data.csv"):
        """
        保存处理后的数据
        :param output_dir: 输出目录
        :param file_name: 输出文件名
        """
        if self.data is None:
            self.logger.warning("没有数据可以保存")
            return

        try:
            output_path = Path(output_dir) / file_name
            output_path.parent.mkdir(parents=True, exist_ok=True)

            self.data.to_csv(output_path, index=False)
            self.logger.info(f"处理后的数据已保存到: {output_path}")

        except Exception as e:
            self.logger.error(f"保存处理后的数据失败: {e}")
            raise

    def get_sample_data(self, n_samples: int = 10) -> pd.DataFrame:
        """
        获取数据样本
        :param n_samples: 样本数量
        :return: 样本数据
        """
        if self.data is None:
            self.logger.warning("没有加载数据")
            return pd.DataFrame()

        if n_samples <= 0:
            n_samples = 10

        return self.data.head(n_samples)

    @staticmethod
    def load_all_csv_files(data_dir: str = "data/raw", **kwargs) -> pd.DataFrame:
        """加载目录下所有CSV文件的便捷函数"""
        loader = DataLoader(data_dir)
        return loader.load_all_csvs(**kwargs)

    @staticmethod
    def load_csv_file(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """加载单个CSV文件的便捷函数"""
        loader = DataLoader()
        return loader.load_csv(file_path, **kwargs)