"""灵猫边缘控制传感器 (Civec)"""
from .base import BaseDevice
import struct

class Civec(BaseDevice):
    def __init__(self, address: str = None, name: str = "47L124000"):
        super().__init__(address, name)

    def on_pressure(self, func):
        return self._register_event("pressure", func)

    def on_battery(self, func):
        return self._register_event("battery", func)

    async def _on_main_notify(self, sender, data: bytearray):
        if len(data) >= 17 and data[0] == 0xD0:
            raw = struct.unpack_from('<h', data, 8)[0]
            await self._emit_event("pressure", raw / 100.0)

    async def start_pressure_report(self, color: int = 0x01):
        await self._write_command(bytes([0x50, color, 0xD0]) + b'\x00' * 14)

    async def stop_pressure_report(self, color: int = 0x01):
        await self._write_command(bytes([0x50, color, 0x00]) + b'\x00' * 14)

    async def reset_pressure(self):
        await self._write_command(bytes([0x66]) + b'\x00' * 9 + b'\x00\x02\x00')

    async def flip_screen(self, current_rotate: int = 1) -> int:
        new_rotate = 0x03 if current_rotate == 1 else 0x01
        cmd = bytes([0x66]) + b'\x00' * 9 + bytes([new_rotate, 0x00, 0x00])
        await self._write_command(cmd)
        return new_rotate