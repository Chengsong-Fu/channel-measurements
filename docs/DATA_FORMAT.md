# 数据格式、字段和单位

## 1. 原始信道文件：MATLAB v7.3 / HDF5

八个主采集文件为 MATLAB v7.3 MAT，内部采用 HDF5；Python 使用 `h5py`，MATLAB 使用 `matfile` 或 `load` 读取。单个文件对应一个场景的一种天线批次，包含该批次所有位置和重复采集。辅助的 `campaign_plan.mat`、后处理 MAT 不保证都是 v7.3，不能仅凭 `.mat` 后缀统一交给 `h5py`。

目录内另有 `premerge_positions_10to12_backup.mat` 等原始处理备份，按科学文件完整保留；原始采集目录只索引八个主采集文件，备份不重复计为新增采集。

| 字段 | h5py 中形状 / 数据类型 | 含义与单位 |
|---|---|---|
| `S21` | `(3001, 100, Nraw)`；结构复数 `real` / `imag`，float32 | 复数传输系数，无量纲；顺序为频点、重复、原始位置 |
| `TDR` | `(3001, 100, Nraw)`；float32 | 仪器输出的原始时域值，原样保留；物理显示格式见 `cfg.tdrFormat`，不擅自标为 dB 或功率 |
| `frequencyHz` | `(3001, 1)`；float64 | 6,000,000,000–7,500,000,000 Hz，步长 500,000 Hz |
| `timeSec` | `(3001, 1)`；float64 | TDR 对应的时间轴，秒；应读取文件内的值 |
| `sampleSucceeded` | `(100, Nraw)`；uint8 | S21 采集成功标记，0/1 |
| `tdrSucceeded` | `(100, Nraw)`；uint8 | TDR 获取成功标记，0/1；读取 TDR 时应同时检查 |
| `sampleStartPosixSec` | `(100, Nraw)`；float64 | POSIX 秒时间戳，基准为 UTC；不是北京时间的本地秒数 |
| `sampleDurationSec` | `(100, Nraw)`；float64 | 单次采集耗时，秒 |
| `actualStartIntervalSec` | `(100, Nraw)`；float64 | 实际采集起始间隔，秒 |
| `lastCompletedPosition` / `lastCompletedRepeat` | `(1,1)` | 断点/完成进度，不是数组形状 |
| `createdAt` | MATLAB 字符串 | 创建时间文字，保留源定义 |
| `cfg` | MATLAB struct / HDF5 group | 频率、功率、IF 带宽、重复数及任务/天线等配置 |

`Nraw` 分别为 SC1=17、SC2=12、SC3=17、SC4=10，均含原始位置 1 的校准记录。每个主文件的精确配置见 [campaigns.json](../metadata/campaigns.json)。

常用 `cfg` 字段：`freqStartHz`、`freqStopHz`、`numFreqPoints`、`numRepeatsPerPosition`、`IFBandwidthHz`（Hz）、`sourcePowerdBm`（dBm）、`sampleIntervalSec`（秒）、`positions`、`positionUnit`、`sceneName`、`antennaName`、`taskID`、`enableTDR`、`tdrFormat`、`timeStartSec`、`timeStopSec`。`cfg.positions` 和 `positionUnit` 组合后的历史标签不等于本仓库已校核的几何距离。

本次八个主文件的 `cfg.tdrFormat` 均为 **`MLOG`**，原采集函数将其定义为 dB 幅度显示；示例列仍命名为 `tdr_raw`，不重复取对数。`IFBandwidthHz` 和 `sourcePowerdBm` 等字段若在源文件中为空，则摘要为 JSON `null`，不补造仪器数值。HDF5 中带 `MATLAB_empty=1` 的数据集是 MATLAB 空数组，存储的 `[0,0]` 形状描述不能解释为真实 0 Hz 或 0 dBm。

### Python 数组读取

