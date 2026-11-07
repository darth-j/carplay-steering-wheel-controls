<!-- SPDX-License-Identifier: GPL-3.0-only; Copyright (C) 2026 Skywalker (darth-j) -->

# Compatibility and reference platform

## English

### Reference integration baseline

The mapping behavior was developed and evaluated in a separate, non-distributed adapter on the following platform. **This is a reference integration baseline, not a ready-to-install compatibility guarantee for the portable library.**

| Item | Reference baseline |
|---|---|
| Vehicle model | Audi A6 allroad, C7.5 generation, model year 2017 |
| Infotainment family | MIB2 High / Harman MHI2 |
| Firmware family | AU57x, Chinese-region software |
| Full software train | `MHI2_CN_AU57x_K1006_2` |
| MU software | `1005` / `MU1005` |
| Embedded runtime | QNX 6.5 ARM; IBM J9 2.3 Foundation |
| Prerequisite | CarPlay is already activated and works through the existing connection |

The public repository contains an independently organized logic library and synthetic tests. The manufacturer adapter, proprietary dependencies and target-compatible installation payload are **not distributed**. Even on the exact reference baseline, the default Java 8 build output cannot simply be copied into the embedded JVM.

### Validation scope

The separate reference adapter has device-test records for next/previous track, roller pause/resume, Siri recognition and execution, incoming-call answer, active-call hangup, and the two connection/playback-state scenarios described in the README.

A physical long hold was observed to reject an incoming call. The later automatic minimum-hold implementation passed an isolated timing test, but its final short-press hardware rejection test was not completed. **Do not label automatic rejection as fully hardware-validated.**

The extracted public library is validated by synthetic tests. It is not the exact firmware overlay deployed during those hardware tests. No general phone, operating-system or navigation/music-application compatibility matrix is claimed.

### Other models and firmware

| Configuration | Status |
|---|---|
| Exact reference baseline above | Mapping reference only; still requires an adapter and target validation |
| Other A6 C7/C7.5 configurations or model years | Not verified; the same dashboard or button layout does not establish compatibility |
| Other AU57x software trains, regions or MU versions | Not verified; do not reuse integration details solely because the firmware-family name matches |
| Other models using MHI2 | Not verified; physical events, source IDs, service interfaces and state models must be checked |
| MHI2Q, MH2p, MIB3 and other infotainment families | Different integration targets; no compatible firmware installer is provided |
| Aftermarket Android or other CarPlay receivers | Require their own adapter; no device support is claimed |

The portable mapping concepts may be reusable. That is different from supporting an existing device-specific binary, loader or flashing procedure.

### How to check your software

Read the normal infotainment version-information page, typically **MENU → Setup / Settings → Version information**. Record the full software train and MU version locally. Menu wording and MU visibility vary; use an existing read-only diagnostic method if the MU value is not shown.

Do not confuse the navigation database/map year with the infotainment firmware or MU software version. A matching model name is not enough; validate the runtime, firmware interfaces, physical input sources, CarPlay availability and rollback path.

**Do not upgrade, downgrade or cross-flash firmware just to match this document.** Firmware work carries a bricking risk; test cautiously and retain a verified recovery method. See [DEPLOYMENT.md](DEPLOYMENT.md).

Only generic model, platform and software-version information is listed here. No vehicle identifier, serial number, hardware fingerprint, personal account or diagnostic endpoint is published.

---

## 中文

### 参考适配平台

以下是独立、未随仓库分发的适配器所依据的平台。**它是已有集成记录的参考基线，不代表本仓库的逻辑库可直接在该平台安装。**

| 项目 | 参考范围 |
|---|---|
| 车型 | 奥迪 A6 allroad，C7.5，2017 年款 |
| 车机平台 | MIB2 High / Harman MHI2 |
| 固件系列 | AU57x，中国区域软件 |
| 完整软件版本 | `MHI2_CN_AU57x_K1006_2` |
| MU 软件版本 | `1005` / `MU1005` |
| 运行环境 | QNX 6.5 ARM；IBM J9 2.3 Foundation |
| 前提 | 原有 CarPlay 已激活，且原连接方式正常工作 |

公开仓库仅包含重新整理的独立逻辑库及合成测试，**不包含原厂适配器、专有依赖或目标设备安装包**。即使车型和固件与上表完全一致，也不能把默认 Java 8 构建产物直接复制进旧车机 JVM。

### 已有测试范围

独立参考适配器已有实机记录的功能包括：上一首／下一首、滚轮暂停／恢复、Siri 识别执行、来电接听、通话后挂断，以及 README 中的两种连接播放状态场景。

来电时物理长按曾验证可拒接；后续自动补足保持时间的实现通过了独立时序测试，但未完成最终的短按拒接实机确认，**不能写成自动拒接已全面通过实测**。

公开逻辑库本身通过的是合成测试，并非上述实测过程中部署的原厂覆盖类原样副本。没有对全部手机、系统版本和音乐／导航 App 作兼容性承诺。

### 其他车型、版本和平台

| 范围 | 状态 |
|---|---|
| 上述完整参考配置 | 作为映射参考，仍需适配器和目标验证 |
| 其他 A6 C7/C7.5 配置或年款 | 未验证；外观或按键布局相同不代表兼容 |
| 其他 AU57x 固件、区域或 MU 版本 | 未验证；不能只凭系列名称复用适配细节 |
| 使用 MHI2 的其他车型 | 未验证；需重新核对事件来源、服务接口和状态模型 |
| MHI2Q、MH2p、MIB3 等平台 | 属于不同适配目标，不提供兼容刷机包 |
| 后装安卓或其他 CarPlay 接收设备 | 需要自己的适配器，不宣称支持 |

“逻辑可能复用”与“现成二进制、启动器或刷机步骤可以通用”是两回事。

### 查看车机版本

在正常车机界面进入 **MENU → Setup／设置 → 版本信息**，在本地核对完整软件版本和 MU 版本。不同界面的菜单名称、MU 展示位置可能不同；没有显示时，应使用已有的只读诊断方式确认。

不要把导航地图数据库的年份或版本当成车机固件版本。车型一致仍不足以确定兼容，还需核对运行环境、服务接口、物理按键来源、原有 CarPlay 状态和恢复方法。

**不要为了匹配本说明而升级、降级或跨平台刷写固件。刷机有风险，测试需谨慎。** 部署和恢复流程见 [DEPLOYMENT.md](DEPLOYMENT.md)。

本页仅公开通用车型、平台和软件版本，不公开车辆识别码、序列号、硬件指纹、个人账号或诊断地址。
