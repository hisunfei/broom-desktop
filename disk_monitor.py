#!/usr/bin/env python3
"""
broom-widget - macOS 菜单栏磁盘监控小挂件
配合 broom skill 使用，实时监控磁盘空间，一键获取清理命令

Version: 1.0.0
License: MIT
"""

import objc
import os
import sys
import json
import time
import logging
import subprocess
import fcntl
from pathlib import Path
from Foundation import NSHomeDirectory, NSMakeRect, NSMakeSize, NSPoint
from AppKit import (
    NSApplication, NSStatusBar, NSStatusItem,
    NSMenu, NSMenuItem, NSVariableStatusItemLength,
    NSApplicationActivationPolicyAccessory,
    NSImage, NSBitmapImageRep, NSGraphicsContext,
    NSBezierPath, NSColor, NSDeviceRGBColorSpace,
    NSMutableAttributedString, NSAlert, NSTextView,
    NSScrollView, NSTimer, NSObject, NSFont,
    NSWindow, NSTitledWindowMask, NSClosableWindowMask,
    NSBackingStoreBuffered, NSPasteboard, NSStringPboardType,
    NSTextField, NSButton, NSView, NSSwitchButton,
    NSBitmapImageFileTypePNG,
)

# ─── 版本信息 ────────────────────────────────────────────
APP_VERSION = "1.0.0"
APP_NAME = "broom-widget"
APP_BUNDLE_ID = "com.hisunfei.broom-widget"
BROOM_GITHUB = "https://github.com/hisunfei/broom"
WIDGET_GITHUB = "https://github.com/hisunfei/broom-widget"

# ─── 日志 ────────────────────────────────────────────────
LOG_DIR = Path.home() / "Library" / "Logs" / "broom-widget"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "broom-widget.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("broom-widget")

# ─── 国际化 ──────────────────────────────────────────────
def get_system_language():
    """获取系统语言"""
    try:
        # macOS 优先使用系统语言设置
        import subprocess
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleLocale"],
            capture_output=True, text=True
        )
        lang = result.stdout.strip()
        return "zh" if lang.startswith("zh") else "en"
    except:
        return "en"

LANG = get_system_language()

