"""公共常量与工具"""
import uuid

_BASE_UUID_SUFFIX = "-0000-1000-8000-00805f9b34fb"

def uuid16(short_id: int) -> uuid.UUID:
    """将16位短ID转换为完整的128位蓝牙UUID"""
    return uuid.UUID(f"0000{short_id:04x}{_BASE_UUID_SUFFIX}")

# 标准蓝牙服务/特征
SERVICE_DEVICE_INFO = uuid16(0x180A)
CHAR_BATTERY = uuid16(0x1500)
SERVICE_MAIN = uuid16(0x180C)
CHAR_WRITE = uuid16(0x150A)
CHAR_NOTIFY = uuid16(0x150B)

# 颜色常量
COLORS = {
    0x00: "熄灭",
    0x01: "黄色",
    0x02: "红色",
    0x03: "紫色",
    0x04: "蓝色",
    0x05: "青色",
    0x06: "绿色",
    0x07: "白色",
}

class DeviceError(Exception):
    """设备相关异常"""
    pass