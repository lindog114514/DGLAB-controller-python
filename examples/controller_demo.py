"""负鼠控制器示例：按键监听与强度控制"""
import asyncio
from dg_lab_devices import Controller

async def main():
    async with Controller() as ctrl:
        @ctrl.on_button
        async def on_button(seq, buttons):
            if buttons.get("A"):
                print("A 键按下，设置 A 通道强度为 160")
                await ctrl.set_strength(a=160)
            elif buttons.get("B"):
                print("B 键按下，设置 B 通道强度为 200")
                await ctrl.set_strength(b=200)

        @ctrl.on_strength_change
        def on_strength(a, b):
            print(f"强度变化 -> A: {a}, B: {b}")

        # 开启按键上报，蓝色指示灯
        await ctrl.set_led_and_report(color=0x04, enable_button_report=True)
        print("等待按键操作（60 秒）...")
        await asyncio.sleep(60)

asyncio.run(main())