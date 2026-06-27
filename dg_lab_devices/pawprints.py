"""爪印无线按钮传感器 V1.1 (PawPrints)"""
import struct
from .base import BaseDevice

class PawPrints(BaseDevice):
    def __init__(self, address: str = None, name: str = "47L120300"):
        super().__init__(address, name)

    def on_status(self, func):
        return self._register_event("status", func)

    def on_trigger(self, func):
        return self._register_event("trigger", func)

    def on_untrack(self, func):
        return self._register_event("untrack", func)

    def on_param_change(self, func):
        return self._register_event("param_change", func)

    def on_physical(self, func):
        return self._register_event("physical", func)

    def on_auto_detect(self, func):
        return self._register_event("auto_detect", func)

    async def _on_main_notify(self, sender, data: bytearray):
        head = data[0]
        if head == 0x51 and len(data) >= 4:
            await self._emit_event("status", data[1], data[2], data[3])
        elif head == 0x5A and len(data) >= 4:
            await self._emit_event("trigger", data[1], data[2], data[3])
        elif head == 0x5B and len(data) >= 3:
            await self._emit_event("untrack", data[1], data[2])
        elif head == 0x5C and len(data) >= 4:
            await self._emit_event("param_change", data[1], data[2], data[3])
        elif head == 0xD0 and len(data) >= 9:
            await self._emit_event("physical", data[1], data[2], data[3],
                                   data[4], data[5], data[6], data[7], data[8])
        elif head == 0xF1 and len(data) >= 14:
            x_range = struct.unpack_from('<hh', data, 2)
            y_range = struct.unpack_from('<hh', data, 6)
            z_range = struct.unpack_from('<hh', data, 10)
            await self._emit_event("auto_detect", x_range, y_range, z_range)

    async def _write_50(self, payload: bytes):
        await self._write_command(bytes([0x50]) + payload)

    async def set_trigger_mode_none(self, color: int = 0x01):
        await self._write_50(bytes([color, 0x00]) + b'\x00' * 14)

    async def set_random_trigger(self, color: int, event_id: int,
                                 green_min: int, green_max: int,
                                 reaction_time: int,
                                 param_inc: int, param_speed: int,
                                 param_dec: int, param_dec_speed: int):
        payload = struct.pack('<BBHHHHBBB', color, 0x03, event_id,
                              green_min, green_max, reaction_time,
                              param_inc, param_speed, param_dec, param_dec_speed)
        payload += b'\x00' * 3
        await self._write_command(bytes([0x50]) + payload)

    async def set_probability_trigger(self, color: int, events_probs: list[tuple[int, int]], cooldown: int):
        data = bytearray([0x50, color, 0x04])
        for i in range(6):
            eid, prob = events_probs[i] if i < len(events_probs) else (0, 0)
            data.append(eid)
            data.append(prob)
        data.append((cooldown >> 8) & 0xFF)
        data.append(cooldown & 0xFF)
        await self._write_command(bytes(data))

    async def set_external_voltage_trigger(self, color: int, event_id: int,
                                           pull_up: int, vol_min: int, vol_max: int, map_range: int):
        payload = bytes([color, 0x0F, event_id, pull_up, vol_min, vol_max, map_range]) + b'\x00' * 9
        await self._write_50(payload)

    async def set_press_motion_trigger(self, color: int, press_event_id: int,
                                       settings_byte: int, press_inc_speed: int,
                                       press_dec_val: int, press_dec_speed: int,
                                       press_inc_val: int, motion_event_id: int,
                                       motion_config: bytes, map_range: int):
        payload = bytes([color, 0x05, press_event_id, settings_byte,
                         press_inc_speed, press_dec_val, press_dec_speed, press_inc_val,
                         motion_event_id]) + motion_config + bytes([map_range])
        await self._write_50(payload)

    async def set_physical_data_mode(self, color: int = 0x01):
        await self._write_50(bytes([color, 0xD0]) + b'\x00' * 14)

    async def reset_param(self):
        await self._write_command(b'\x5F')

    async def auto_detect_angle(self):
        await self._write_command(b'\x60')

    async def set_led(self, color: int):
        await self._write_command(bytes([0x70, color]))

    async def set_led_blink(self, color1: int, color2: int, speed: int):
        await self._write_command(bytes([0x70, color1, color2, speed]))