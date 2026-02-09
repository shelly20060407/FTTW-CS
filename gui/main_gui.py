#图形界面
"""
main_gui.py - 卫星遥测数据分析系统图形界面
功能：
1. 数据加载和管理界面
2. 数据可视化展示
3. 阈值设置和报警管理
4. 数据分析和报告生成
5. 图表显示和导出
"""

import json
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, scrolledtext

import numpy as np
import pandas as pd
import plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# 添加项目根目录到Python路径，以便导入模块
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入项目模块
try:
    from core.data_loader import DataLoader
    from core.data_analysis import calculate_statistics, fit_temperature_trend, detect_outliers, \
        analyze_orbit_parameters
    from core.data_report import generate_cycle_report, create_summary_report, save_report_to_file, format_statistics
    from visualization.plot_static import plot_temperature, plot_voltage, plot_orbit_parameters, plot_statistics, \
        plot_all
    from utils.logger import Logger
    import yaml
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块已正确安装")


class SatelliteTelemetryGUI:
    """卫星遥测数据分析系统主界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("卫星遥测数据分析系统 v1.0")
        self.root.geometry("1920x1080")

        # 设置应用程序图标
        try:
            icon_path = project_root / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass

        # 初始化变量
        self.data_loader = None
        self.current_df = None
        self.current_file = None
        self.thresholds = {}
        self.alarms = []

        # 设置样式
        self.setup_styles()

        # 创建日志记录器
        self.logger = Logger("GUI")

        # 创建主界面
        self.create_widgets()

        # 加载默认配置
        self.load_default_config()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 状态栏更新
        self.update_status("系统初始化完成，欢迎使用卫星遥测数据分析系统")

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()

        # 使用clam主题，支持更多自定义
        style.theme_use('clam')

        # 自定义颜色
        style.configure('Title.TLabel',
                        font=('Arial', 16, 'bold'),
                        background='#2c3e50',
                        foreground='white',
                        padding=10)

        style.configure('Header.TLabel',
                        font=('Arial', 12, 'bold'),
                        foreground='#2c3e50')

        style.configure('Action.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=8,
                        background='#3498db',
                        foreground='white')

        style.map('Action.TButton',
                  background=[('active', '#2980b9')])

        style.configure('Success.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=8,
                        background='#27ae60',
                        foreground='white')

        style.map('Success.TButton',
                  background=[('active', '#229954')])

        style.configure('Warning.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=8,
                        background='#f39c12',
                        foreground='white')

        style.map('Warning.TButton',
                  background=[('active', '#d68910')])

        style.configure('Danger.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=8,
                        background='#e74c3c',
                        foreground='white')

        style.map('Danger.TButton',
                  background=[('active', '#c0392b')])

        style.configure('Status.TLabel',
                        font=('Arial', 9),
                        background='#34495e',
                        foreground='white',
                        padding=5)

    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 标题栏
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(title_frame,
                                text="🛰️ 卫星遥测数据分析系统",
                                style='Title.TLabel')
        title_label.pack(fill=tk.X)

        # 主内容区 - 使用Notebook实现标签页
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建各个标签页
        self.create_data_loading_tab()
        self.create_visualization_tab()
        self.create_analysis_tab()
        self.create_thresholds_tab()
        self.create_reports_tab()

        # 日志输出区域
        log_frame = ttk.LabelFrame(main_container, text="系统日志", padding=10)
        log_frame.pack(fill=tk.X, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  height=6,
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 状态栏
        self.status_bar = ttk.Label(main_container,
                                    text="就绪",
                                    style='Status.TLabel',
                                    anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))

    def create_data_loading_tab(self):
        """创建数据加载标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📂 数据加载")

        # 数据加载控制区域
        load_frame = ttk.LabelFrame(tab, text="数据文件操作", padding=15)
        load_frame.pack(fill=tk.X, padx=10, pady=10)

        # 文件选择区域
        file_frame = ttk.Frame(load_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="数据文件:", font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 10))

        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(file_frame, text="浏览...",
                   command=self.browse_file,
                   style='Action.TButton').pack(side=tk.LEFT)

        # 操作按钮区域
        btn_frame = ttk.Frame(load_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="加载CSV文件",
                   command=self.load_csv_file,
                   style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(btn_frame, text="批量加载目录",
                   command=self.load_directory,
                   style='Action.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(btn_frame, text="清除数据",
                   command=self.clear_data,
                   style='Danger.TButton').pack(side=tk.LEFT)

        # 数据预览区域
        preview_frame = ttk.LabelFrame(tab, text="数据预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 创建Treeview显示数据
        self.create_data_treeview(preview_frame)

    def create_data_treeview(self, parent):
        """创建数据预览表格"""
        # 创建滚动条
        scroll_y = ttk.Scrollbar(parent)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 创建Treeview
        columns = ('timestamp', 'temperature', 'battery_voltage', 'a', 'e', 'i', 'raan', 'argp', 'mean_anomaly')
        self.data_tree = ttk.Treeview(parent,
                                      columns=columns,
                                      show='headings',
                                      yscrollcommand=scroll_y.set,
                                      xscrollcommand=scroll_x.set)

        # 设置列标题
        column_names = {
            'timestamp': '时间戳',
            'temperature': '温度(°C)',
            'battery_voltage': '电池电压(V)',
            'a': '半长轴(km)',
            'e': '偏心率',
            'i': '轨道倾角(°)',
            'raan': '升交点赤经(°)',
            'argp': '近地点幅角(°)',
            'mean_anomaly': '平近点角(°)'
        }

        for col in columns:
            self.data_tree.heading(col, text=column_names.get(col, col))
            self.data_tree.column(col, width=100, anchor=tk.CENTER)

        self.data_tree.pack(fill=tk.BOTH, expand=True)

        # 配置滚动条
        scroll_y.config(command=self.data_tree.yview)
        scroll_x.config(command=self.data_tree.xview)

        # 添加右键菜单
        self.setup_treeview_context_menu()

    def setup_treeview_context_menu(self):
        """设置Treeview右键菜单"""
        self.tree_menu = tk.Menu(self.data_tree, tearoff=0)
        self.tree_menu.add_command(label="复制选中行", command=self.copy_selected_row)
        self.tree_menu.add_command(label="导出选中数据", command=self.export_selected_data)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="刷新预览", command=self.refresh_data_preview)

        # 绑定右键事件
        self.data_tree.bind("<Button-3>", self.show_treeview_context_menu)

    def create_visualization_tab(self):
        """创建可视化标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 数据可视化")

        # 图表选择区域
        chart_control_frame = ttk.LabelFrame(tab, text="图表控制", padding=15)
        chart_control_frame.pack(fill=tk.X, padx=10, pady=10)

        # 图表类型选择
        chart_type_frame = ttk.Frame(chart_control_frame)
        chart_type_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(chart_type_frame, text="选择图表类型:",
                  font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 10))

        self.chart_var = tk.StringVar(value="temperature")
        chart_types = [
            ("温度曲线", "temperature"),
            ("电压曲线", "voltage"),
            ("轨道参数", "orbit"),
            ("统计图表", "statistics")
        ]

        for text, value in chart_types:
            ttk.Radiobutton(chart_type_frame, text=text, variable=self.chart_var,
                            value=value).pack(side=tk.LEFT, padx=10)

        # 控制按钮
        control_btn_frame = ttk.Frame(chart_control_frame)
        control_btn_frame.pack(fill=tk.X)

        ttk.Button(control_btn_frame, text="生成图表",
                   command=self.generate_chart,
                   style='Action.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(control_btn_frame, text="生成所有图表",
                   command=self.generate_all_charts,
                   style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(control_btn_frame, text="保存图表",
                   command=self.save_chart,
                   style='Warning.TButton').pack(side=tk.LEFT)

        # 图表显示区域
        self.chart_frame = ttk.LabelFrame(tab, text="图表显示", padding=10)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 创建matplotlib画布
        self.create_matplotlib_canvas()

    def create_matplotlib_canvas(self):
        """创建matplotlib画布"""
        #设置图例字体
        import matplotlib.pyplot as plt
        import matplotlib

        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 创建图形
        self.current_figure = None
        self.canvas = None
        self.toolbar = None

        # 初始显示空白图形
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, '请加载数据并选择图表类型',
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=14,
                color='gray')
        ax.set_axis_off()

        # 创建画布
        self.canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 添加工具栏
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.chart_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_analysis_tab(self):
        """创建数据分析标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📈 数据分析")

        # 分析功能区域
        analysis_frame = ttk.LabelFrame(tab, text="分析功能", padding=15)
        analysis_frame.pack(fill=tk.X, padx=10, pady=10)

        # 分析按钮网格
        btn_grid = ttk.Frame(analysis_frame)
        btn_grid.pack(fill=tk.X)

        analysis_buttons = [
            ("📊 基本统计", self.analyze_statistics, '#3498db'),
            ("📈 温度趋势", self.analyze_temperature_trend, '#2ecc71'),
            ("⚠️ 异常检测", self.analyze_outliers, '#e74c3c'),
            ("🛰️ 轨道分析", self.analyze_orbit, '#9b59b6'),
            ("🔍 数据质量", self.analyze_data_quality, '#f39c12'),
            ("📋 综合报告", self.generate_comprehensive_report, '#1abc9c')
        ]

        # 创建两行三列的按钮网格
        for i, (text, command, color) in enumerate(analysis_buttons):
            row = i // 3
            col = i % 3

            btn = tk.Button(btn_grid, text=text, command=command,
                            font=('Arial', 11, 'bold'),
                            bg=color, fg='white',
                            relief=tk.RAISED,
                            padx=20, pady=15,
                            cursor='hand2')
            btn.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.lighten_color(b.cget('bg'))))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

        # 配置网格权重
        for i in range(3):
            btn_grid.columnconfigure(i, weight=1)
        for i in range(2):
            btn_grid.rowconfigure(i, weight=1)

        # 结果显示区域
        result_frame = ttk.LabelFrame(tab, text="分析结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 创建结果显示文本框
        self.result_text = scrolledtext.ScrolledText(result_frame,
                                                     wrap=tk.WORD,
                                                     font=('Consolas', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 添加结果操作按钮
        result_btn_frame = ttk.Frame(result_frame)
        result_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(result_btn_frame, text="清空结果",
                   command=self.clear_results,
                   style='Danger.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(result_btn_frame, text="保存结果",
                   command=self.save_analysis_results,
                   style='Action.TButton').pack(side=tk.LEFT)

    def create_thresholds_tab(self):
        """创建阈值管理标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚡ 阈值管理")

        # 阈值设置区域
        threshold_frame = ttk.LabelFrame(tab, text="阈值设置", padding=15)
        threshold_frame.pack(fill=tk.X, padx=10, pady=10)

        # 温度阈值
        temp_frame = ttk.LabelFrame(threshold_frame, text="温度阈值 (°C)", padding=10)
        temp_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(temp_frame, text="高温报警:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.temp_high_var = tk.DoubleVar(value=40.0)
        ttk.Entry(temp_frame, textvariable=self.temp_high_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(temp_frame, text="高温警告:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.temp_warn_high_var = tk.DoubleVar(value=38.0)
        ttk.Entry(temp_frame, textvariable=self.temp_warn_high_var, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(temp_frame, text="低温警告:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.temp_warn_low_var = tk.DoubleVar(value=22.0)
        ttk.Entry(temp_frame, textvariable=self.temp_warn_low_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(temp_frame, text="低温报警:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.temp_low_var = tk.DoubleVar(value=20.0)
        ttk.Entry(temp_frame, textvariable=self.temp_low_var, width=10).grid(row=1, column=3, padx=5, pady=5)

        # 电压阈值
        voltage_frame = ttk.LabelFrame(threshold_frame, text="电池电压阈值 (V)", padding=10)
        voltage_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(voltage_frame, text="高压报警:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.voltage_high_var = tk.DoubleVar(value=8.4)
        ttk.Entry(voltage_frame, textvariable=self.voltage_high_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(voltage_frame, text="高压警告:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.voltage_warn_high_var = tk.DoubleVar(value=8.2)
        ttk.Entry(voltage_frame, textvariable=self.voltage_warn_high_var, width=10).grid(row=0, column=3, padx=5,
                                                                                         pady=5)

        ttk.Label(voltage_frame, text="低压警告:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.voltage_warn_low_var = tk.DoubleVar(value=7.2)
        ttk.Entry(voltage_frame, textvariable=self.voltage_warn_low_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(voltage_frame, text="低压报警:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.voltage_low_var = tk.DoubleVar(value=7.0)
        ttk.Entry(voltage_frame, textvariable=self.voltage_low_var, width=10).grid(row=1, column=3, padx=5, pady=5)

        # 控制按钮
        threshold_btn_frame = ttk.Frame(threshold_frame)
        threshold_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(threshold_btn_frame, text="保存阈值",
                   command=self.save_thresholds,
                   style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(threshold_btn_frame, text="应用阈值检查",
                   command=self.apply_thresholds,
                   style='Warning.TButton').pack(side=tk.LEFT)

        # 报警结果显示区域
        alarm_frame = ttk.LabelFrame(tab, text="报警结果", padding=10)
        alarm_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 创建报警列表
        self.alarm_listbox = tk.Listbox(alarm_frame,
                                        font=('Consolas', 10),
                                        bg='#fff',
                                        selectbackground='#3498db')
        self.alarm_listbox.pack(fill=tk.BOTH, expand=True)

        # 报警操作按钮
        alarm_btn_frame = ttk.Frame(alarm_frame)
        alarm_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(alarm_btn_frame, text="清空报警",
                   command=self.clear_alarms,
                   style='Danger.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(alarm_btn_frame, text="导出报警",
                   command=self.export_alarms,
                   style='Action.TButton').pack(side=tk.LEFT)

    def create_reports_tab(self):
        """创建报告生成标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 报告生成")

        # 报告类型选择
        report_type_frame = ttk.LabelFrame(tab, text="报告类型", padding=15)
        report_type_frame.pack(fill=tk.X, padx=10, pady=10)

        self.report_var = tk.StringVar(value="summary")

        report_types = [
            ("📊 周期报告", "cycle"),
            ("📋 综合报告", "comprehensive")
        ]

        for i, (text, value) in enumerate(report_types):
            ttk.Radiobutton(report_type_frame, text=text, variable=self.report_var,
                            value=value).grid(row=i // 3, column=i % 3, padx=10, pady=5, sticky=tk.W)

        # 报告参数设置
        param_frame = ttk.LabelFrame(tab, text="报告参数", padding=15)
        param_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(param_frame, text="周期大小:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cycle_size_var = tk.IntVar(value=10)
        ttk.Entry(param_frame, textvariable=self.cycle_size_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(param_frame, text="输出格式:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.report_format_var = tk.StringVar(value="txt")
        format_combo = ttk.Combobox(param_frame, textvariable=self.report_format_var,
                                    values=["txt", "json", "html", "md"], width=10)
        format_combo.grid(row=0, column=3, padx=5, pady=5)

        # 报告操作按钮
        report_btn_frame = ttk.Frame(tab)
        report_btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(report_btn_frame, text="生成报告",
                   command=self.generate_report,
                   style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(report_btn_frame, text="预览报告",
                   command=self.preview_report,
                   style='Action.TButton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(report_btn_frame, text="导出报告",
                   command=self.export_report,
                   style='Warning.TButton').pack(side=tk.LEFT)

        # 报告预览区域
        preview_frame = ttk.LabelFrame(tab, text="报告预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.report_text = scrolledtext.ScrolledText(preview_frame,
                                                     wrap=tk.WORD,
                                                     font=('Consolas', 10))
        self.report_text.pack(fill=tk.BOTH, expand=True)

    # =========================== 功能方法 ===========================

    def load_default_config(self):
        """加载默认配置"""
        try:
            config_path = project_root / "config" / "thresholds.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.thresholds = yaml.safe_load(f)
                    self.update_status(f"已加载默认阈值配置")
            else:
                # 创建默认配置
                self.thresholds = {
                    'temperature': {
                        'max': 40.0,
                        'min': 20.0,
                        'warning_max': 38.0,
                        'warning_min': 22.0
                    },
                    'battery_voltage': {
                        'max': 8.4,
                        'min': 7.0,
                        'warning_max': 8.2,
                        'warning_min': 7.2
                    }
                }
                self.update_status("使用默认阈值配置")
        except Exception as e:
            self.log_error(f"加载配置失败: {e}")

    def browse_file(self):
        """浏览文件"""
        file_path = filedialog.askopenfilename(
            title="选择CSV数据文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.update_status(f"已选择文件: {Path(file_path).name}")

    def load_csv_file(self):
        """加载CSV文件"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "请先选择CSV文件")
            return

        try:
            self.update_status("正在加载数据...")
            self.root.config(cursor='wait')

            # 在后台线程中加载数据
            def load_data():
                try:
                    self.data_loader = DataLoader()
                    self.current_df = self.data_loader.load_csv(file_path)
                    self.current_file = file_path

                    # 在主线程中更新UI
                    self.root.after(0, self.on_data_loaded)
                except Exception as e:
                    self.root.after(0, lambda: self.log_error(f"加载数据失败: {e}"))
                finally:
                    self.root.after(0, lambda: self.root.config(cursor=''))

            threading.Thread(target=load_data, daemon=True).start()

        except Exception as e:
            self.log_error(f"加载数据失败: {e}")
            self.root.config(cursor='')

    def load_directory(self):
        """批量加载目录"""
        dir_path = filedialog.askdirectory(title="选择数据目录")
        if not dir_path:
            return

        try:
            self.update_status("正在批量加载数据...")
            self.root.config(cursor='wait')

            def load_data():
                try:
                    self.data_loader = DataLoader(data_dir=dir_path)
                    self.current_df = self.data_loader.load_all_csvs()
                    self.current_file = dir_path

                    self.root.after(0, self.on_data_loaded)
                except Exception as e:
                    self.root.after(0, lambda: self.log_error(f"批量加载失败: {e}"))
                finally:
                    self.root.after(0, lambda: self.root.config(cursor=''))

            threading.Thread(target=load_data, daemon=True).start()

        except Exception as e:
            self.log_error(f"批量加载失败: {e}")
            self.root.config(cursor='')

    def on_data_loaded(self):
        """数据加载完成后的处理"""
        if self.current_df is not None:
            data_info = f"成功加载 {len(self.current_df)} 条数据，{len(self.current_df.columns)} 列"
            self.update_status(data_info)
            self.log_message(f"📊 {data_info}")

            # 更新数据预览
            self.refresh_data_preview()

            # 更新阈值标签页的阈值
            self.update_threshold_entries()

            messagebox.showinfo("成功", f"数据加载成功！\n\n{data_info}")
        else:
            messagebox.showerror("错误", "数据加载失败")

    def refresh_data_preview(self, max_rows=100):
        """刷新数据预览"""
        if self.current_df is None:
            return

        try:
            # 清除现有数据
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)

            # 显示前max_rows行数据
            preview_df = self.current_df.head(max_rows)

            for idx, row in preview_df.iterrows():
                values = []
                for col in self.data_tree['columns']:
                    if col in row:
                        value = row[col]
                        # 格式化显示
                        if isinstance(value, (float, np.floating)):
                            if col in ['temperature', 'battery_voltage']:
                                values.append(f"{value:.2f}")
                            elif col in ['a']:
                                values.append(f"{value:.1f}")
                            elif col in ['e']:
                                values.append(f"{value:.6f}")
                            else:
                                values.append(f"{value:.4f}")
                        elif isinstance(value, pd.Timestamp):
                            values.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                        else:
                            values.append(str(value))
                    else:
                        values.append('')

                self.data_tree.insert('', 'end', values=values)

            self.update_status(f"数据预览已更新，显示 {len(preview_df)} 行")

        except Exception as e:
            self.log_error(f"刷新数据预览失败: {e}")

    def clear_data(self):
        """清除数据"""
        if messagebox.askyesno("确认", "确定要清除所有数据吗？"):
            self.current_df = None
            self.current_file = None
            self.data_loader = None

            # 清除数据预览
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)

            # 清除图表
            if self.canvas:
                fig = Figure(figsize=(10, 6), dpi=100)
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, '数据已清除\n请加载新数据',
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=14,
                        color='gray')
                ax.set_axis_off()

                self.canvas.figure = fig
                self.canvas.draw()

            # 清除结果和报告
            self.result_text.delete(1.0, tk.END)
            self.report_text.delete(1.0, tk.END)
            self.alarm_listbox.delete(0, tk.END)

            self.update_status("数据已清除")
            self.log_message("🗑️ 数据已清除")

    def generate_chart(self):
        """生成图表"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            chart_type = self.chart_var.get()

            if chart_type == "temperature":
                thresholds = {'high': self.temp_high_var.get(), 'low': self.temp_low_var.get()}
                fig = plot_temperature(self.current_df, thresholds)

            elif chart_type == "voltage":
                thresholds = {'high': self.voltage_high_var.get(), 'low': self.voltage_low_var.get()}
                fig = plot_voltage(self.current_df, thresholds)

            elif chart_type == "orbit":
                fig = plot_orbit_parameters(self.current_df)

            elif chart_type == "statistics":
                fig = plot_statistics(self.current_df)

            if fig:
                # 更新画布
                self.canvas.figure = fig
                self.canvas.draw()

                self.update_status(f"已生成{chart_type}图表")
                self.log_message(f"📈 已生成{chart_type}图表")
            else:
                messagebox.showerror("错误", "图表生成失败")

        except Exception as e:
            self.log_error(f"生成图表失败: {e}")

    def generate_all_charts(self):
        """生成所有图表"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在生成所有图表...")
            self.root.config(cursor='wait')

            def generate():
                try:
                    thresholds = {
                        'temperature': {
                            'max': self.temp_high_var.get(),
                            'min': self.temp_low_var.get()
                        },
                        'battery_voltage': {
                            'max': self.voltage_high_var.get(),
                            'min': self.voltage_low_var.get()
                        }
                    }

                    saved_files = plot_all(self.current_df, "data/processed/plots", thresholds)

                    self.root.after(0, lambda: self.on_charts_generated(saved_files))
                except Exception as e:
                    self.root.after(0, lambda: self.log_error(f"生成所有图表失败: {e}"))
                finally:
                    self.root.after(0, lambda: self.root.config(cursor=''))

            threading.Thread(target=generate, daemon=True).start()

        except Exception as e:
            self.log_error(f"生成所有图表失败: {e}")
            self.root.config(cursor='')

    def on_charts_generated(self, saved_files):
        """图表生成完成后的处理"""
        message = f"已生成 {len(saved_files)} 组图表\n"
        for chart_type, files in saved_files.items():
            message += f"- {chart_type}: {len(files)} 个文件\n"

        self.update_status("所有图表生成完成")
        self.log_message(f"📊 {message}")
        messagebox.showinfo("成功", message)

    def save_chart(self):
        """保存图表"""
        if not hasattr(self, 'canvas') or self.canvas.figure is None:
            messagebox.showwarning("警告", "没有可保存的图表")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存图表",
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                self.canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                self.update_status(f"图表已保存到: {Path(file_path).name}")
                self.log_message(f"💾 图表已保存: {Path(file_path).name}")
            except Exception as e:
                self.log_error(f"保存图表失败: {e}")

    # =========================== 数据分析方法 ===========================

    def analyze_statistics(self):
        """分析基本统计信息"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在计算统计信息...")
            stats = calculate_statistics(self.current_df)

            # 格式化结果显示
            result_text = format_statistics(stats, 'text')

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "=" * 60 + "\n")
            self.result_text.insert(tk.END, "基本统计信息分析结果\n")
            self.result_text.insert(tk.END, "=" * 60 + "\n\n")
            self.result_text.insert(tk.END, result_text)

            self.update_status("统计信息分析完成")
            self.log_message("📊 已计算基本统计信息")

        except Exception as e:
            self.log_error(f"统计分析失败: {e}")

    def analyze_temperature_trend(self):
        """分析温度趋势"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在分析温度趋势...")
            trend = fit_temperature_trend(self.current_df)

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "=" * 60 + "\n")
            self.result_text.insert(tk.END, "温度趋势分析结果\n")
            self.result_text.insert(tk.END, "=" * 60 + "\n\n")

            if trend:
                self.result_text.insert(tk.END, f"温度趋势: {trend.get('trend', '未知')}\n")
                self.result_text.insert(tk.END, f"趋势斜率: {trend.get('slope', 0):.4f}\n")
                self.result_text.insert(tk.END, f"拟合度 R²: {trend.get('r_squared', 0):.4f}\n")
                self.result_text.insert(tk.END, f"当前温度: {trend.get('current_temperature', 0):.2f}°C\n")
                self.result_text.insert(tk.END, f"平均温度: {trend.get('average_temperature', 0):.2f}°C\n")
                self.result_text.insert(tk.END, f"温度范围: {trend.get('temperature_range', 0):.2f}°C\n\n")

                # 显示预测结果
                future_pred = trend.get('future_predictions', [])
                if future_pred:
                    self.result_text.insert(tk.END, "未来预测值:\n")
                    for i, pred in enumerate(future_pred, 1):
                        self.result_text.insert(tk.END, f"  未来第{i}点: {pred:.2f}°C\n")
            else:
                self.result_text.insert(tk.END, "无法分析温度趋势\n")

            self.update_status("温度趋势分析完成")
            self.log_message("📈 已分析温度趋势")

        except Exception as e:
            self.log_error(f"温度趋势分析失败: {e}")

    def analyze_outliers(self):
        """异常值检测"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在检测异常值...")
            outliers = detect_outliers(self.current_df, method='iqr')

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "=" * 60 + "\n")
            self.result_text.insert(tk.END, "异常值检测结果\n")
            self.result_text.insert(tk.END, "=" * 60 + "\n\n")

            if outliers and 'summary' in outliers:
                total = outliers['summary'].get('total_outliers', 0)
                self.result_text.insert(tk.END, f"检测到异常值总数: {total}\n")
                self.result_text.insert(tk.END, f"检测方法: {outliers['summary'].get('method', '未知')}\n\n")

                for col, info in outliers.items():
                    if col != 'summary':
                        count = info.get('count', 0)
                        percentage = info.get('percentage', 0)
                        self.result_text.insert(tk.END, f"{col.upper()}:\n")
                        self.result_text.insert(tk.END, f"  异常值数量: {count} ({percentage:.2f}%)\n")

                        if info.get('values'):
                            self.result_text.insert(tk.END, f"  异常值示例: {info['values'][:3]}\n")
                        self.result_text.insert(tk.END, "\n")
            else:
                self.result_text.insert(tk.END, "未检测到异常值\n")

            self.update_status("异常值检测完成")
            self.log_message("⚠️ 已检测异常值")

        except Exception as e:
            self.log_error(f"异常值检测失败: {e}")

    def analyze_orbit(self):
        """轨道参数分析"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在分析轨道参数...")
            orbit_analysis = analyze_orbit_parameters(self.current_df)

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "=" * 60 + "\n")
            self.result_text.insert(tk.END, "轨道参数分析结果\n")
            self.result_text.insert(tk.END, "=" * 60 + "\n\n")

            if orbit_analysis:
                for param, info in orbit_analysis.items():
                    if param not in ['orbit_stability', 'parameter_correlations', 'orbit_period']:
                        self.result_text.insert(tk.END, f"{param.upper()} ({info.get('stability', '未知')}):\n")
                        self.result_text.insert(tk.END, f"  均值: {info.get('mean', 0):.4f}\n")
                        self.result_text.insert(tk.END, f"  标准差: {info.get('std', 0):.4f}\n")
                        self.result_text.insert(tk.END, f"  范围: {info.get('range', 0):.4f}\n\n")

                if 'orbit_stability' in orbit_analysis:
                    stability = orbit_analysis['orbit_stability']
                    self.result_text.insert(tk.END, "轨道稳定性分析:\n")
                    self.result_text.insert(tk.END, f"  评估: {stability.get('stability_assessment', '未知')}\n")

                if 'orbit_period' in orbit_analysis:
                    period = orbit_analysis['orbit_period']
                    self.result_text.insert(tk.END, "轨道周期:\n")
                    self.result_text.insert(tk.END, f"  平均周期: {period.get('mean_minutes', 0):.2f} 分钟\n")
            else:
                self.result_text.insert(tk.END, "无法分析轨道参数\n")

            self.update_status("轨道参数分析完成")
            self.log_message("🛰️ 已分析轨道参数")

        except Exception as e:
            self.log_error(f"轨道参数分析失败: {e}")

    def analyze_data_quality(self):
        """分析数据质量"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在分析数据质量...")

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "=" * 60 + "\n")
            self.result_text.insert(tk.END, "数据质量分析报告\n")
            self.result_text.insert(tk.END, "=" * 60 + "\n\n")

            # 基本信息
            total_rows = len(self.current_df)
            total_cols = len(self.current_df.columns)

            self.result_text.insert(tk.END, f"数据总行数: {total_rows}\n")
            self.result_text.insert(tk.END, f"数据总列数: {total_cols}\n\n")

            # 缺失值分析
            missing_counts = self.current_df.isnull().sum()
            total_missing = missing_counts.sum()
            missing_percentage = total_missing / (total_rows * total_cols) * 100

            self.result_text.insert(tk.END, f"缺失值总数: {total_missing}\n")
            self.result_text.insert(tk.END, f"缺失值比例: {missing_percentage:.2f}%\n\n")

            # 各列缺失情况
            if total_missing > 0:
                self.result_text.insert(tk.END, "各列缺失值情况:\n")
                for col, count in missing_counts.items():
                    if count > 0:
                        col_percentage = count / total_rows * 100
                        self.result_text.insert(tk.END, f"  {col}: {count} ({col_percentage:.2f}%)\n")
                self.result_text.insert(tk.END, "\n")

            # 重复值分析
            duplicate_rows = self.current_df.duplicated().sum()
            duplicate_percentage = duplicate_rows / total_rows * 100

            self.result_text.insert(tk.END, f"重复行数: {duplicate_rows}\n")
            self.result_text.insert(tk.END, f"重复行比例: {duplicate_percentage:.2f}%\n\n")

            # 数据质量评估
            quality_score = 100 - missing_percentage - duplicate_percentage
            quality_level = "优秀" if quality_score >= 90 else "良好" if quality_score >= 80 else "一般" if quality_score >= 60 else "较差"

            self.result_text.insert(tk.END, f"数据质量评分: {quality_score:.1f}/100\n")
            self.result_text.insert(tk.END, f"数据质量等级: {quality_level}\n")

            # 建议
            self.result_text.insert(tk.END, "\n建议:\n")
            if missing_percentage > 10:
                self.result_text.insert(tk.END, "⚠️ 缺失值较多，建议检查数据采集系统\n")
            if duplicate_percentage > 5:
                self.result_text.insert(tk.END, "⚠️ 重复值较多，建议检查数据存储流程\n")
            if quality_score >= 90:
                self.result_text.insert(tk.END, "✅ 数据质量良好，可直接用于分析\n")

            self.update_status("数据质量分析完成")
            self.log_message("🔍 已分析数据质量")

        except Exception as e:
            self.log_error(f"数据质量分析失败: {e}")

    def generate_comprehensive_report(self):
        """生成综合报告"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在生成综合报告...")

            # 汇总分析结果
            stats = calculate_statistics(self.current_df)
            trend = fit_temperature_trend(self.current_df)
            outliers = detect_outliers(self.current_df)
            orbit_analysis = analyze_orbit_parameters(self.current_df)

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "=" * 70 + "\n")
            self.result_text.insert(tk.END, "卫星遥测数据综合分析报告\n")
            self.result_text.insert(tk.END, "=" * 70 + "\n\n")

            # 生成时间
            self.result_text.insert(tk.END, f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.result_text.insert(tk.END,
                                    f"数据文件: {Path(self.current_file).name if self.current_file else '未知'}\n")
            self.result_text.insert(tk.END, f"数据条数: {len(self.current_df)}\n\n")

            # 数据概览
            self.result_text.insert(tk.END, "一、数据概览\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")
            self.result_text.insert(tk.END, f"数据列数: {len(self.current_df.columns)}\n")

            if 'timestamp' in self.current_df.columns:
                time_min = self.current_df['timestamp'].min()
                time_max = self.current_df['timestamp'].max()
                time_diff = time_max - time_min
                self.result_text.insert(tk.END, f"时间范围: {time_min} 到 {time_max}\n")
                self.result_text.insert(tk.END, f"时间跨度: {time_diff}\n")
            self.result_text.insert(tk.END, "\n")

            # 关键指标
            self.result_text.insert(tk.END, "二、关键指标统计\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")

            key_params = ['temperature', 'battery_voltage', 'a', 'e', 'i']
            for param in key_params:
                if param in stats:
                    param_stats = stats[param]
                    self.result_text.insert(tk.END, f"{param.upper()}:\n")
                    self.result_text.insert(tk.END, f"  均值: {param_stats.get('mean', 0):.4f}\n")
                    self.result_text.insert(tk.END, f"  标准差: {param_stats.get('std', 0):.4f}\n")
                    self.result_text.insert(tk.END,
                                            f"  范围: [{param_stats.get('min', 0):.4f}, {param_stats.get('max', 0):.4f}]\n\n")

            # 趋势分析
            self.result_text.insert(tk.END, "三、趋势分析\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")
            if trend:
                self.result_text.insert(tk.END, f"温度趋势: {trend.get('trend', '未知')}\n")
                self.result_text.insert(tk.END, f"拟合优度: R² = {trend.get('r_squared', 0):.4f}\n\n")

            # 异常值
            self.result_text.insert(tk.END, "四、异常值检测\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")
            if outliers and 'summary' in outliers:
                total_outliers = outliers['summary'].get('total_outliers', 0)
                self.result_text.insert(tk.END, f"异常值总数: {total_outliers}\n")
                if total_outliers > 0:
                    self.result_text.insert(tk.END,
                                            f"异常值比例: {total_outliers / len(self.current_df) * 100:.2f}%\n\n")
            else:
                self.result_text.insert(tk.END, "未检测到异常值\n\n")

            # 轨道分析
            self.result_text.insert(tk.END, "五、轨道参数分析\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")
            if orbit_analysis:
                if 'orbit_stability' in orbit_analysis:
                    stability = orbit_analysis['orbit_stability'].get('stability_assessment', '未知')
                    self.result_text.insert(tk.END, f"轨道稳定性: {stability}\n\n")

            # 总结和建议
            self.result_text.insert(tk.END, "六、总结与建议\n")
            self.result_text.insert(tk.END, "-" * 40 + "\n")

            # 根据分析结果生成建议
            recommendations = []

            # 温度建议
            if 'temperature' in stats:
                temp_std = stats['temperature'].get('std', 0)
                if temp_std > 5:
                    recommendations.append("温度波动较大，建议检查温控系统")

            # 电压建议
            if 'battery_voltage' in stats:
                voltage_min = stats['battery_voltage'].get('min', 8)
                if voltage_min < 7.2:
                    recommendations.append("电池电压偏低，建议检查电源系统")

            # 异常值建议
            if outliers and 'summary' in outliers:
                total_outliers = outliers['summary'].get('total_outliers', 0)
                if total_outliers > len(self.current_df) * 0.1:
                    recommendations.append("异常值较多，建议检查传感器状态")

            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    self.result_text.insert(tk.END, f"{i}. {rec}\n")
            else:
                self.result_text.insert(tk.END, "✅ 所有参数正常，系统运行良好\n")

            self.update_status("综合报告生成完成")
            self.log_message("📋 已生成综合报告")

        except Exception as e:
            self.log_error(f"生成综合报告失败: {e}")

    def clear_results(self):
        """清除分析结果"""
        self.result_text.delete(1.0, tk.END)
        self.update_status("分析结果已清除")

    def save_analysis_results(self):
        """保存分析结果"""
        results = self.result_text.get(1.0, tk.END).strip()
        if not results:
            messagebox.showwarning("警告", "没有可保存的分析结果")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存分析结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(results)

                self.update_status(f"分析结果已保存到: {Path(file_path).name}")
                self.log_message(f"💾 分析结果已保存")
            except Exception as e:
                self.log_error(f"保存分析结果失败: {e}")

    # =========================== 阈值管理方法 ===========================

    def update_threshold_entries(self):
        """更新阈值输入框的值"""
        if not self.thresholds:
            return

        try:
            # 温度阈值
            if 'temperature' in self.thresholds:
                temp_thresh = self.thresholds['temperature']
                self.temp_high_var.set(temp_thresh.get('max', 40.0))
                self.temp_warn_high_var.set(temp_thresh.get('warning_max', 38.0))
                self.temp_warn_low_var.set(temp_thresh.get('warning_min', 22.0))
                self.temp_low_var.set(temp_thresh.get('min', 20.0))

            # 电压阈值
            if 'battery_voltage' in self.thresholds:
                volt_thresh = self.thresholds['battery_voltage']
                self.voltage_high_var.set(volt_thresh.get('max', 8.4))
                self.voltage_warn_high_var.set(volt_thresh.get('warning_max', 8.2))
                self.voltage_warn_low_var.set(volt_thresh.get('warning_min', 7.2))
                self.voltage_low_var.set(volt_thresh.get('min', 7.0))
        except Exception as e:
            self.log_error(f"更新阈值输入框失败: {e}")

    def save_thresholds(self):
        """保存阈值设置"""
        try:
            self.thresholds = {
                'temperature': {
                    'max': self.temp_high_var.get(),
                    'warning_max': self.temp_warn_high_var.get(),
                    'warning_min': self.temp_warn_low_var.get(),
                    'min': self.temp_low_var.get()
                },
                'battery_voltage': {
                    'max': self.voltage_high_var.get(),
                    'warning_max': self.voltage_warn_high_var.get(),
                    'warning_min': self.voltage_warn_low_var.get(),
                    'min': self.voltage_low_var.get()
                }
            }

            # 保存到文件
            config_path = project_root / "config" / "thresholds.yaml"
            config_path.parent.mkdir(exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.thresholds, f, allow_unicode=True, default_flow_style=False)

            self.update_status("阈值设置已保存")
            self.log_message("⚡ 阈值设置已保存")
            messagebox.showinfo("成功", "阈值设置已保存到配置文件")

        except Exception as e:
            self.log_error(f"保存阈值失败: {e}")

    def load_thresholds(self):
        """加载阈值设置"""
        try:
            config_path = project_root / "config" / "thresholds.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.thresholds = yaml.safe_load(f)
                    self.update_threshold_entries()
                    self.update_status("已加载阈值配置")
                    self.log_message("⚡ 已加载阈值配置")
            else:
                messagebox.showwarning("警告", "阈值配置文件不存在")
        except Exception as e:
            self.log_error(f"加载阈值失败: {e}")

    def apply_thresholds(self):
        """应用阈值检查"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            self.update_status("正在应用阈值检查...")

            # 清除现有报警
            self.alarm_listbox.delete(0, tk.END)
            self.alarms = []

            # 检查温度阈值
            temp_high = self.temp_high_var.get()
            temp_low = self.temp_low_var.get()

            if 'temperature' in self.current_df.columns:
                for idx, temp in self.current_df['temperature'].items():
                    if pd.notna(temp):
                        if temp > temp_high:
                            self.add_alarm(f"高温报警: {temp:.2f}°C > {temp_high}°C (索引: {idx})")
                        elif temp < temp_low:
                            self.add_alarm(f"低温报警: {temp:.2f}°C < {temp_low}°C (索引: {idx})")

            # 检查电压阈值
            voltage_high = self.voltage_high_var.get()
            voltage_low = self.voltage_low_var.get()

            if 'battery_voltage' in self.current_df.columns:
                for idx, voltage in self.current_df['battery_voltage'].items():
                    if pd.notna(voltage):
                        if voltage > voltage_high:
                            self.add_alarm(f"高压报警: {voltage:.2f}V > {voltage_high}V (索引: {idx})")
                        elif voltage < voltage_low:
                            self.add_alarm(f"低压报警: {voltage:.2f}V < {voltage_low}V (索引: {idx})")

            # 显示结果
            if self.alarms:
                self.update_status(f"发现 {len(self.alarms)} 个报警")
                self.log_message(f"⚠️ 发现 {len(self.alarms)} 个报警")
            else:
                self.update_status("未发现报警")
                self.log_message("✅ 未发现报警")

        except Exception as e:
            self.log_error(f"应用阈值检查失败: {e}")

    def add_alarm(self, message):
        """添加报警信息"""
        self.alarms.append(message)
        self.alarm_listbox.insert(tk.END, f"[{len(self.alarms)}] {message}")

        # 如果报警数量过多，只保留最新的100条
        if self.alarm_listbox.size() > 100:
            self.alarm_listbox.delete(0)

    def clear_alarms(self):
        """清除报警"""
        self.alarm_listbox.delete(0, tk.END)
        self.alarms = []
        self.update_status("报警已清除")

    def export_alarms(self):
        """导出报警信息"""
        if not self.alarms:
            messagebox.showwarning("警告", "没有报警信息可导出")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出报警信息",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                ext = Path(file_path).suffix.lower()

                if ext == '.csv':
                    # 导出为CSV
                    alarm_df = pd.DataFrame({'报警信息': self.alarms})
                    alarm_df.to_csv(file_path, index=False, encoding='utf-8')
                else:
                    # 导出为文本
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("卫星遥测数据报警报告\n")
                        f.write("=" * 50 + "\n")
                        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"报警总数: {len(self.alarms)}\n")
                        f.write("=" * 50 + "\n\n")

                        for i, alarm in enumerate(self.alarms, 1):
                            f.write(f"{i}. {alarm}\n")

                self.update_status(f"报警信息已导出到: {Path(file_path).name}")
                self.log_message(f"📤 报警信息已导出")

            except Exception as e:
                self.log_error(f"导出报警信息失败: {e}")

    # =========================== 报告生成方法 ===========================

    def generate_report(self):
        """生成报告"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            report_type = self.report_var.get()
            format_type = self.report_format_var.get()

            self.update_status(f"正在生成{report_type}报告...")

            if report_type == 'cycle':
                cycle_size = self.cycle_size_var.get()
                reports = generate_cycle_report(self.current_df, cycle_size)
                report_text = "周期报告生成完成"

            elif report_type == 'summary':
                summary = create_summary_report(self.current_df)
                report_text = json.dumps(summary, indent=2, ensure_ascii=False, default=str)

            elif report_type == 'comprehensive':
                self.generate_comprehensive_report()
                report_text = self.result_text.get(1.0, tk.END)

            else:
                report_text = f"{report_type}报告功能开发中..."

            # 显示报告
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report_text)

            self.update_status(f"{report_type}报告生成完成")
            self.log_message(f"📋 已生成{report_type}报告")

        except Exception as e:
            self.log_error(f"生成报告失败: {e}")

    def preview_report(self):
        """预览报告"""
        if self.current_df is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        try:
            report_type = self.report_var.get()

            if report_type == 'cycle':
                cycle_size = self.cycle_size_var.get()
                reports = generate_cycle_report(self.current_df, cycle_size)

                # 格式化显示
                preview_text = f"周期报告预览 (周期大小: {cycle_size})\n"
                preview_text += "=" * 60 + "\n\n"

                for i, report in enumerate(reports[:5], 1):  # 只显示前5个周期
                    preview_text += f"周期 {i}:\n"
                    preview_text += report.get('summary', '') + "\n\n"

                if len(reports) > 5:
                    preview_text += f"... 还有 {len(reports) - 5} 个周期\n"

            elif report_type == 'summary':
                summary = create_summary_report(self.current_df)

                # 格式化显示
                preview_text = "汇总报告预览\n"
                preview_text += "=" * 60 + "\n\n"
                preview_text += f"报告生成时间: {summary.get('report_generated', '未知')}\n"
                preview_text += f"总记录数: {summary.get('data_overview', {}).get('total_records', 0)}\n\n"

                # 显示关键指标
                stats = summary.get('statistics_summary', {})
                if stats:
                    preview_text += "关键指标:\n"
                    for param, values in stats.items():
                        preview_text += f"  {param}: {values.get('mean', 0):.2f}\n"
                    preview_text += "\n"

                # 显示报警摘要
                alarms = summary.get('alarms_summary', {})
                if alarms:
                    preview_text += f"报警总数: {alarms.get('total_alarms', 0)}\n"

            else:
                preview_text = f"{report_type}报告预览功能开发中..."

            # 显示预览
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, preview_text)

            self.update_status(f"{report_type}报告预览已生成")

        except Exception as e:
            self.log_error(f"预览报告失败: {e}")

    def export_report(self):
        """导出报告"""
        report_text = self.report_text.get(1.0, tk.END).strip()
        if not report_text:
            messagebox.showwarning("警告", "没有可导出的报告")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出报告",
            defaultextension=".txt",
            filetypes=[
                ("文本文件", "*.txt"),
                ("JSON文件", "*.json"),
                ("HTML文件", "*.html"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            try:
                ext = Path(file_path).suffix.lower()

                if ext == '.json':
                    # 尝试解析为JSON
                    try:
                        report_data = json.loads(report_text)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(report_data, f, indent=2, ensure_ascii=False)
                    except:
                        # 如果不是JSON，保存为文本
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(report_text)

                elif ext == '.html':
                    # 保存为HTML
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>卫星遥测数据报告</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; }}
                            h1 {{ color: #2c3e50; }}
                            pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
                        </style>
                    </head>
                    <body>
                        <h1>卫星遥测数据报告</h1>
                        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <pre>{report_text}</pre>
                    </body>
                    </html>
                    """
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)

                else:
                    # 保存为文本
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report_text)

                self.update_status(f"报告已导出到: {Path(file_path).name}")
                self.log_message(f"📤 报告已导出")

            except Exception as e:
                self.log_error(f"导出报告失败: {e}")

    # =========================== 工具方法 ===========================

    def update_status(self, message):
        """更新状态栏"""
        self.status_bar.config(text=f"状态: {message}")
        self.root.update_idletasks()

    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

        # 限制日志行数
        log_lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(log_lines) > 100:
            self.log_text.delete(1.0, 2.0)

    def log_error(self, message):
        """记录错误消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_entry = f"[{timestamp}] ❌ 错误: {message}\n"

        self.log_text.insert(tk.END, error_entry)
        self.log_text.see(tk.END)

        # 在状态栏也显示错误
        self.update_status(f"错误: {message[:50]}...")

    def show_treeview_context_menu(self, event):
        """显示Treeview右键菜单"""
        try:
            self.tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()

    def copy_selected_row(self):
        """复制选中行"""
        selection = self.data_tree.selection()
        if selection:
            item = self.data_tree.item(selection[0])
            values = item['values']
            text = '\t'.join(str(v) for v in values)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.update_status("已复制选中行数据")

    def export_selected_data(self):
        """导出选中数据"""
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选中数据行")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出选中数据",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 写入表头
                    headers = [self.data_tree.heading(col)['text'] for col in self.data_tree['columns']]
                    f.write(','.join(headers) + '\n')

                    # 写入选中的数据
                    for item_id in selection:
                        item = self.data_tree.item(item_id)
                        values = item['values']
                        f.write(','.join(str(v) for v in values) + '\n')

                self.update_status(f"已导出 {len(selection)} 行数据")
                self.log_message(f"📤 已导出 {len(selection)} 行数据")

            except Exception as e:
                self.log_error(f"导出数据失败: {e}")

    def lighten_color(self, color, factor=0.2):
        """变亮颜色"""
        try:
            # 将颜色从16进制转换为RGB
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

            # 变亮颜色
            light_rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)

            # 转换回16进制
            return f'#{light_rgb[0]:02x}{light_rgb[1]:02x}{light_rgb[2]:02x}'
        except:
            return color

    def on_closing(self):
        """窗口关闭事件处理"""
        if messagebox.askokcancel("退出", "确定要退出系统吗？"):
            self.log_message("🛑 系统正在关闭...")
            self.root.destroy()


def main():
    """主函数"""
    # 创建主窗口
    root = tk.Tk()

    # 设置DPI缩放（在高分辨率显示器上）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    # 创建应用程序
    app = SatelliteTelemetryGUI(root)

    # 运行主循环
    root.mainloop()