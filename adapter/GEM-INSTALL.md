<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Reference adapter: build and GEM installation

## English

**Firmware modification can brick a head unit. Test cautiously, while parked with stable power and an independent recovery method.** The adapter supports only `MHI2_CN_AU57x_K1006_2 / MU1005`. A matching model name is not sufficient. The new public installer has automated isolation tests but has not been live-tested; the generated class payload is checked against the independently device-evaluated reference classes. Do not confuse those two claims.

### Build your package

Use your own legally obtained original `lsd.jar` from the exact supported firmware. Do not use an already modified dependency JAR. Provide the matching original `lsd.jxe` as well. Only its checksum enters your local SD package; the file itself is not copied. The installer compares the running ROM to that locally supplied backup. Keep both inputs outside the public repository. If starting from an original `lsd.jxe`, tools such as [lsdtool](https://github.com/JeniCzech92/lsdtool) describe local conversion; this project does not distribute a converter, OEM runtime or its dependencies. Conversion output must match the pinned class fingerprints; a mismatch stops the build.

Local prerequisites: Python 3, a desktop Java runtime, CFR 0.152, Eclipse ECJ 4.6.1 and a locally supplied compatible Java runtime/boot dependency JAR. CFR and ECJ are fingerprint-checked. The builder does not download or install tools. Compiler/runtime/OEM dependencies are not uploaded with the project.

```sh
python3 adapter/build_gem.py \
  --lsd-jar /path/to/original/lsd.jar \
  --jxe-file /path/to/original/lsd.jxe \
  --cfr-jar /path/to/cfr-0.152.jar \
  --ecj-jar /path/to/ecj-4.6.1.jar \
  --boot-jar /path/to/local/runtime.jar
```

The builder canonicalizes three source files with CFR, applies exact patches, compiles them with the two original project helpers and refuses output unless **all seven resulting class fingerprints** match the reference. It does not copy the original JAR or generated OEM source into the release directory. Dependency or source mismatches are not a reason to remove the guards.

Output is an uncompressed `dist/gem/` directory, including a complete `mod/` tree and the generated payload. Nothing from your private backup directory should be copied to the SD card except the generated output.

### Install through GEM

1. Keep a known-good backup and working management access. Use an existing functioning M.I.B SD card; do not format it or delete `apps`, `config` or `backup`.
2. Copy the generated `dist/gem/mod` to the SD root. If replacing `/mod/command.sh`, back up your previous entry locally first. Never create `mod/mod` or a renamed `mod 2` tree. SD1 is preferred; SD2 is supported by the wrapper.
3. Leave `mod/steering-controls/action.txt` as **`install-once`** for the first run. Use LF line endings.
4. GEM → m.i.b → advanced_settings → run_individual_script → **Run individual script**.
5. Only **`INSTALL VERIFIED: install-once`** means the installer verified the writes. An outer “it is all done” is not success. A STOP means stop and preserve the complete message.
6. Restart manually only when safe. The one-boot loader restores and verifies the original startup file before loading the test. After a further restart it uses the original loading path.
7. Validate music, Siri execution, console passthrough, call controls, connection-state playback and recovery. Short automatic rejection and wider device combinations still need target testing.
8. To make the same payload permanent after a successful temporary test, edit `action.txt` to **`install-permanent`**, run the same GEM entry, require **`INSTALL VERIFIED: install-permanent`**, then coordinate a restart. No SD is required for subsequent permanent boots.

The package refuses foreign/pre-existing loaders, including earlier private project loaders. Do not overwrite them. Restore/uninstall such a loader through its own verified procedure first. The public installer is not an automatic migration tool for an already modified head unit.

### Uninstall and recovery

Set `action.txt` to **`uninstall`** and run the same GEM entry. Require **`UNINSTALL VERIFIED`** before a coordinated restart. It restores the per-unit original startup and removes only the checksummed JAR owned by this installer; the original backup and checksum are retained.

Backups remain under the head unit's `eso/hmi/lsd` directory as `lsd.sh.sww-original` and its `.sha1` record. These files may contain unit-specific startup data and must never be published. The JAR is `jars/SteeringWheelCarPlayControls.jar`.

The bypass flag is `sww-controls.disabled` in that same startup directory. The loader skips the overlay when the flag exists. Creating it requires a working management channel and the platform's normal writable/read-only handling; do not guess mount commands.

If an installation failure prints **`RESTORE VERIFIED`**, writes were rolled back to the prior startup. If it prints **`RECOVERY FAILED`**, or restoration/read-only status cannot be verified, do not repeatedly reboot or reinstall; preserve the SD card and use independent recovery. One-boot fallback depends on the actual restore succeeding, not merely the presence of a backup file. No script automatically reboots.

## 中文

**修改固件有变砖风险，测试需谨慎。请驻车、稳定供电并保留独立恢复方法。** 仅支持 `MHI2_CN_AU57x_K1006_2 / MU1005`。公开安装器目前只做了隔离自动测试，尚未实车验证；生成的七个类会与已有独立实车适配版本逐字节核对。不能把“类来自已测试版本”说成“新安装器已实测”。

### 构建

操作者需提供自己合法取得、版本完全匹配且未修改的原厂 `lsd.jar`，并准备本地 CFR 0.152、ECJ 4.6.1、Java 运行时依赖 JAR、桌面 Java 和 Python 3。原始 `lsd.jxe` 可参考 lsdtool 的本地转换说明。本项目不分发原厂依赖或转换工具，不自动下载任何工具。

运行上面的 `python3 adapter/build_gem.py` 命令并将五个 `/path/to/...` 替换为自己的本地文件。还需提供匹配的原始 `lsd.jxe`，只把其摘要写入本地安装包，不复制 JXE 本体；安装器会核对车机运行的 ROM 是否与自己的原始备份一致。构建器会核对工具及原厂类指纹、反编译、严格应用三个修改补丁，再编译并核对全部七个覆盖类；任何不符都会停止，不能为了绕过错误而删除校验。

成功生成的是无需解压的 `dist/gem/` 完整目录，里面的 `mod/` 已有安装脚本及负载。不应把整个原厂备份或依赖目录放上 SD 卡。

### GEM 安装

1. 使用现有正常的 M.I.B SD 卡，保留 `apps`、`config`、`backup`，不要格式化。覆盖旧 `/mod/command.sh` 前在本地保留原入口。
2. 将生成的 `dist/gem/mod` 放在 SD 根目录，不要出现 `mod/mod` 或带 `2` 后缀的目录；优先 SD1。
3. 首次保持 `mod/steering-controls/action.txt` 内容为 **`install-once`**。
4. GEM → m.i.b → advanced_settings → run_individual_script → **Run individual script**。
5. 只有看到 **`INSTALL VERIFIED: install-once`** 才代表写入校验通过，之后在安全条件下手动重启。外层 `it is all done` 不代表成功。
6. 一次启动加载器会先恢复并核对原启动文件，再载入测试；进一步重启后使用原加载方式。须验证音乐、Siri 执行、中央控制台原厂行为、电话、连接播放状态和恢复。
7. 测试通过后，把 `action.txt` 改为 **`install-permanent`**，再运行同一入口；看到 **`INSTALL VERIFIED: install-permanent`** 后协调重启，后续永久加载不依赖 SD。

已有其他加载器（包括早先私有版本）会被拒绝，必须先用原加载器自己的恢复流程卸载，不能硬覆盖。不同版本的本安装器负载也应先卸载再装，不自动升级未知状态。

### 卸载与恢复

把 `action.txt` 改为 **`uninstall`**，运行同一 GEM 入口；看到 **`UNINSTALL VERIFIED`** 后再安全重启。只移除当前安装器校验确认属于自己的 JAR，并保留原始启动备份及摘要。

本机备份是启动目录中的 `lsd.sh.sww-original` 及其 `.sha1`，可能包含本机启动信息，不能公开。负载名为 `jars/SteeringWheelCarPlayControls.jar`。同目录的 `sww-controls.disabled` 标记可在有管理通道时用于跳过加载，具体读写挂载操作必须按该平台既有恢复方式执行。

安装失败后，只有 **`RESTORE VERIFIED`** 才能确认启动文件已回退。出现 **`RECOVERY FAILED`**、恢复无法确认或只读挂载失败时，不要反复重启或重复安装，应保留 SD 和现场，通过独立恢复通道处理。没有脚本会自动重启。
