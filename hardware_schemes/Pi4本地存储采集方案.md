# Pi 4 本地统一存储与采集方案

本文档规定实验室和现场的唯一采集方式：Raspberry Pi 4 Model B 同时采集 IWR1843BOOST/DCA1000EVM 雷达原始数据和 ADXL355 加速度数据，在 Pi 本地统一时间戳、落盘和组织实验目录。

## 1. 唯一系统拓扑

```text
电脑 ──Wi-Fi / SSH──→ Raspberry Pi 4
                         ├──SPI + DRDY──→ ADXL355
                         ├──USB────────→ IWR1843BOOST
                         └──Ethernet────→ DCA1000EVM

IWR1843BOOST ←─60-pin HD / LVDS─→ DCA1000EVM
```

- USB 链路用于 Pi 配置和控制 IWR1843BOOST。
- 60-pin HD/LVDS 链路将雷达原始 ADC 数据送到 DCA1000EVM。
- Pi 有线网口直连 DCA1000EVM，接收 UDP 原始数据。
- Pi 通过 SPI 读取 ADXL355，通过 DRDY GPIO 记录样本时间。
- Pi Wi-Fi 只用于 SSH 控制、状态查看和采后拷贝，不承载实时原始 ADC 数据。

## 2. Pi 本地存储

Pi 4 是所有采集数据的首次落盘点。系统盘可使用高耐久 microSD；DCA1000 原始数据的正式采集优先使用 Pi USB 3 高速 SSD，并必须在实验前完成端到端持续写入压力测试。

| 存储内容 | 保存位置 | 要求 |
|---|---|---|
| DCA1000 PCAP/原始 ADC | Pi 本地实验目录 | 持续写入不丢包，优先 SSD |
| ADXL355 原始样本 | 同一 Pi 实验目录 | 二进制定长记录，保存 DRDY 时间戳 |
| 雷达配置和 DCA 配置 | 同一 Pi 实验目录 | 采集时使用的实际版本 |
| 同步事件 | 同一 Pi 实验目录 | 单调时钟、触发号、帧号和样本号 |
| 健康与采集日志 | 同一 Pi 实验目录 | 欠压、温度、剩余空间、丢包和漏样 |

未完成落盘和完整性校验前，不依赖电脑端保存任何唯一副本。

## 3. 雷达采集链路

```text
Pi USB → IWR1843BOOST 配置/控制
IWR1843BOOST → 60-pin HD/LVDS → DCA1000EVM
DCA1000EVM → Ethernet/UDP → Pi 本地 PCAP
```

Pi 本地程序负责：

1. 通过稳定的 `/dev/serial/by-id/` 路径识别 IWR1843BOOST 的控制串口。
2. 配置 DCA1000EVM 并启动 Pi 本地抓包。
3. 下发已归档的雷达配置。
4. 在硬件触发就绪后开始有限帧采集。
5. 根据 DCA 包序号和字节计数检测丢包。
6. 在 Pi 上解码或封存 PCAP，并将雷达帧数与触发数对照。

PCAP 中的网络包到达时间不是雷达帧开始时间，不用它代替硬件触发时间。

## 4. ADXL355 采集链路

```text
ADXL355 → SPI → Pi 4
ADXL355 DRDY → Pi GPIO 中断
```

Pi 直接采集 ADXL355，不在主方案中增加 MCU 或第二台采集器。每个样本至少记录：

```text
sample_id, drdy_timestamp_ns, read_complete_timestamp_ns,
x_raw, y_raw, z_raw, fifo_state, error_flags
```

温度通道按较低频率单独记录，不放进每个 DRDY 的实时 SPI 热路径。

采集程序需要检查设备 ID、ODR、量程、时间戳单调性、样本序号连续性和 FIFO 溢出。

## 5. 同步方案

定量融合使用 Pi 作为统一时基和触发协调者：

```text
Pi GPIO OUT → IWR1843BOOST SYNC_IN
Pi 记录每个触发边沿的 CLOCK_MONOTONIC 时间
Pi GPIO/DRDY 记录每个 ADXL355 样本的同类时间
```

一次采集的时序为：

```text
预检查
→ 创建 Pi 本地实验目录
→ 启动 Pi 本地 DCA 抓包并进入 RECORD
→ 启动 ADXL355 并预采集 1–2 s
→ 配置 IWR1843BOOST 进入硬件触发等待
→ Pi 产生 N 个帧触发并记录时间
→ 停止触发，ADXL355 继续后采集 1–2 s
→ 停止所有采集并 flush/fsync
→ 校验数据完整性
→ 封存实验目录
```

雷达第 `i` 帧对应第 `i` 个触发边沿，雷达帧时间轴由 Pi 的真实触发记录生成，不使用 `frame_index × nominal_period` 替代。

该同步线是目标实现，正式接线和采集前必须先用当前 IWR1843 固件验证 `triggerSelect=2`，并核对 IWR1843BOOST 与 DCA1000EVM 连接时的 `SYNC_IN` 路由和板卡版本；验证完成前不能把硬件触发视为已可用功能。

## 6. 实验目录

```text
captures/<experiment_id>/
  radar/
    dca.pcap
    radar.cfg
    dca.json
    algorithm_input/
      adc_cube.npy
      frame_times_s.npy
      manifest.json
  adxl355/
    samples_raw.bin
    samples_raw.npy
    acceleration_mps2.npy
    sample_times_s.npy
    manifest.json
  sync/
    radar_trigger_times_ns.npy
    sync.json
  status/
    capture.log
    health.json
  metadata.json
```

Pi 本地协调程序创建并拥有该目录的完整生命周期。各子程序不在电脑上各自创建实验副本，也不由电脑事后拼接雷达和加速度原始文件。

## 7. 完整性判定

以下任一条件出现时，实验必须标记为不完整，不静默插值或修复：

- DCA1000 包序号或字节计数不连续；
- 触发数与解码雷达帧数不一致；
- ADXL355 样本时间戳不单调或出现超限长间隔；
- ADXL355 FIFO 溢出或设备中途复位；
- Pi 欠压、存储写满、文件未正常关闭或必需元数据缺失。

## 8. 电脑端边界

```text
电脑 → Wi-Fi/SSH → Pi 本地协调程序
Pi 封存实验目录 → scp/rsync → 电脑离线副本
```

电脑只负责 SSH 命令、状态观察、采后拷贝和离线处理。电脑不连接传感器，不参与采集、计时、实验目录创建或原始文件组织。

## 9. 上线前压测

1. 在 Pi 上以目标雷达配置运行不少于单次正式实验时长的 DCA1000 接收与写盘测试。
2. 同时运行 ADXL355 目标 ODR，检查调度负载下的漏样和时间戳抖动。
3. 记录 Pi CPU 温度、欠压、内存、网口丢包、磁盘写入延迟和剩余空间。
4. 模拟 SSH 断开，确认 Pi 本地采集不受影响，仍能按预设时长安全收尾。
5. 通过已封存的 Pi 目录重建离线输入，确认不需要从电脑端补充任何采集期间文件。