以下示例读取原始位置索引 4（P03）、第 12 次采集。Python 使用从 0 开始的索引，因此下标是 3 和 11。

```python
import h5py
import numpy as np

with h5py.File("path/to/measurement.mat", "r") as f:
    frequency_hz = f["frequencyHz"][:].reshape(-1)
    value = f["S21"][:, 11, 3]   # [频点, 重复, 原始位置]
    s21 = value["real"].astype(float) + 1j * value["imag"].astype(float)
    succeeded = bool(f["sampleSucceeded"][11, 3])
    tdr_succeeded = bool(f["tdrSucceeded"][11, 3])
    magnitude_db = 20 * np.log10(np.maximum(np.abs(s21), 1e-30))
    phase_deg = np.angle(s21, deg=True)
```

完整可运行的坐标感知导出脚本为 [read_capture.py](../scripts/read_capture.py)。示例 CSV 中幅度采用 `20 log10(|S21|)`，相位为未展开的角度，单位 °；`tdr_raw` 是源数组原值。

### MATLAB 数组读取

MATLAB 原生 MAT 维度与 h5py 显示的 HDF5 维度互为反序：MATLAB `S21` 为 **`[Nraw, 100, 3001]`**，而 h5py 为 `[3001,100,Nraw]`。

```matlab
m = matfile('path/to/measurement.mat');
rawPositionIndex = 4; % P03；校准点是原始位置 1
repeatIndex = 12;
s21 = squeeze(m.S21(rawPositionIndex, repeatIndex, :));
frequencyHz = m.frequencyHz;
frequencyHz = frequencyHz(:);
magnitude_dB = 20 * log10(max(abs(s21), 1e-30));
phase_deg = angle(s21) * 180 / pi;
```

不要将 MATLAB 的索引顺序直接用于 `h5py`，也不要把 P03 误读为原始位置索引 3。

## 2. 原始后处理结果

各批次 `Postprocessing_Results/` 保留源目录与文件字节：

| 文件 / 路径 | 格式 | 内容 |
|---|---|---|
| `repeat_channel_parameters.csv` | CSV，首行为列名 | 每个频带的逐点逐次参数，包括原始位置/重复索引 |
| `channel_parameter_results.mat` | MATLAB MAT | 该频带的处理结果与相关数组；用 MATLAB 检查字段，不能假定与主 MAT 同结构 |
| `campaign_*summary*.csv` | CSV | 大尺度、小尺度、分频带、条件分组与路径损耗拟合汇总 |
| `*position_mapping.csv` / `hall_position_geometry.csv` | CSV | 历史处理的位置映射；若与已核对坐标不同，几何距离以 `metadata/points.csv` 为准 |
| `*.png` | PNG | 源处理绘图，包括有效的小尺度参数图 |
| `campaign_plan.mat` / `postprocessing_plan.mat` | MATLAB MAT | 采集和处理计划 / 配置 |
| `campaign_log.txt` / `*_log.txt` | 文本 | 采集过程日志 |

九个处理频带为：

- `wide_6to7p5`：6–7.5 GHz，全带宽 1.5 GHz。
- `target_6425to7125`：6.425–7.125 GHz，带宽 700 MHz。
- `subband_01_6425to6525MHz` 至 `subband_07_7025to7125MHz`：连续七个 100 MHz 子带。

CSV 字段因结果类型和场景而异；每个 CSV 的完整列名与行数都列在 [result-tables.csv](../metadata/result-tables.csv)，应以实际文件表头为准。常见字段如下：

