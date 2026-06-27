## DGLAB-controller-python

DG-LAB 蓝牙设备的 Python SDK，基于 bleak。
支持同时连接多个设备、异步事件处理，并通过 async with 自动管理连接。

---
支持的设备
---

灵猫边缘控制传感器(47L124000)

负鼠振动控制器 (47L127000)

爪印无线按钮传感器 (47L120300)


---
安装
---
```bash
pip install DGLAB-controller-python
```

要求 Python 3.10+ 且 bleak ≥ 0.21。

---
快速开始
---
灵猫 – 气压上报

```python
import asyncio
from dg_lab_devices import Civec

async def main():
    async with Civec() as civec:
        @civec.on_pressure
        def on_pressure(kpa: float):
            print(f"气压: {kpa:.2f} kPa")

        await civec.start_pressure_report(color=0x02)
        await asyncio.sleep(30)

asyncio.run(main())
```

负鼠 – 按键与强度

```python
from dg_lab_devices import Controller

async def main():
    async with Controller() as ctrl:
        @ctrl.on_button
        async def on_button(seq, buttons):
            if buttons.get("A"):
                await ctrl.set_strength(a=160)

        await ctrl.set_led_and_report(enable_button_report=True)
        await asyncio.sleep(60)

asyncio.run(main())
```

爪印 – 触发模式

```python
from dg_lab_devices import PawPrints

async def main():
    async with PawPrints() as pp:
        @pp.on_trigger
        def on_trigger(color, event_id, param):
            print(f"触发事件 {event_id}，参数={param}")

        await pp.set_random_trigger(
            color=0x01, event_id=5,
            green_min=30, green_max=50,
            reaction_time=10,
            param_inc=20, param_speed=40,
            param_dec=50, param_dec_speed=40
        )
        await asyncio.sleep(300)

asyncio.run(main())
```

---
主要特性
---
· **异步事件驱动** – 装饰器订阅设备通知

· **自动连接管理** – async with 自动连接/断开

· **多设备并发** – 同一事件循环同时运行多个设备

· **完整协议支持** – 实现所有 BLE 指令与回调

---
开源许可
---
本项目使用 MIT 许可证。

---
联系作者 
---
. QQ群:870333220 <del>有香香软软的小南娘和技术大佬<del>

---
相关链接
---

. [参考文档](https://github.com/dungeonlab-open/dglab-bluetooth-protocol)

· [PyPI](https://pypi.org/project/DGLAB-controller-python/)

· [API文档](docs/API.md)