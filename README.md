# CarPlay Steering-Wheel Controls

A small, dependency-free Java reference implementation of context-aware steering-wheel controls for CarPlay integrations.

用于 CarPlay 接入的方向盘按键映射逻辑：只包含独立状态机、测试和适配说明，不包含原厂固件、反编译类、车机备份、账号或设备数据。MIT 许可证。

**这不是可直接刷入车机的安装包。** 硬件事件、原厂服务调用和安全恢复由适配器实现；本仓库本身不会连接、重启或修改任何设备。

## 功能

| 状态 | 星号 | 音量滚轮按下 | 语音键 | 导航语音键 |
|---|---|---|---|---|
| CarPlay 音乐页面 | 下一首 | 暂停／播放 | Siri | 上一首 |
| 已连接，处于其他页面 | 交回原厂 | 交回原厂 | 切回 CarPlay | 交回原厂 |
| 未连接 | 交回原厂 | 交回原厂 | 打开设备选择 | 交回原厂 |
| 来电响铃，任意页面 | 接听 | 不操作音乐 | 切回 CarPlay | 拒接按压序列 |
| 通话中，任意页面 | 不操作音乐 | 不操作音乐 | 切回 CarPlay | 挂断 |

- 只接管明确标记为方向盘来源的事件，中央控制台事件返回给原厂。
- 短按通常在松开时触发；长按、双击不额外执行短按动作。
- Siri 使用完整的“按下 → 长按检测 → 松开”序列，异常路径也释放。
- 播放中显式发送暂停，暂停时显式发送播放；暂停分支不重新请求音乐音源。
- 拒接保持时间默认 1500 ms，异步释放，不阻塞输入线程；通话挂断不增加这段延时。
- 断连会取消按键捕获并使旧延时任务失效，避免旧任务释放新通话的按键。

## 连接时播放状态保护

`PlaybackPolicy` 在连接初期阻止未经用户操作的播放／播放暂停命令。首次状态未知或已暂停时，不主动播放；手机明确上报正在播放后放行。手动音乐控制也会解除保护。

保护本身从不发送暂停命令，避免为了阻止续播而暂停本来正在播放的手机。`ButtonGate` 成对处理按下／松开，状态回调恰好发生在两者之间也不会漏发孤立松开事件。

边界：它只能拦截经过适配器的车机命令，无法读取手机连接前的历史状态；若手机 App 自行续播，或控制绕过该边界，不能保证阻止。适配器必须把真实连接／重连事件传入，不能只在程序启动时调用一次。

## 运行测试

需要 JDK 17 或更新版本，无第三方依赖：

```sh
sh test.sh
```

测试只使用合成事件、虚拟时钟、假调度器和内存记录器，不需要固件、手机、网络、车辆或个人数据。

源文件保持简单的 Java 写法，但脚本生成的是桌面测试用 Java 8 字节码。**不能把该输出直接装进旧嵌入式 JVM。** 如需集成，必须针对实际运行时重新编译和验证。

## 接入

```java
SteeringWheelControls controls = new SteeringWheelControls(port, clock, scheduler);
controls.updateConnection(connected, carPlayPage);
controls.updatePlayback(playbackState, valid);
controls.updateCalls(callStatuses, callDirections, valid);
boolean consumed = controls.onKey(logicalKey, event, steeringWheelSource);
```

只有 `consumed == true` 时才阻止原厂继续处理。适配器还应以 `setInputAllowed` 反映电源／待机和其他输入限制。

详细契约见 [INTEGRATION.md](INTEGRATION.md)。这个例子中的变量来自调用方，不是内置设备连接或全局服务。

## 实现与验证范围

这是从既有按键功能中重新整理的独立参考库，不是已部署厂商覆盖类的逐字开源副本。关键行为在合成测试中验证；拒接的保持时间、来电枚举、多通话和具体应用兼容性仍需要目标适配器实测。

不宣称支持全部车机或全部固件，也不宣称自动拒接已在所有目标上验证。参数和接口语义见接入文档；不自动安装、配对、扫描或开启远程服务。

## 隐私和发布范围

本仓库不采集、不存储、不上传遥测数据。电话分支只需要状态与方向，不需要号码、联系人或通话标识。源文件不包含私人固件、日志、截图、访问凭据、硬件标识或本地路径。

- [PRIVACY.md](PRIVACY.md)：发布内容边界。
- [SECURITY.md](SECURITY.md)：缺陷报告与日志最小化。
- [LICENSE](LICENSE)：仅适用于这里原创实现的代码和文档。

CarPlay 为其权利人的商标。本项目不隶属于设备制造商或平台提供方。