I18N = {
    "zh": {
        "app_name": "broom-widget",
        "broom_clean": "Broom 清理",
        "low_space_alert": "空间不足提醒",
        "launch_at_startup": "开机启动",
        "enable": "启用",
        "disable": "禁用",
        "display_style": "显示风格",
        "pie": "饼图",
        "text": "纯文字",
        "bar": "进度条",
        "quit": "退出",
        "about": "关于",
        "preferences": "偏好设置",
        "uninstall": "卸载",
        "used": "已用",
        "free": "可用",
        "total": "总计",
        "broom_desc": "Broom 是一个 AI agent 驱动的智能磁盘清理工具。\n你可以使用它了解当前电脑的缓存、下载、应用数据等，\n同时自己定制清理方案，安全地释放空间。",
        "install_method": "【安装方法】",
        "step1": "1、复制以下信息发送给你的 agent：",
        "install_cmd": "使用https://github.com/hisunfei/broom，为我清理电脑；",
        "step2": "2、首次安装后会自动清理一次，后续只需对 Agent 说：\"broom\"即可开始清理。",
        "step3": "3、如果你想让它自动进行清理，可以告诉 agent：",
        "schedule_cmd": "每周一上午10 点，使用broom skill自动为我清理电脑（https://github.com/hisunfei/broom）；",
        "close": "关闭",
        "welcome_title": "欢迎使用 broom-widget",
        "welcome_msg": "broom-widget 已启动！\n\n它会在菜单栏显示你的磁盘空间。\n点击菜单栏图标可以：\n• 查看 Broom 清理说明\n• 设置空间不足提醒\n• 切换显示风格\n• 设置开机启动",
        "ok": "好的",
        "about_title": "关于 broom-widget",
        "about_msg": f"broom-widget v{APP_VERSION}\n\nmacOS 菜单栏磁盘监控小挂件\n配合 broom AI skill 使用\n\nGitHub: {WIDGET_GITHUB}\nbroom: {BROOM_GITHUB}\n\n© 2024 hisunfei. MIT License.",
        "uninstall_confirm": "确定要卸载 broom-widget 吗？\n这将删除配置文件和开机启动项。",
        "uninstall_done": "broom-widget 已卸载。\n配置文件已删除。",
        "cancel": "取消",
        "already_running": "broom-widget 已在运行中",
        "alert_low_space": "⚠️ 磁盘空间不足",
        "alert_msg_template": "可用空间仅剩 {free:.1f} GB，低于设置的 {threshold} GB 阈值。建议使用 Broom 清理磁盘。",
        "pref_title": "偏好设置",
        "pref_style": "显示风格",
        "pref_threshold": "空间不足提醒阈值",
        "pref_launch": "开机自动启动",
        "pref_save": "保存",
        "pref_cancel": "取消",
        "update_check": "检查更新",
        "update_latest": "已是最新版本 (v{version})",
        "update_available": "发现新版本 v{version}！\n请访问 {url} 下载。",
    },
    "en": {
        "app_name": "broom-widget",
        "broom_clean": "Broom Clean",
        "low_space_alert": "Low Space Alert",
        "launch_at_startup": "Launch at Startup",
        "enable": "Enable",
        "disable": "Disable",
        "display_style": "Display Style",
        "pie": "Pie Chart",
        "text": "Text Only",
        "bar": "Progress Bar",
        "quit": "Quit",
        "about": "About",
        "preferences": "Preferences",
        "uninstall": "Uninstall",
        "used": "Used",
        "free": "Free",
        "total": "Total",
        "broom_desc": "Broom is an AI agent-powered smart disk cleanup tool.\nIt helps you analyze caches, downloads, and app data,\nwhile letting you customize cleanup plans safely.",
        "install_method": "[Installation]",
        "step1": "1. Copy the following and send to your agent:",
        "install_cmd": "Use https://github.com/hisunfei/broom to clean my computer;",
        "step2": "2. After first install, it auto-cleans once. Then just say \"broom\" to your Agent.",
        "step3": "3. For automatic cleanup, tell your agent:",
        "schedule_cmd": "Every Monday at 10am, use broom skill to auto-clean my computer (https://github.com/hisunfei/broom);",
        "close": "Close",
        "welcome_title": "Welcome to broom-widget",
        "welcome_msg": "broom-widget is running!\n\nIt shows your disk space in the menu bar.\nClick the menu bar icon to:\n• View Broom cleanup instructions\n• Set low space alerts\n• Change display style\n• Enable launch at startup",
        "ok": "OK",
        "about_title": "About broom-widget",
        "about_msg": f"broom-widget v{APP_VERSION}\n\nmacOS menu bar disk monitor widget\nWorks with broom AI skill\n\nGitHub: {WIDGET_GITHUB}\nbroom: {BROOM_GITHUB}\n\n© 2024 hisunfei. MIT License.",
        "uninstall_confirm": "Are you sure you want to uninstall broom-widget?\nThis will remove config files and launch agent.",
        "uninstall_done": "broom-widget uninstalled.\nConfig files removed.",
        "cancel": "Cancel",
        "already_running": "broom-widget is already running",
        "alert_low_space": "⚠️ Low Disk Space",
        "alert_msg_template": "Only {free:.1f} GB free, below your {threshold} GB threshold. Consider using Broom to clean up.",
        "pref_title": "Preferences",
        "pref_style": "Display Style",
        "pref_threshold": "Low Space Alert Threshold",
        "pref_launch": "Launch at Startup",
        "pref_save": "Save",
        "pref_cancel": "Cancel",
        "update_check": "Check for Updates",
        "update_latest": "You're up to date (v{version})",
        "update_available": "New version v{version} available!\nVisit {url} to download.",
    },
}

