## DGLAB-controller-python API 文档

---

安装

```bash
pip install DGLAB-controller-python
```

依赖：

- Python ≥ 3.10

- bleak ≥ 0.21

---
快速开始
---
```python
import asyncio
from dg_lab_devices import Civec

async def main():
    async with Civec() as civec:
        @civec.on_pressure
        def on_pressure(kpa):
            print(f"气压: {kpa:.2f} kPa")

        await civec.start_pressure_report(color=0x02)
        await asyncio.sleep(30)

asyncio.run(main())
```

---
通用设计
---
##### 异步上下文管理器

所有设备类均支持 async with 语法，进入时自动连接，退出时自动断开：

```python
async with DeviceClass() as device:
    # 设备已连接
    ...
# 此处设备已断开
```

#### 事件装饰器

每个设备提供一系列 on_* 方法，可作为装饰器注册回调。回调可以是同步函数或协程。

#### 颜色常量

可使用以下整数值表示颜色：

|值 |颜色|
|---|---|
|0x00|熄灭|
|0x01|黄色|
|0x02|红色|
|0x03|紫色|
|0x04|蓝色|
|0x05|青色|
|0x06|绿色|
|0x07|白色|

---
基础设备类 (BaseDevice)
---
抽象基类，不能被直接实例化 

#### 构造参数

```python
BaseDevice(address: str | None = None, name: str = "")
```

|参数| 类型       |说明|
|---|----------|----|
|address | str或None |蓝牙 MAC 地址，None 时按名称扫描|
|name | str      |蓝牙广播名称

#### 通用方法

|方法|说明|
|----|---|
|await connect() |连接设备|
|await disconnect() |断开连接（可安全重复调用）|
|await get_battery() -> int |主动读取电量，返回 0–100|

---
灵猫传感器 Civec
---

```python
from dg_lab_devices import Civec
```

#### 构造参数

```python
Civec(address: str | None = None, name: str = "47L124000")
```

#### 事件装饰器

**@civec.on_pressure**

```python
async def callback(pressure_kpa: float):
    ...
```

- 触发：调用 start_pressure_report 后，设备每 100ms 主动上报一次。

- 参数：pressure_kpa – 气压值（kPa），精确到 0.01 kPa。

**@civec.on_battery**

```python
async def callback(percent: int):
    ...
```

- 触发：电量变化时。

- 参数：percent – 电量百分比 (0–100)。

#### 指令方法

|方法| 说明|
|----|----|
|await start_pressure_report(color=0x01) |开启气压主动上报|
|await stop_pressure_report(color=0x01) |停止气压主动上报|
|await reset_pressure() |重置气压读值为零|
|await flip_screen(current_rotate=1) -> int |翻转屏幕方向，返回新方向值 (1 或 3)|

---
负鼠控制器 Controller
---

```python
from dg_lab_devices import Controller
```

#### 构造参数

```python
Controller(address: str | None = None, name: str = "47L127000")
```

#### 事件装饰器

**@ctrl.on_button**

```python
async def callback(seq: int, buttons: dict[str, bool]):
    ...
```

- 触发：物理按键按下或抬起时（需先调用 set_led_and_report 开启上报）。

- 参数：
  - seq – 报文序号 (0–255 循环)。

  - buttons – 字典，键为按钮名称，值为 True (按下) 或 False (抬起)。

#### 支持的按键名称：

具体名称对应的按键表请参考官方文档
```
SEL_1, SEL_2, HOME, Up, Down, Left, Right, B, A, G, D
```

**@ctrl.on_strength_change**

```python
async def callback(a_strength: int, b_strength: int):
    ...
```

- 触发：A/B 通道强度发生变化时（指令或物理按键）。
- 参数：a_strength、b_strength – 强度值 (0–200)。

**@ctrl.on_battery**

同灵猫的 on_battery。

##### 指令方法

|方法|说明|
|----|---|
|await set_led_and_report(color=0x01, enable_button_report=True) |设置指示灯颜色，开启/关闭按键上报|
|await set_strength(a=None, b=None) |设置 A/B 通道强度。None 或 0xFF 表示不修改|
|await set_waveform(a_wave, b_wave) |写入振动波形数据。每个通道 4 字节，值范围 0–100。每 100ms 写入一次|

##### 强度设置示例：

```python
await ctrl.set_strength(a=160)          # 仅修改 A 通道
await ctrl.set_strength(a=100, b=200)   # 同时修改两个通道
```

调用 set_strength 后会自动通过 B2 指令更新屏幕显示。

---
爪印按钮传感器 PawPrints
----
```python
from dg_lab_devices import PawPrints
```

构造参数

```python
PawPrints(address: str | None = None, name: str = "47L120300")
```

连接后必须立即写入触发模式设置，库会自动发送“无任何触发”模式以防断开。

#### 事件装饰器

**@pp.on_status**

```python
async def callback(color: int, device_type: int, battery: int):
    ...
```

- 触发：连接后首次上报，或电量变化时。
- 参数：
  - color – 当前主指示灯颜色。
  - device_type – 设备类型 (V1.1 = 0x03)。
  - battery – 电量百分比。

