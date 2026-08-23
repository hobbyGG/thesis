# Pi 4 + SD 卡直存采集方案

本文档采用唯一硬件路线：

```text
Raspberry Pi 4 Model B 直接本地记录到 microSD 卡
```

本方案不再考虑 USB SSD 作为主数据盘，也不把无线链路作为实时数据传输通道。桥上端或实验台端由 Raspberry Pi 4 Model B 控制采集、保存数据、记录日志；地面 PC 或笔记本只负责远程启动、停止、查看状态和实验后拷贝数据。

## 1. 方案定位

目标是搭建一套最轻量、最少线缆、最容易复现实验的采集节点：

```text
IWR1843BOOST 板端固件 -> 选定目标复数 I/Q 或 wrapped phase -> Raspberry Pi 4 -> microSD
ADXL355 -> SPI -> Raspberry Pi 4 -> microSD
Raspberry Pi 4 -> Wi-Fi/SSH -> PC 控制与预览
```

本方案默认不采集长时间全量 DCA1000 原始 ADC 数据，但这不等于直接使用普通点云输出。位移相位算法至少需要每帧目标单元的复数 I/Q 或由板端固件计算出的 wrapped phase。采集内容应控制在 Pi 4 和 microSD 能稳定写入的范围内，重点保存算法需要的雷达相位/目标特征、加速度数据、同步日志和实验元数据。

适用场景：

- 现场或实验室短到中等时长采集；
- 只需要保存雷达目标特征、wrapped phase、幅值、SNR、加速度和同步信息；
- 需要设备轻、部署快、线缆少；
- 需要后续离线验证多目标选择、相位解缠和融合算法。

不适用场景：

- 长时间连续保存 DCA1000 原始 ADC；
- 高速大吞吐雷达 cube 全量落盘；
- 对写盘零丢包有强工程保证的正式长期监测。

## 2. 硬件组成

| 类别 | 推荐硬件 | 用途 |
|---|---|---|
| 主控与存储 | Raspberry Pi 4 Model B，建议 4 GB | 控制采集、写 microSD、远程通信 |
| 系统与数据卡 | 高耐久 microSD，A2/U3/V30，建议 256 GB 或 512 GB | 系统盘和实验数据盘 |
| 毫米波雷达 | TI IWR1843BOOST | 输出雷达相位、目标和距离信息 |
| 加速度计 | ADXL355 模块/评估板 | 三轴低噪声加速度采集 |
| 可选协处理器 | STM32 / Teensy 4.1 / RP2040 | 更稳定的 ADXL355 采样和硬件时间戳 |
| 网络 | Pi 4 自带 Wi-Fi 或小型无线 AP | SSH 控制、状态查看、低速预览 |
| 电源 | 稳定 5.1 V 3 A 供电 | 避免 Pi 4 欠压和写盘异常 |
| 散热 | Pi 4 散热片或带风扇外壳 | 避免长时间采集降频 |
| 安装 | 刚性安装板、防护外壳、短线缆 | 雷达和加速度计共址固定 |

microSD 建议使用高耐久卡，而不是普通消费级低速卡。优先选择标称适合视频连续写入或监控记录的型号，并在正式实验前做持续写入测试。

## 3. 数据链路

### 3.1 雷达链路

推荐雷达链路为：

```text
IWR1843BOOST 板端处理 -> 目标复数 I/Q 或 wrapped phase -> Raspberry Pi 4 -> microSD
```

保存内容建议包括：

- `frame_id`
- `timestamp_pi`
- `target_id`
- `range_bin`
- `range_m`
- `iq_real`
- `iq_imag`
- `wrapped_phase_rad`
- `amplitude`
- `snr_db`
- `angle_or_beta_preview`
- `quality_flag`

也可以保存少量调试用中间量，例如候选 target 数量、range profile 局部峰值、目标健康度等。但不建议把全量 ADC 或完整 range-angle cube 长时间写入 microSD。

需要明确三种数据层级：

| 数据层级 | 是否满足相位位移算法 | 是否符合本方案 |
|---|---|---|
| 普通点云坐标、速度、SNR | 不满足。点云通常不保留可连续跟踪的复数相位 | 不作为主数据 |
| 选定 range/range-angle 单元的复数 I/Q 或 wrapped phase | 满足。可用于相位解缠和位移恢复 | 本方案主数据 |
| DCA1000 原始 ADC 全量数据 | 满足且最底层，但数据量大 | 仅作为研发验证，不作为 SD 卡直存主方案 |

因此，不买 DCA1000 的前提是：需要修改或复用 IWR1843 板端处理程序，让它在 UART/USB 等链路中输出选定目标的复数 I/Q 或 wrapped phase。若只能使用官方普通点云 demo，无法直接支撑本文的原始相位算法。

### 3.2 加速度链路

推荐加速度链路为：

```text
ADXL355 -> SPI -> Raspberry Pi 4 -> microSD
```

`accel.csv` 建议字段：

```text
timestamp_pi,sample_id,ax,ay,az,temp,range_g,odr_hz
```

如果 Pi 4 直接读取 ADXL355 的实时性不够稳定，可以加一个 MCU：

