"""负鼠振动控制器 (Controller)"""
from .base import BaseDevice

class Controller(BaseDevice):
    def __init__(self, address: str = None, name: str = "47L127000"):
        super().__init__(address, name)
        self._button_map = [
            "SEL_1", "SEL_2", "HOME", None, None, None, None, None,
            "Up", "Down", "Left", "Right", "B", "A", "G", "D"
        ]

    def on_button(self, func):
        return self._register_event("button", func)

    def on_strength_change(self, func):
        return self._register_event("strength", func)

    def on_battery(self, func):
        return self._register_event("battery", func)

    async def _on_main_notify(self, sender, data: bytearray):
        if len(data) >= 3 and data[0] == 0xB3:
            await self._emit_event("strength", data[1], data[2])
        elif len(data) >= 4 and data[0] == 0xD0:
            seq = data[1]
            state = (data[2] << 8) | data[3]
            buttons = {}
            for i, name in enumerate(self._button_map):
                if name:
                    buttons[name] = bool(state & (1 << (15 - i)))
            await self._emit_event("button", seq, buttons)

    async def set_led_and_report(self, color: int = 0x01, enable_button_report: bool = True):
        mode = 0x01 if enable_button_report else 0x00
        await self._write_command(bytes([0x50, color, mode]))

    async def set_waveform(self, a_wave: list[int], b_wave: list[int]):
        if len(a_wave) != 4 or len(b_wave) != 4:
            raise ValueError("波形数据必须为4字节")
        for v in a_wave + b_wave:
            if not (0 <= v <= 100):
                raise ValueError("波形强度超出0-100")
        cmd = bytes([0xB0]) + b'\x00' * 7 + bytes(a_wave) + b'\x00' * 4 + bytes(b_wave)
        await self._write_command(cmd)

    async def set_strength(self, a: int | None = None, b: int | None = None):
        def _byte(v):
            return 0xFF if v is None else v
        cmd = bytes([0xB3, _byte(a), _byte(b)])
        await self._write_command(cmd)
        # 同步屏幕显示
        await self._sync_screen(a, b)

    async def _sync_screen(self, a: int | None, b: int | None):
        prefix = bytes.fromhex("FFFF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0809")
        a_byte = a if a is not None else 0xFF
        b_byte = b if b is not None else 0xFF
        cmd = bytes([0xB2]) + prefix + bytes([a_byte, b_byte])
        await self._write_command(cmd)