| 字段 | 含义 |
|---|---|
| `PositionIndex` / `RawPositionIndex` / `RepeatIndex` | 一般为从 1 开始的位置/重复索引；原始位置与场景点位必须通过映射核对 |
| `TaskID` / `SceneName` / `AntennaName` / `ProfileID` | 任务、源场景名、源天线名及频带处理标识 |
| `BandStart_GHz` / `BandStop_GHz` / `CenterFrequency_GHz` | GHz |
| `Bandwidth_MHz` | MHz |
| `PropagationCondition` | LOS / NLOS 的分组标记 |
| `RMSDelaySpread_ns` | RMS 时延扩展，ns |
| `KFactorPDP_dB` | 源算法以 PDP 计算的 K 因子，dB；不额外解释为其他估计方法 |
| `CI_PathLossExponent_n` | CI 路径损耗指数，无量纲 |
| `CI_ShadowSigma_dB` / `FI_ShadowSigma_dB` | 源拟合的阴影衰落标准差，dB |
| `FI_Intercept_dB` / `FI_Slope` | FI 截距与源算法定义的斜率，不与报告表中的不同记号混同 |
| `ABG_Alpha` / `ABG_Beta_dB` / `ABG_Gamma` | ABG 源拟合参数，按源定义使用 |
| `SourceFile` | 生成结果时的原始机器路径；是历史溯源文字，换机后使用清单中的相对路径 |

源 CSV 未重算或重新编码；有些历史中文字段存在乱码，数值和原始字节保留。新生成的 `metadata/` 和 `examples/` CSV 采用 **UTF-8 BOM、逗号分隔**，供 Python/Excel 读取。空字段表示未知/不适用，不能当作 0；源文件出现的 `NaN` 仍按缺失或未定义值处理。

## 3. 仓库目录与坐标 CSV

`metadata/measurements.csv` 每行对应一次原始位置 × 重复采集，并含：

- `scenario`、`scene_name`、`campaign`、`antenna`（`directional` / `omni`）。
- `point`（P01…或 CAL）、`point_role`（measurement / calibration）、`raw_position_index`（从 1 开始）、`original_position_label`。
- `repeat_index`（1–100）、`frequency_start_hz`、`frequency_stop_hz`、`frequency_points`。
- `captured_at_utc`（ISO 8601 UTC）、`succeeded`（0/1）。
- `tx_x_m` / `tx_y_m` / `tx_z_m` 与 `rx_x_m` / `rx_y_m` / `rx_z_m`。
- `distance_m`：三维直线距离；`corridor_distance_m`：有明确资料时的沿走廊距离。
- `horizontal_distance_m`：已知 x/y 计算的平面直线距离；`coordinate_dimension`：`xyz` 或 `xy`，表示坐标依据的维数。校准记录为空。
- `propagation_condition`、`raw_file`（相对仓库根目录的恢复路径）。

`metadata/points.csv` 是不按重复展开的场景测量点映射；校准记录在采集目录中单独标为 CAL。SC4 已补充经两批位置映射验证的二维坐标和 `horizontal_distance_m`，z 与三维 `distance_m` 留空；其坐标来源见 `metadata/sc4-coordinate-source.json`。所有场景的坐标仅适用于明确列出的八个批次。

`metadata/files.csv` 记录 `scenario,campaign,path,size_bytes,sha256`。SHA-256 对应恢复后的源文件内容，不是 ZIP 压缩字节。`metadata/archives.json` 同时记录分卷与合并 ZIP 的散列，采用顺序 `.001,.002,...` 合并。

## 4. 报告结果与后续太赫兹数据

`report/large-scale.json`、`table-*.csv` 与 14 张大尺度 PNG 来源于报告；`report/sc1-layout` 至 `sc4-layout` 的 PNG / SVG 为按核对坐标重绘的四张场景图，替代旧场景图。统一汇总表、历史分批次拟合和源后处理结果分别保存。报告空白参数保持空白；没有混入报告中不正确的小尺度图。

天线方向图、原始增益结点、沿用的处理频率映射及 3,001 点插值表位于 `antenna/`，数据来源及数值含义见 [天线说明](../antenna/README.md)。

太赫兹文件尚未提供，暂不约定数组维度、频率范围、天线、场景或数据格式。未来接入时将单独建立版本、字段字典、清单和读取器。
