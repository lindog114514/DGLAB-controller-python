"""多设备并发示例：同时连接灵猫、负鼠、爪印"""
import asyncio
from dg_lab_devices import Civec, Controller, PawPrints

async def main():
    async with Civec() as civec, \
               Controller() as ctrl, \
               PawPrints() as pp:

        @civec.on_pressure
        def pressure_cb(kpa):
            print(f"[灵猫] 气压: {kpa:.2f} kPa")

        @ctrl.on_button
        async def button_cb(seq, buttons):
            pressed = [k for k, v in buttons.items() if v]
            if pressed:
                print(f"[负鼠] 按键按下: {pressed}")

        @pp.on_trigger
        def trigger_cb(color, eid, param):
            print(f"[爪印] 触发事件 {eid}，参数 {param}")

        # 启动各个设备的功能
        await civec.start_pressure_report(color=0x02)
        await ctrl.set_led_and_report(color=0x04, enable_button_report=True)
        await pp.set_random_trigger(
            color=0x01, event_id=3,
            green_min=10, green_max=20,
            reaction_time=5,
            param_inc=10, param_speed=30,
            param_dec=20, param_dec_speed=30
        )

        print("三个设备同时运行 120 秒...")
        await asyncio.sleep(120)

asyncio.run(main())