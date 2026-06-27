"""设备基类：BLE连接、事件注册/发射、通用命令"""
import asyncio
import logging
from abc import ABC, abstractmethod
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError  # 新增
from .common import CHAR_WRITE, CHAR_NOTIFY, CHAR_BATTERY, DeviceError

logger = logging.getLogger(__name__)

class BaseDevice(ABC):
    """所有DG-LAB蓝牙设备的抽象基类"""

    def __init__(self, address: str | None = None, name: str = ""):
        self.address = address
        self.name = name
        self.client: BleakClient | None = None
        self._event_handlers: dict[str, list] = {}

    # ---------- 异步上下文管理器 ----------
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False

    # ---------- 事件装饰器注册 ----------
    def _register_event(self, event_name: str, func):
        self._event_handlers.setdefault(event_name, []).append(func)
        return func

    async def _emit_event(self, event_name: str, *args):
        for handler in self._event_handlers.get(event_name, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args)
                else:
                    handler(*args)
            except Exception as e:
                logger.error(f"事件 {event_name} 回调异常: {e}")

    # ---------- 连接管理 ----------
    async def connect(self) -> None:
        try:
            if self.address is None:
                device = await BleakScanner.find_device_by_name(self.name, timeout=5.0)
                if device is None:
                    raise DeviceError(f"未找到设备: {self.name}")
                self.address = device.address
            self.client = BleakClient(self.address)
            await self.client.connect()
        except BleakError as e:
            msg = str(e).lower()
            if any(keyword in msg for keyword in ("bluetooth", "adapter")) and \
               any(keyword in msg for keyword in ("off", "disabled", "not available", "not found")):
                raise DeviceError("蓝牙未开启，请打开蓝牙后重试") from e
            raise DeviceError(f"连接失败: {e}") from e
        except Exception as e:
            raise DeviceError(f"设备连接异常: {e}") from e

        # 连接成功后启动通知
        await self.client.start_notify(CHAR_NOTIFY, self._on_main_notify)
        try:
            await self.client.start_notify(CHAR_BATTERY, self._on_battery_notify)
        except Exception:
            logger.debug("设备不支持电量通知，使用主动读取")
        logger.info(f"已连接 {self.name} [{self.address}]")

    async def disconnect(self) -> None:
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            logger.info(f"已断开 {self.name}")
        self.client = None

    @abstractmethod
    async def _on_main_notify(self, sender, data: bytearray):
        ...

    async def _on_battery_notify(self, sender, data: bytearray):
        if data:
            await self._emit_event("battery", data[0])

    async def _write_command(self, cmd: bytes):
        if not self.client or not self.client.is_connected:
            raise DeviceError("设备未连接")
        await self.client.write_gatt_char(CHAR_WRITE, cmd, response=False)

    async def get_battery(self) -> int:
        if not self.client:
            raise DeviceError("未连接")
        data = await self.client.read_gatt_char(CHAR_BATTERY)
        return data[0] if data else 0