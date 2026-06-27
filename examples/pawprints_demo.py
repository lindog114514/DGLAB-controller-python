"""爪印按钮传感器示例：随机反应触发模式"""
import asyncio
from dg_lab_devices import PawPrints

async def main():
    async with PawPrints() as pp:
        @pp.on_trigger
        def on_trigger(color, event_id, param):
            print(f"触发事件 {event_id}，当前参数 {param}")

        @pp.on_untrack
        def on_untrack(color, event_id):
            print(f"事件 {event_id} 已取消")

        @pp.on_param_change
        def on_param_change(color, event_id, param):
            print(f"事件 {event_id} 参数变化 -> {param}")

        # 设置随机反应触发：事件ID=7，绿灯随机30~50秒，反应时间10秒
        await pp.set_random_trigger(
            color=0x01, event_id=7,
            green_min=30, green_max=50,
            reaction_time=10,
            param_inc=20, param_speed=40,
            param_dec=50, param_dec_speed=40
        )
        print("随机反应触发模式已启动，运行 5 分钟...")
        await asyncio.sleep(300)

asyncio.run(main())