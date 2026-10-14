# 结果分析工具

这些脚本只服务于当前 A20 仿真和算法结果，不参与采集或估计主链。

生成 A20 响应图：

```bash
python3 tool/simulate_a20_response.py
```

查看算法结果：

```bash
python3 tool/plot_algorithm_results.py \
  --result /tmp/algorithm-result.npz
```

`plot_iq_mmvib_style.py` 和 `plot_iq_snr.py` 用于检查 IQ 轨迹与噪声敏感性；
它们读取输入或生成独立图，不改变 `system/algorithm/` 的估计路径。
