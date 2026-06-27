"""灵猫传感器示例：气压上报与基本控制"""
import asyncio
from dg_lab_devices import Civec

async def main():
    async with Civec() as civec:
        @civec.on_pressure
        def on_pressure(kpa: float):
            print(f"气压: {kpa:.2f} kPa")

        # 开启上报，红色指示灯
        await civec.start_pressure_report(color=0x02)
        print("气压上报已开启，运行 30 秒...")
        await asyncio.sleep(30)
        await civec.stop_pressure_report()
        print("已停止上报")

asyncio.run(main())