def t(key, **kwargs):
    """翻译"""
    text = I18N.get(LANG, I18N["en"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

# ─── 配置管理 ───────────────────────────────────────────
CONFIG_DIR = Path.home() / "Library" / "Application Support" / "broom-widget"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "style": "pie",
    "alert_threshold_gb": 5,
    "launch_at_startup": False,
    "first_launch": True,
    "last_update_check": 0,
}

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# ─── LaunchAgent ────────────────────────────────────────
LAUNCHAGENT_DIR = Path.home() / "Library" / "LaunchAgents"
LAUNCHAGENT_FILE = LAUNCHAGENT_DIR / "com.broom.widget.plist"

def get_python_path():
    return sys.executable

def get_script_path():
    return str(Path(__file__).resolve())

def create_launchagent():
    LAUNCHAGENT_DIR.mkdir(parents=True, exist_ok=True)
    python_path = get_python_path()
    script_path = get_script_path()
    
    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.broom.widget</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>ProcessType</key>
    <string>Background</string>
    <key>LimitLoadToSessionType</key>
    <string>Aqua</string>
</dict>
</plist>'''
    
    with open(LAUNCHAGENT_FILE, "w") as f:
        f.write(plist)
    
    uid = os.getuid()
    result = subprocess.run(
        ["launchctl", "bootstrap", f"gui/{uid}", str(LAUNCHAGENT_FILE)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        subprocess.run(["launchctl", "load", str(LAUNCHAGENT_FILE)],
                       capture_output=True, text=True)
    logger.info(f"LaunchAgent created: {LAUNCHAGENT_FILE}")

def remove_launchagent():
    if LAUNCHAGENT_FILE.exists():
        uid = os.getuid()
        result = subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/com.broom.widget"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            subprocess.run(["launchctl", "unload", str(LAUNCHAGENT_FILE)],
                           capture_output=True, text=True)
        LAUNCHAGENT_FILE.unlink()
        logger.info(f"LaunchAgent removed: {LAUNCHAGENT_FILE}")

# ─── 常量 ───────────────────────────────────────────────
ALERT_THRESHOLDS = {1: "1 GB", 3: "3 GB", 5: "5 GB", 10: "10 GB"}

STYLE_PIE = "pie"
STYLE_TEXT = "text"
STYLE_BAR = "bar"
STYLE_LABELS = {STYLE_PIE: "pie", STYLE_TEXT: "text", STYLE_BAR: "bar"}

# ─── 单实例锁 ───────────────────────────────────────────
LOCK_FILE = Path("/tmp/broom-widget.lock")

def acquire_lock():
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        return lock_fd
    except (IOError, OSError):
        logger.warning(t("already_running"))
        sys.exit(0)

def release_lock(lock_fd):
    try:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        lock_fd.close()
        LOCK_FILE.unlink(missing_ok=True)
    except:
        pass

# ─── 图形绘制 ───────────────────────────────────────────
def _new_bitmap(w, h):
    scale = 2
    pw, ph = w * scale, h * scale
    bmp = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, pw, ph, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0,
    )
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(bmp)
    return bmp, ctx, scale, pw, ph

def _finish_image(bmp, w, h):
    img = NSImage.alloc().initWithSize_(NSMakeSize(w, h))
    img.addRepresentation_(bmp)
    img.setTemplate_(True)
    return img

def map_display_percentage(actual_pct):
    if actual_pct <= 0.9:
        return actual_pct / 0.9 * 0.8
    else:
        return 0.8 + (actual_pct - 0.9) / 0.1 * 0.2

def draw_pie_image(percentage, size=18):
    display_pct = map_display_percentage(percentage)
    bmp, ctx, s, pw, ph = _new_bitmap(size, size)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(ctx)
    
    cx, cy = pw / 2, ph / 2
    r = pw / 2 - 2 * s
    lw = 1.2 * s
    
    circle = NSBezierPath.bezierPathWithOvalInRect_(
        NSMakeRect(cx - r, cy - r, r * 2, r * 2)
    )
    NSColor.blackColor().setStroke()
    circle.setLineWidth_(lw)
    circle.stroke()
    
    if display_pct > 0.001:
        wedge = NSBezierPath.bezierPath()
        wedge.moveToPoint_(NSPoint(cx, cy))
        start = 90
        sweep = -display_pct * 360
        wedge.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
            NSPoint(cx, cy), r, start, start + sweep, False,
        )
        wedge.closePath()
        NSColor.blackColor().setFill()
        wedge.fill()
    
    NSGraphicsContext.restoreGraphicsState()
    return _finish_image(bmp, size, size)

def draw_bar_image(percentage, width=24, height=12):
    bmp, ctx, s, pw, ph = _new_bitmap(width, height)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(ctx)
    
    pad = 1 * s
    cr = 2.5 * s
    
    outer = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
        NSMakeRect(pad, pad, pw - pad * 2, ph - pad * 2), cr, cr
    )
    NSColor.blackColor().setStroke()
    outer.setLineWidth_(1.0 * s)
    outer.stroke()
    
    inner_pad = pad + 2 * s
    max_w = pw - inner_pad * 2
    fill_w = max(0, max_w * percentage)
    if fill_w > 0:
        fill = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(inner_pad, inner_pad, fill_w, ph - inner_pad * 2),
            max(cr - 1 * s, 0), max(cr - 1 * s, 0),
        )
        NSColor.blackColor().setFill()
        fill.fill()
    
    NSGraphicsContext.restoreGraphicsState()
    return _finish_image(bmp, width, height)

# ─── 磁盘信息 ───────────────────────────────────────────
def get_disk_info():
    home = NSHomeDirectory()
    stat = os.statvfs(home)
    total = stat.f_blocks * stat.f_frsize
    free = stat.f_bavail * stat.f_frsize
    used = total - free
    pct = used / total if total > 0 else 0
    return {
        "total": total, "free": free, "used": used, "percentage": pct,
        "totalGB": total / (1024 ** 3),
        "freeGB": free / (1024 ** 3),
        "usedGB": used / (1024 ** 3),
    }

def fmt_size(gb):
    if gb >= 1000:
        return f"{gb / 1024:.1f} TB"
    return f"{gb:.0f} GB"

# ─── 对话框 ─────────────────────────────────────────────
def show_broom_ad():
    alert = NSAlert.alloc().init()
    alert.setMessageText_(t("broom_clean"))
    alert.setInformativeText_(
        t("broom_desc") + "\n\n" +
        t("install_method") + "\n\n" +
        t("step1") + '\n"' + t("install_cmd") + '"\n\n' +
        t("step2") + "\n\n" +
        t("step3") + '\n"' + t("schedule_cmd") + '"'
    )
    alert.addButtonWithTitle_(t("close"))
    alert.runModal()

def show_about():
    alert = NSAlert.alloc().init()
    alert.setMessageText_(t("about_title"))
    alert.setInformativeText_(t("about_msg"))
    alert.addButtonWithTitle_(t("ok"))
    alert.runModal()

def show_welcome():
    alert = NSAlert.alloc().init()
    alert.setMessageText_(t("welcome_title"))
    alert.setInformativeText_(t("welcome_msg"))
    alert.addButtonWithTitle_(t("ok"))
    alert.runModal()

def show_uninstall_confirm():
    alert = NSAlert.alloc().init()
    alert.setMessageText_(t("uninstall"))
    alert.setInformativeText_(t("uninstall_confirm"))
    alert.addButtonWithTitle_(t("uninstall"))
    alert.addButtonWithTitle_(t("cancel"))
    return alert.runModal() == 1000

def show_uninstall_done():
    alert = NSAlert.alloc().init()
    alert.setMessageText_(t("uninstall"))
    alert.setInformativeText_(t("uninstall_done"))
    alert.addButtonWithTitle_(t("ok"))
    alert.runModal()

def do_uninstall():
    """卸载：删除配置、LaunchAgent、锁文件"""
    remove_launchagent()
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    LOCK_FILE.unlink(missing_ok=True)
    logger.info("Uninstalled")

# ─── 偏好设置窗口 ───────────────────────────────────────
class PreferencesWindow(NSObject):
    def __init__(self, config, on_save):
        self.config = config.copy()
        self.on_save = on_save
        self.window = None
        
        self.createWindow()
    
    def createWindow(self):
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 360, 280),
            NSTitledWindowMask | NSClosableWindowMask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_(t("pref_title"))
        self.window.center()
        self.window.setHidesOnDeactivate_(False)
        self.window.setLevel_(3)
        self.window.setDelegate_(self)
        
        content = self.window.contentView()
        y = 240
        
        # 显示风格
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, 120, 20))
        label.setStringValue_(t("pref_style"))
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        content.addSubview_(label)
        
        self.style_popup = NSMenu.alloc().init()
        for key in [STYLE_PIE, STYLE_TEXT, STYLE_BAR]:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t(key), "", "")
            item.setRepresentedObject_(key)
            if key == config.get("style", STYLE_PIE):
                item.setState_(1)
            self.style_popup.addItem_(item)
        
        style_btn = NSButton.alloc().initWithFrame_(NSMakeRect(150, y - 4, 120, 24))
        style_btn.setTitle_(t(config.get("style", STYLE_PIE)))
        style_btn.setBezelStyle_(3)
        style_btn.setTarget_(self)
        style_btn.setAction_("changeStyle:")
        content.addSubview_(style_btn)
        self.style_btn = style_btn
        
        y -= 50
        
        # 提醒阈值
        label2 = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, 120, 20))
        label2.setStringValue_(t("pref_threshold"))
        label2.setBezeled_(False)
        label2.setDrawsBackground_(False)
        label2.setEditable_(False)
        label2.setSelectable_(False)
        content.addSubview_(label2)
        
        self.threshold_popup = NSMenu.alloc().init()
        for gb, label_text in ALERT_THRESHOLDS.items():
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label_text, "", "")
            item.setRepresentedObject_(gb)
            if gb == config.get("alert_threshold_gb", 5):
                item.setState_(1)
            self.threshold_popup.addItem_(item)
        
        threshold_btn = NSButton.alloc().initWithFrame_(NSMakeRect(150, y - 4, 120, 24))
        threshold_btn.setTitle_(ALERT_THRESHOLDS.get(config.get("alert_threshold_gb", 5), "5 GB"))
        threshold_btn.setBezelStyle_(3)
        threshold_btn.setTarget_(self)
        threshold_btn.setAction_("changeThreshold:")
        content.addSubview_(threshold_btn)
        self.threshold_btn = threshold_btn
        
        y -= 50
        
        # 开机启动
        self.launch_switch = NSSwitchButton.alloc().initWithFrame_(NSMakeRect(20, y - 4, 200, 24))
        self.launch_switch.setTitle_(t("pref_launch"))
        self.launch_switch.setState_(1 if config.get("launch_at_startup", False) else 0)
        content.addSubview_(self.launch_switch)
        
        y -= 60
        
        # 保存按钮
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(130, y, 100, 30))
        save_btn.setTitle_(t("pref_save"))
        save_btn.setBezelStyle_(3)
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        content.addSubview_(save_btn)
    
    def changeStyle_(self, sender):
        # 弹出菜单
        menu = NSMenu.alloc().init()
        for key in [STYLE_PIE, STYLE_TEXT, STYLE_BAR]:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t(key), "selectStyle:", "")
            item.setTarget_(self)
            item.setRepresentedObject_(key)
            if key == self.config.get("style", STYLE_PIE):
                item.setState_(1)
            menu.addItem_(item)
        NSMenu.popUpContextMenu_withEvent_forView_(menu, None, sender)
    
    def selectStyle_(self, sender):
        key = sender.representedObject()
        if key:
            self.config["style"] = key
            self.style_btn.setTitle_(t(key))
            for item in sender.menu().itemArray():
                item.setState_(1 if item.representedObject() == key else 0)
    
    def changeThreshold_(self, sender):
        menu = NSMenu.alloc().init()
        for gb, label_text in ALERT_THRESHOLDS.items():
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label_text, "selectThreshold:", "")
            item.setTarget_(self)
            item.setRepresentedObject_(gb)
            if gb == self.config.get("alert_threshold_gb", 5):
                item.setState_(1)
            menu.addItem_(item)
        NSMenu.popUpContextMenu_withEvent_forView_(menu, None, sender)
    
    def selectThreshold_(self, sender):
        gb = sender.representedObject()
        if gb:
            self.config["alert_threshold_gb"] = gb
            self.threshold_btn.setTitle_(ALERT_THRESHOLDS.get(gb, "5 GB"))
            for item in sender.menu().itemArray():
                item.setState_(1 if item.representedObject() == gb else 0)
    
    def save_(self, sender):
        self.config["launch_at_startup"] = self.launch_switch.state() == 1
        self.on_save(self.config)
        self.window.close()

# ─── 自动更新检查 ───────────────────────────────────────
def check_for_updates(force=False):
    """检查更新（非阻塞）"""
    config = load_config()
    last_check = config.get("last_update_check", 0)
    now = time.time()
    
    if not force and (now - last_check) < 86400:  # 每天检查一次
        return
    
    try:
        import urllib.request
        url = f"{WIDGET_GITHUB}/releases/latest"
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "broom-widget")
        response = urllib.request.urlopen(req, timeout=5)
        # 简单检查：如果响应正常，说明有 release
        config["last_update_check"] = now
        save_config(config)
        logger.info("Update check completed")
    except Exception as e:
        logger.warning(f"Update check failed: {e}")

# ─── 主类 ───────────────────────────────────────────────
class DiskMonitor(NSObject):
    
    statusItem = None
    timer = None
    currentStyle = STYLE_PIE
    diskInfo = None
    config = None
    lastAlertTime = 0
    prefWindow = None
    
    def init(self):
        self = objc.super(DiskMonitor, self).init()
        if self is None:
            return None
        
        self.config = load_config()
        self.currentStyle = self.config.get("style", STYLE_PIE)
        self.diskInfo = get_disk_info()
        
        self.setupStatusItem()
        self.renderStatusItem()
        
        # 首次启动欢迎
        if self.config.get("first_launch", True):
            self.config["first_launch"] = False
            save_config(self.config)
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                1.0, self, "showWelcome:", None, False
            )
        
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            60.0, self, "tick:", None, True,
        )
        
        # 后台检查更新
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            5.0, self, "checkUpdates:", None, False
        )
        
        return self
    
    def setupStatusItem(self):
        self.statusItem = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        btn = self.statusItem.button()
        btn.setAction_("statusItemClicked:")
        btn.setTarget_(self)
        self.buildMenu()
    
    def buildMenu(self):
        menu = NSMenu.alloc().init()
        
        # Broom 清理
        broomItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            t("broom_clean"), "showBroomAd:", ""
        )
        broomItem.setTarget_(self)
        menu.addItem_(broomItem)
        
        menu.addItem_(NSMenuItem.separatorItem())
        
        # 空间不足提醒
        alertItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("low_space_alert"), "", "")
        alertSubmenu = NSMenu.alloc().init()
        for gb, label in ALERT_THRESHOLDS.items():
            mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label, "setAlertThreshold:", "")
            mi.setTarget_(self)
            mi.setRepresentedObject_(gb)
            if gb == self.config.get("alert_threshold_gb", 5):
                mi.setState_(1)
            alertSubmenu.addItem_(mi)
        alertItem.setSubmenu_(alertSubmenu)
        menu.addItem_(alertItem)
        
        # 开机启动
        launchItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("launch_at_startup"), "", "")
        launchSubmenu = NSMenu.alloc().init()
        
        enableItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("enable"), "enableLaunchAtStartup:", "")
        enableItem.setTarget_(self)
        if self.config.get("launch_at_startup", False):
            enableItem.setState_(1)
        launchSubmenu.addItem_(enableItem)
        
        disableItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("disable"), "disableLaunchAtStartup:", "")
        disableItem.setTarget_(self)
        if not self.config.get("launch_at_startup", False):
            disableItem.setState_(1)
        launchSubmenu.addItem_(disableItem)
        
        launchItem.setSubmenu_(launchSubmenu)
        menu.addItem_(launchItem)
        
        menu.addItem_(NSMenuItem.separatorItem())
        
        # 显示风格
        styleItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("display_style"), "", "")
        styleSubmenu = NSMenu.alloc().init()
        for key in [STYLE_PIE, STYLE_TEXT, STYLE_BAR]:
            mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t(key), "switchStyle:", "")
            mi.setTarget_(self)
            mi.setRepresentedObject_(key)
            if key == self.currentStyle:
                mi.setState_(1)
            styleSubmenu.addItem_(mi)
        styleItem.setSubmenu_(styleSubmenu)
        menu.addItem_(styleItem)
        
        menu.addItem_(NSMenuItem.separatorItem())
        
        # 关于
        aboutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("about"), "showAbout:", "")
        aboutItem.setTarget_(self)
        menu.addItem_(aboutItem)
        
        # 偏好设置
        prefItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("preferences"), "showPreferences:", "")
        prefItem.setTarget_(self)
        menu.addItem_(prefItem)
        
        # 卸载
        uninstallItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("uninstall"), "uninstall:", "")
        uninstallItem.setTarget_(self)
        menu.addItem_(uninstallItem)
        
        menu.addItem_(NSMenuItem.separatorItem())
        
        # 退出
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t("quit"), "quitClicked:", "q")
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)
        
        self.statusItem.setMenu_(menu)
    
    def renderStatusItem(self):
        btn = self.statusItem.button()
        pct = self.diskInfo["percentage"]
        freeGB = self.diskInfo["freeGB"]
        
        btn.setImage_(None)
        btn.setTitle_("")
        
        if self.currentStyle == STYLE_PIE:
            btn.setImage_(draw_pie_image(pct, size=18))
            btn.setTitle_(f" {fmt_size(freeGB)}")
        elif self.currentStyle == STYLE_TEXT:
            btn.setTitle_(fmt_size(freeGB))
        elif self.currentStyle == STYLE_BAR:
            btn.setImage_(draw_bar_image(pct, width=24, height=12))
            btn.setTitle_(f" {fmt_size(freeGB)}")
        
        self.updateDetailMenu()
    
    def updateDetailMenu(self):
        menu = self.statusItem.menu()
        info = self.diskInfo
        
        while menu.numberOfItems() > 0:
            t_title = menu.itemAtIndex_(0).title()
            if t_title in (t("broom_clean"), t("low_space_alert"), t("launch_at_startup"),
                          t("display_style"), t("about"), t("preferences"), t("uninstall"),
                          t("quit"), ""):
                break
            menu.removeItemAtIndex_(0)
        
        lines = [
            f"{t('used')}  {fmt_size(info['usedGB'])}  ({info['percentage']:.0%})",
            f"{t('free')}  {fmt_size(info['freeGB'])}",
            f"{t('total')}  {fmt_size(info['totalGB'])}",
        ]
        for i, line in enumerate(reversed(lines)):
            attr = NSMutableAttributedString.alloc().initWithString_(line)
            mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("", "", "")
            mi.setAttributedTitle_(attr)
            menu.insertItem_atIndex_(mi, i)
    
    # ── 事件 ────────────────────────────────────────────
    def tick_(self, _):
        self.diskInfo = get_disk_info()
        self.renderStatusItem()
        self.checkAlert()
    
    def statusItemClicked_(self, _):
        self.diskInfo = get_disk_info()
        self.renderStatusItem()
    
    def showBroomAd_(self, _):
        show_broom_ad()
    
    def showAbout_(self, _):
        show_about()
    
    def showWelcome_(self, _):
        show_welcome()
    
    def showPreferences_(self, _):
        if self.prefWindow is not None:
            self.prefWindow.window.makeKeyAndOrderFront_(None)
            return
        
        def on_save(config):
            self.config = config
            save_config(config)
            self.currentStyle = config.get("style", STYLE_PIE)
            self.renderStatusItem()
            
            # 更新开机启动
            if config.get("launch_at_startup", False):
                create_launchagent()
            else:
                remove_launchagent()
            
            self.prefWindow = None
        
        self.prefWindow = PreferencesWindow(self.config, on_save)
        self.prefWindow.window.makeKeyAndOrderFront_(None)
    
    def uninstall_(self, _):
        if show_uninstall_confirm():
            do_uninstall()
            show_uninstall_done()
            self.quitClicked_(None)
    
    def setAlertThreshold_(self, sender):
        gb = sender.representedObject()
        if gb and gb in ALERT_THRESHOLDS:
            self.config["alert_threshold_gb"] = gb
            save_config(self.config)
            for item in sender.menu().itemArray():
                if item.representedObject() in ALERT_THRESHOLDS:
                    item.setState_(1 if item.representedObject() == gb else 0)
            logger.info(f"Alert threshold set to: {ALERT_THRESHOLDS[gb]}")
    
    def enableLaunchAtStartup_(self, sender):
        self.config["launch_at_startup"] = True
        save_config(self.config)
        create_launchagent()
        menu = sender.menu()
        for item in menu.itemArray():
            if item.title() == t("enable"):
                item.setState_(1)
            elif item.title() == t("disable"):
                item.setState_(0)
        logger.info("Launch at startup enabled")
    
    def disableLaunchAtStartup_(self, sender):
        self.config["launch_at_startup"] = False
        save_config(self.config)
        remove_launchagent()
        menu = sender.menu()
        for item in menu.itemArray():
            if item.title() == t("enable"):
                item.setState_(0)
            elif item.title() == t("disable"):
                item.setState_(1)
        logger.info("Launch at startup disabled")
    
    def switchStyle_(self, sender):
        key = sender.representedObject()
        if key and key in STYLE_LABELS:
            self.currentStyle = key
            self.config["style"] = key
            save_config(self.config)
            for item in sender.menu().itemArray():
                if item.representedObject() in STYLE_LABELS:
                    item.setState_(1 if item.representedObject() == key else 0)
            self.renderStatusItem()
    
    def checkAlert(self):
        freeGB = self.diskInfo["freeGB"]
        threshold = self.config.get("alert_threshold_gb", 5)
        
        if freeGB < threshold:
            now = time.time()
            if now - self.lastAlertTime > 3600:
                self.lastAlertTime = now
                msg = t("alert_msg_template", free=freeGB, threshold=threshold)
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{msg}" with title "{t("alert_low_space")}" sound name "Basso"'
                ], capture_output=True)
                logger.info(f"Alert sent: {freeGB:.1f} GB < {threshold} GB")
    
    def checkUpdates_(self, _):
        check_for_updates()
    
    def quitClicked_(self, _):
        if self.timer:
            self.timer.invalidate()
        NSApplication.sharedApplication().terminate_(self)


# ─── 入口 ───────────────────────────────────────────────
def main():
    lock_fd = acquire_lock()
    logger.info(f"broom-widget v{APP_VERSION} starting (PID: {os.getpid()})")
    
    try:
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        
        # 设置应用图标
        icon_path = Path(__file__).parent / "icon" / "broom-widget.icns"
        if icon_path.exists():
            app_icon = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if app_icon:
                app.setApplicationIconImage_(app_icon)
                logger.info(f"App icon loaded: {icon_path}")
        
        monitor = DiskMonitor.alloc().init()
        
        logger.info("broom-widget started successfully")
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        release_lock(lock_fd)
        logger.info("broom-widget stopped")


if __name__ == "__main__":
    main()
