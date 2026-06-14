"""负鼠振动控制器核心控制类"""

import asyncio
from typing import Optional, Callable, List, Union
from bleak import BleakScanner, BleakClient
from .constants import (
    DEFAULT_DEVICE_NAME, BASE_UUID,
    CHAR_WRITE, CHAR_NOTIFY, CHAR_BATTERY,
    CMD_LED_AND_REPORT, CMD_WAVEFORM, CMD_SCREEN_UPDATE, CMD_INTENSITY,
    INTENSITY_MIN, INTENSITY_MAX, WAVEFORM_MAX, B2_PREAMBLE
)
from .exceptions import ConnectionError, CommandError

# 回调函数原型：参数为 (sender_handle: int, data: bytearray)
NotificationCallback = Callable[[int, bytearray], None]

class PossumController:
    """负鼠振动控制器蓝牙操作类

    推荐使用异步上下文管理器进行连接和释放：

        async with PossumController() as device:
            battery = await device.get_battery()
            await device.set_intensity(a=100, b=150)
            await device.start_waveform_loop(duration=20.0)
    """

    def __init__(
        self,
        device_name: str = DEFAULT_DEVICE_NAME,
        address: Optional[str] = None,
        on_notification: Optional[NotificationCallback] = None,
        auto_connect: bool = True
    ):
        """
        Args:
            device_name: 蓝牙广播名称，默认 "47L127000"
            address: 蓝牙 MAC 地址，若提供则跳过扫描
            on_notification: 全局通知回调，收到设备上报时触发
            auto_connect: 使用 async with 时是否自动连接 (默认 True)
        """
        self.device_name = device_name
        self.address = address
        self.auto_connect = auto_connect

        self._client: Optional[BleakClient] = None
        self._write_uuid = BASE_UUID.format(CHAR_WRITE)
        self._notify_uuid = BASE_UUID.format(CHAR_NOTIFY)
        self._battery_uuid = BASE_UUID.format(CHAR_BATTERY)

        # 保存最近设置的强度（用于波形自动生成）
        self._last_intensity_a = 100
        self._last_intensity_b = 100

        # 回调列表
        self._callbacks: List[NotificationCallback] = []
        if on_notification:
            self._callbacks.append(on_notification)

    # ---------- 异步上下文管理器 ----------
    async def __aenter__(self):
        if self.auto_connect:
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    # ---------- 通知处理 ----------
    def _internal_notify_handler(self, sender: int, data: bytearray):
        """内部处理：打印原始报文 + 解析关键消息 + 转发给用户回调"""
        print(f"\n[Notify] {data.hex()}")

        if len(data) >= 1:
            head = data[0]
            if head == CMD_INTENSITY and len(data) >= 3:
                a_val, b_val = data[1], data[2]
                print(f"  -> 通道强度上报: A={a_val}, B={b_val}")
            elif head == 0xD0 and len(data) >= 4:
                seq = data[1]
                btn_low = data[2]
                btn_high = data[3]
                print(f"  -> 按键状态上报 序号:{seq} 状态集:{btn_low:08b} {btn_high:08b}")

        for cb in self._callbacks:
            try:
                cb(sender, data)
            except Exception as e:
                print(f"[Warning] 用户回调异常: {e}")

    def add_callback(self, callback: NotificationCallback):
        """注册额外的通知回调"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: NotificationCallback):
        """移除回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    # ---------- 连接管理 ----------
    async def connect(self):
        """扫描并连接设备，绑定通知"""
        if self._client and self._client.is_connected:
            print("设备已连接")
            return

        if not self.address:
            print(f"正在扫描设备 '{self.device_name}' ...")
            device = await BleakScanner.find_device_by_name(
                self.device_name, timeout=10.0
            )
            if not device:
                raise ConnectionError(
                    f"未找到设备 '{self.device_name}'，请确认已开机且蓝牙图标为黄色"
                )
            self.address = device.address
            print(f"找到设备: {device.name} ({self.address})")

        self._client = BleakClient(self.address)
        await self._client.connect()
        print("蓝牙已连接")

        # 安卓设备推荐设置 MTU
        try:
            mtu = await self._client.set_mtu(144)
            print(f"MTU 已设置为 {mtu}")
        except Exception as e:
            print(f"设置 MTU 失败（可忽略）: {e}")

        await self._client.start_notify(
            self._notify_uuid, self._internal_notify_handler
        )
        print("已绑定通知特征")

    async def disconnect(self):
        """断开连接"""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            print("蓝牙已断开")
        self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    # ---------- 基础功能 ----------
    async def get_battery(self) -> int:
        """读取当前电量（百分比）"""
        self._ensure_connected()
        data = await self._client.read_gatt_char(self._battery_uuid)
        return data[0]

    async def set_led_and_report(self, color: int = 0x01, enable_report: bool = True):
        """设置主灯颜色和按键上报开关

        Args:
            color: 颜色值 (1 字节，默认 0x01)
            enable_report: 是否开启按键状态上报 (默认开启)
        """
        self._ensure_connected()
        report = 0x01 if enable_report else 0x00
        cmd = bytearray([CMD_LED_AND_REPORT, color, report])
        print(f"发送 50 指令: {cmd.hex()}")
        await self._client.write_gatt_char(self._write_uuid, cmd)

    async def set_intensity(self, a: Optional[int] = None, b: Optional[int] = None):
        """同时设置 A/B 通道强度，并更新屏幕显示

        若某一参数为 None，则对应通道保持原值（发送 0xFF）。
        强度范围 0~200。

        Args:
            a: A 通道强度 (None 表示不变)
            b: B 通道强度 (None 表示不变)
        """
        self._ensure_connected()
        a_byte = a if a is not None else 0xFF
        b_byte = b if b is not None else 0xFF

        if a is not None:
            a_byte = max(INTENSITY_MIN, min(a_byte, INTENSITY_MAX))
            self._last_intensity_a = a_byte
        if b is not None:
            b_byte = max(INTENSITY_MIN, min(b_byte, INTENSITY_MAX))
            self._last_intensity_b = b_byte

        # 发送 B3 指令
        b3_cmd = bytearray([CMD_INTENSITY, a_byte, b_byte])
        print(f"发送 B3 指令: {b3_cmd.hex()}")
        await self._client.write_gatt_char(self._write_uuid, b3_cmd)

        # 发送 B2 指令（需要使用当前的强度值，不能是 0xFF）
        screen_a = self._last_intensity_a
        screen_b = self._last_intensity_b
        b2_cmd = bytearray([CMD_SCREEN_UPDATE]) + B2_PREAMBLE + bytearray([screen_a, screen_b])
        print(f"发送 B2 指令: {b2_cmd.hex()}")
        await self._client.write_gatt_char(self._write_uuid, b2_cmd)

    async def set_intensity_a(self, value: int):
        """单独设置 A 通道强度（0~200）"""
        await self.set_intensity(a=value)

    async def set_intensity_b(self, value: int):
        """单独设置 B 通道强度（0~200）"""
        await self.set_intensity(b=value)

    async def send_waveform(self,
                            a_data: Union[bytes, List[int]],
                            b_data: Union[bytes, List[int]]):
        """发送一次 B0 波形指令（20 字节）

        Args:
            a_data: A 通道 4 个强度值 (0~100)，bytes 或 List[int]
            b_data: B 通道 4 个强度值 (0~100)
        """
        self._ensure_connected()
        a_bytes = self._validate_waveform(a_data, "A 通道")
        b_bytes = self._validate_waveform(b_data, "B 通道")

        # 构造指令：HEAD + 7字节00 + A波形 + 4字节00 + B波形
        cmd = bytearray([CMD_WAVEFORM]) + bytes(7) + a_bytes + bytes(4) + b_bytes
        print(f"发送 B0 指令: {cmd.hex()}")
        await self._client.write_gatt_char(self._write_uuid, cmd)

    async def start_waveform_loop(self,
                                  duration: float,
                                  a_data: Optional[Union[bytes, List[int]]] = None,
                                  b_data: Optional[Union[bytes, List[int]]] = None,
                                  interval: float = 0.1):
        """循环发送 B0 波形，持续指定时间

        若未提供 a_data/b_data，则使用最近一次 set_intensity 设置的强度自动生成恒定波形
        （强度值 / 2，最大 100）。

        Args:
            duration: 持续时间（秒）
            a_data: A 通道波形数据，默认自动生成
            b_data: B 通道波形数据，默认自动生成
            interval: 发送间隔（秒），默认 0.1（100ms）
        """
        self._ensure_connected()

        if a_data is None:
            wave_a = min(self._last_intensity_a // 2, WAVEFORM_MAX)
            a_bytes = bytes([wave_a] * 4)
        else:
            a_bytes = self._validate_waveform(a_data, "A 通道")

        if b_data is None:
            wave_b = min(self._last_intensity_b // 2, WAVEFORM_MAX)
            b_bytes = bytes([wave_b] * 4)
        else:
            b_bytes = self._validate_waveform(b_data, "B 通道")

        cmd = bytearray([CMD_WAVEFORM]) + bytes(7) + a_bytes + bytes(4) + b_bytes
        total = int(duration / interval)
        print(f"开始循环发送波形，共 {total} 次，持续 {duration} 秒 ...")
        try:
            for i in range(total):
                print(f"B0 ({i+1}/{total}): {cmd.hex()}")
                await self._client.write_gatt_char(self._write_uuid, cmd)
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n用户中断波形发送")
        finally:
            print("波形发送结束")

    # ---------- 内部工具 ----------
    def _ensure_connected(self):
        if not self.is_connected:
            raise ConnectionError("设备未连接，请先调用 connect() 或使用 async with")

    def _validate_waveform(self, data, name: str) -> bytes:
        """校验并转换波形数据为 4 字节"""
        if isinstance(data, bytes):
            if len(data) != 4:
                raise ValueError(f"{name} 波形必须为 4 字节")
            result = data
        elif isinstance(data, (list, tuple)):
            if len(data) != 4:
                raise ValueError(f"{name} 波形必须包含 4 个元素")
            result = bytes(data)
        else:
            raise TypeError("波形数据应为 bytes 或 List[int]")

        for v in result:
            if v < 0 or v > WAVEFORM_MAX:
                raise ValueError(f"{name} 波形值超出范围 (0~{WAVEFORM_MAX})")
        return result