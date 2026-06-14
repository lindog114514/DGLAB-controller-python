## DGLAB-vibrate-controller-python— API 参考手册

安装

```bash
pip install dglab-vibrate-controller
```

导入

```python
from dglab_vibrate_controller import PossumController
```

---

一、初始化

```python
PossumController(
    device_name: str = "47L127000",
    address: Optional[str] = None,
    on_notification: Optional[Callable[[int, bytearray], None]] = None,
    auto_connect: bool = True
)
```

参数 类型 默认值 说明
device_name str "47L127000" 蓝牙广播名称。
address str 或 None None 已知的 MAC 地址，提供后跳过扫描。
on_notification Callable 或 None None 全局通知回调函数，每当收到设备上报时调用。签名：def callback(sender: int, data: bytearray) -> None。
auto_connect bool True 使用 async with 上下文时，是否自动调用 connect()。

推荐用法（异步上下文管理器）：

```python
async with PossumController() as device:
    # 自动连接，退出时自动断开
    ...
```

---

二、连接管理

async connect()

扫描并连接设备，绑定通知特征。若已连接则无操作。

可能抛出的异常：

· ConnectionError：未找到设备时抛出。

async disconnect()

断开蓝牙连接，清理资源。

is_connected（属性）

-> bool
返回当前是否已连接。

---

三、基础控制

async get_battery() -> int

读取当前电量百分比（0–100）。

示例：

```python
battery = await device.get_battery()
```

async set_led_and_report(color: int = 0x01, enable_report: bool = True)

设置主指示灯颜色并控制按键状态上报的开关。

参数 类型 默认值 说明
color int 0x01 指示灯颜色（1 字节）。
enable_report bool True 是否开启按键状态上报（0xB3 / 0xD0）。

---

四、强度控制

async set_intensity(a: Optional[int] = None, b: Optional[int] = None)

同时设置 A / B 通道强度，并自动更新屏幕显示。
强度范围：0 ~ 200。若不传值（或传 None），对应通道保持不变（内部发送 0xFF）。

示例：

```python
await device.set_intensity(a=160)         # 仅修改A通道
await device.set_intensity(b=200)         # 仅修改B通道
await device.set_intensity(a=120, b=80)   # 同时修改
```

async set_intensity_a(value: int)

单独设置 A 通道强度（0–200）。

async set_intensity_b(value: int)

单独设置 B 通道强度（0–200）。

---

五、波形发送

async send_waveform(a_data: Union[bytes, List[int]], b_data: Union[bytes, List[int]])

发送一次 B0 波形指令（20 字节），立即控制振动。

· 每个通道需要 4 个字节，代表 100ms 内四段 25ms 的强度。
· 波形值范围：0 ~ 100。
· 输入类型可为 bytes（长度=4）或 List[int]（长度=4）。

示例：

```python
await device.send_waveform(
    a_data=[50, 80, 30, 10],
    b_data=[0, 100, 50, 20]
)
```

async start_waveform_loop(duration: float, a_data=None, b_data=None, interval: float = 0.1)

循环发送 B0 波形指令，持续指定时长。

· 若未提供 a_data 或 b_data，会根据最近一次 set_intensity 设定的强度自动生成恒定波形（强度值 / 2，上限 100）。
· duration：持续时间（秒），interval：发送间隔（默认 0.1 秒）。

示例：

```python
# 先设置强度，再循环发送 20 秒波形
await device.set_intensity(a=100, b=100)
await device.start_waveform_loop(duration=20.0)
```

---

六、通知回调

所有设备上报（B3 强度变化、D0 按键状态等）会通过库内部自动打印原始 hex 并解析，同时调用用户注册的所有回调。

add_callback(callback: Callable[[int, bytearray], None])

注册一个额外的通知回调，可多次调用添加多个回调。

remove_callback(callback: Callable[[int, bytearray], None])

移除已注册的回调。

回调函数签名：

```python
def my_notification(sender: int, data: bytearray) -> None:
    # sender: 通知来源的句柄
    # data: 原始数据包，例如 b'\xb3\x64\xc8'
```

---

七、异常

所有异常继承自 PossumError：

· ConnectionError：连接相关错误（例如设备未找到、未连接时调用方法）
· CommandError：指令发送异常（预留，当前版本可能不触发）

---

八、完整使用流程示例

```python
import asyncio
from dglab_vibrate_controller import PossumController

async def main():
    async with PossumController() as dev:
        batt = await dev.get_battery()
        print(f"电量：{batt}%")

        await dev.set_led_and_report(color=0x01, enable_report=True)
        await dev.set_intensity(a=120, b=80)

        await dev.start_waveform_loop(duration=5.0)

asyncio.run(main())
```

---

九、常量

常量名 值 说明
DEFAULT_DEVICE_NAME "47L127000" 默认设备广播名称
INTENSITY_MIN 0 强度最小值
INTENSITY_MAX 200 强度最大值
WAVEFORM_MAX 100 波形数据最大值

所有 API 均为异步，需在 asyncio 事件循环中调用。