```text
ADXL355 -> SPI -> MCU -> UART/USB -> Raspberry Pi 4 -> microSD
```

MCU 只负责稳定采样和打时间戳，Pi 4 仍负责统一落盘和实验管理。

## 4. 实验目录结构

每次实验建立独立目录：

```text
experiments/<experiment_id>/
  radar_features.csv
  accel.csv
  sync_log.csv
  preview.csv
  node_status.csv
  capture_log.txt
  metadata.json
```

文件含义：

| 文件 | 内容 |
|---|---|
| `radar_features.csv` | 雷达每帧目标、相位、幅值、SNR 和质量指标 |
| `accel.csv` | ADXL355 全采样率三轴加速度 |
| `sync_log.csv` | 雷达帧、加速度样本、触发状态和时间戳对应关系 |
| `preview.csv` | 降采样预览数据，用于远程查看 |
| `node_status.csv` | CPU 温度、欠压状态、剩余空间、写盘速率 |
| `capture_log.txt` | 启停、错误、丢样、异常事件日志 |
| `metadata.json` | 硬件型号、安装方式、采样率、实验说明 |

## 5. 同步方案

最低要求是所有数据都带 Pi 4 时间戳。推荐进一步保存雷达帧号和加速度样本号的对应关系。

`sync_log.csv` 建议字段：

```text
timestamp_pi,radar_frame_id,accel_sample_id,trigger_state,event
```

同步优先级：

1. **硬件触发或帧同步**  
   如果 IWR1843 能输出 frame sync 或可用 GPIO 触发信号，接入 Pi 4 或 MCU，记录雷达帧与加速度样本的对应关系。

2. **统一进程时间戳**  
   Pi 4 同时接收雷达特征和 ADXL355 数据时，统一使用 Pi 系统时间戳。

3. **离线细对齐**  
   后处理阶段再用加速度短窗积分和雷达相位运动代理做小范围时间偏移估计。

正式实验应至少做到第 2 项；如果要做定量精度评价，建议做到第 1 项。

## 6. 远程控制

无线链路只承担控制、状态和低速预览：

```text
PC -> SSH/HTTP/WebSocket -> Raspberry Pi 4
Raspberry Pi 4 -> status/preview -> PC
Raspberry Pi 4 -> microSD -> 完整数据本地保存
```

建议命令：

- `start <experiment_id>`：开始采集；
- `stop`：停止采集并 flush 文件；
- `status`：查看温度、欠压、剩余空间、采样率；
- `preview`：返回低速预览；
- `package`：实验结束后打包本次目录。

实验结束后可以通过 SFTP/rsync 下载数据，也可以关机后直接取出 microSD 读卡。

## 7. SD 卡写入边界

microSD 是本方案的关键风险点。必须控制数据量，并在实验前做写入测试。

建议边界：

| 数据类型 | 是否建议写入 microSD | 说明 |
|---|---|---|
| ADXL355 100-1000 Hz CSV | 建议 | 数据量小 |
| 雷达每帧目标特征 CSV | 建议 | 适合本方案 |
| 低速 preview | 建议 | 用于远程查看 |
| 状态日志和元数据 | 建议 | 必须保存 |
| 短时少量 ADC 片段 | 谨慎 | 只用于调试 |
| 长时间 DCA1000 原始 ADC | 不建议 | 写入压力和丢包风险高 |
| 完整 range-angle cube | 不建议 | 数据量过大 |

正式采集前应做三项检查：

1. 连续写入压力测试，时间不少于计划单次实验时长；
2. 采集过程中监测 Pi 4 欠压、CPU 温度和剩余空间；
3. 每次写入采用分段 flush，避免异常断电导致整段数据损坏。

## 8. 推荐实验流程

1. 插入高耐久 microSD，确认剩余空间。
2. 启动 Pi 4，连接 PC 到同一 Wi-Fi 或直连热点。
3. 通过 SSH 检查雷达、ADXL355 和采集程序状态。
4. 创建 `experiment_id`，写入 `metadata.json`。
5. 启动采集，生成 `radar_features.csv`、`accel.csv` 和 `sync_log.csv`。
6. 采集期间只回传低速 `preview` 和 `status`。
7. 停止采集后关闭文件并校验行数、时长、丢样和剩余空间。
8. 下载实验目录或取出 microSD。
9. 在 PC 上进行离线融合处理和精度评价。

## 9. 最终推荐

唯一推荐采购和搭建路线：

```text
Raspberry Pi 4 Model B 4GB
高耐久 microSD 256GB 或 512GB
TI IWR1843BOOST
ADXL355 模块/评估板
可选 STM32 / Teensy 4.1 / RP2040
Pi 4 散热片或带风扇外壳
稳定 5.1V 3A 电源
小型 Wi-Fi AP 或使用 Pi 4 自带 Wi-Fi
刚性安装板和防护外壳
```

本方案的核心原则是：

```text
只把必要的雷达特征、加速度、同步和日志写入 SD 卡；
不把 SD 卡当作长时间原始 ADC 高速数据盘。
```
