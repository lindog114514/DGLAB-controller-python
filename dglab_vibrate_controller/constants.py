"""蓝牙 UUID 与指令常量"""

# 默认设备广播名称
DEFAULT_DEVICE_NAME = "47L127000"

# UUID 基础模板
BASE_UUID = "0000{:04x}-0000-1000-8000-00805f9b34fb"

# 特征 UUID
CHAR_WRITE    = 0x150A   # 写指令
CHAR_NOTIFY   = 0x150B   # 接收通知
CHAR_BATTERY  = 0x1500   # 电量

# 指令头
CMD_LED_AND_REPORT = 0x50   # 指示灯 + 按键上报开关
CMD_WAVEFORM       = 0xB0   # 波形数据
CMD_SCREEN_UPDATE  = 0xB2   # 更新屏幕显示
CMD_INTENSITY      = 0xB3   # 强度设置

# 强度范围
INTENSITY_MIN = 0
INTENSITY_MAX = 200
WAVEFORM_MAX  = 100   # 波形数据最大值

# B2 指令固定前导数据（21 字节）
B2_PREAMBLE = bytes.fromhex("FFFF00" + "F" * 32 + "0809")