**@pp.on_trigger**

```python
async def callback(color: int, event_id: int, param: int):
    ...
```
 
- 触发：进入事件触发状态时。
- 参数：
  - event_id – 触发的设定事件 ID。
  - param – 当前参数值 (0–255)。

**@pp.on_untrack**

```python
async def callback(color: int, event_id: int):
    ...
```

- 触发：事件触发状态取消时。

**@pp.on_param_change**

```python
async def callback(color: int, event_id: int, param: int):
    ...
```

- 触发：参数值发生变化时（含触发期间的持续变化）。

**@pp.on_physical**

```python
async def callback(color: int, seq: int, pressed: int,
                   accel: int, x: int, y: int, z: int, voltage: int):
    ...
```

- 触发：当设置为 D0 物理数据直传模式后，每 100ms 上报一次。
 
参数：
  - pressed – 按下状态 (0x00 未按下，否则按下)。

  - accel – 加速度值。

  - x, y, z – XYZ 轴角度值。

  - voltage – 外部电压原始值 (0–210 对应 0.00V–2.10V)。


**@pp.on_auto_detect**

```python
async def callback(x_range: tuple[int, int],
                   y_range: tuple[int, int],
                   z_range: tuple[int, int]):
    ...
```

- 触发：调用 auto_detect_angle() 完成后上报。
- 参数：各轴的角度阈值范围（已按协议除以 2 的有符号 16 位值）。

##### 指令方法

触发模式设置

- 所有触发模式设置方法的第一个参数多为 color（指示灯颜色），其余参数含义请参照 DG-LAB 官方协议。

|方法| 说明|
|---|-----|
|await set_trigger_mode_none(color=0x01) |无任何触发（仅保持连接）|
|await set_random_trigger(color, event_id, green_min, green_max, reaction_time, param_inc, param_speed, param_dec, param_dec_speed)| 随机反应触发|
|await set_probability_trigger(color, events_probs, cooldown) 概率触发：events_probs 为最多 6 个 (事件ID, 概率) 元组，概率总和 ≤ 200；cooldown| 为冷却时间（秒）|
|await set_external_voltage_trigger(color, event_id, pull_up, vol_min, vol_max, map_range) |外部电压检测触发，电压单位 0.01V|
|await set_press_motion_trigger(color, press_event_id, settings_byte, press_inc_speed, press_dec_val, press_dec_speed, press_inc_val, motion_event_id, motion_config, map_range) |按下/抬起 + 加速度/角度组合触发。settings_byte 为位组合控制字节，motion_config 为 6 字节配置|
|await set_physical_data_mode(color=0x01) |开启 D0 物理数据直传模式（每 100ms 上报全部传感器数据）|

概率触发示例：

```python
events = [(5, 60), (2, 80)]   # 事件5概率30%，事件2概率40%
await pp.set_probability_trigger(color=0x01, events_probs=events, cooldown=600)
```

#### 其他指令

|方法| 说明|
|---|---|
|await reset_param() |重置所有触发模式的参数值为 0|
|await auto_detect_angle() |启动自动角度检测，结果通过 on_auto_detect 事件返回|
|await set_led(color) |点亮肩灯为指定颜色|
|await set_led_blink(color1, color2, speed) |控制肩灯闪烁，speed：0x01 慢速、0x02 快速、0x03 停止|

---

#### 高级用法

 - 多设备并发

```python
async with Civec() as civec, Controller() as ctrl, PawPrints() as pp:
    # 三台设备同时在线
    ...
```

- 或手动并行连接：

```python
civec = Civec()
ctrl = Controller()
await asyncio.gather(civec.connect(), ctrl.connect())
```

- 指定蓝牙地址

```python
device = Civec(address="AA:BB:CC:DD:EE:FF")
await device.connect()
```

#### 错误处理

连接与通信错误将抛出 DeviceError 或标准异常，建议用 try/except 捕获：

```python
from dg_lab_devices.common import DeviceError

try:
    async with Civec() as civec:
        ...
except DeviceError as e:
    print(f"设备错误: {e}")
```

---
公共模块参考
----

**dg_lab_devices.common**

- 提供底层常量与工具，一般无需直接使用。

```python
from dg_lab_devices.common import (
    uuid16,
    SERVICE_DEVICE_INFO,
    CHAR_BATTERY,
    SERVICE_MAIN,
    CHAR_WRITE,
    CHAR_NOTIFY,
    COLORS,
    DeviceError
)
```

- uuid16(short_id: int) -> uuid.UUID – 将 16 位短 ID 转换为 128 位蓝牙 UUID。
- SERVICE_DEVICE_INFO – 设备信息服务 (0x180A)。
- CHAR_BATTERY – 电量特征 (0x1500)。
- SERVICE_MAIN – 主服务 (0x180C)。
- CHAR_WRITE – 指令写入特征 (0x150A)。
- CHAR_NOTIFY – 消息通知特征 (0x150B)。
- COLORS – 颜色值到名称的映射字典。
- DeviceError – 库自定义异常类。


#### 如有协议细节疑问，请参考 DG-LAB 官方文档，本库尽力保持一致。。