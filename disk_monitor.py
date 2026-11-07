#!/usr/bin/env python3
"""
broom-桌面 - macOS 菜单栏磁盘监控工具
配合 broom skill 使用，一键清理磁盘空间
"""

import objc
import os
import json
import subprocess
from pathlib import Path
from Foundation import NSHomeDirectory, NSMakeRect, NSMakeSize, NSPoint
from AppKit import (
    NSApplication, NSStatusBar, NSStatusItem,
    NSMenu, NSMenuItem, NSVariableStatusItemLength,
    NSApplicationActivationPolicyAccessory,
    NSImage, NSBitmapImageRep, NSGraphicsContext,
    NSBezierPath, NSColor, NSDeviceRGBColorSpace,
    NSMutableAttributedString, NSAlert, NSTextView,
    NSScrollView, NSTimer, NSObject,
)

# ─── 配置管理 ───────────────────────────────────────────
CONFIG_DIR = Path.home() / "Library" / "Application Support" / "broom-desktop"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "style": "pie",
    "alert_threshold_gb": 5,  # 默认 5GB 提醒
    "launch_at_startup": False,  # 默认不开机启动
}

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in config:
                        config[k] = v
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# ─── LaunchAgent 管理 ───────────────────────────────────
LAUNCHAGENT_DIR = Path.home() / "Library" / "LaunchAgents"
LAUNCHAGENT_FILE = LAUNCHAGENT_DIR / "com.broom.desktop.plist"

def get_python_path():
    """获取 Python 解释器路径"""
    import sys
    return sys.executable

def get_script_path():
    """获取脚本路径"""
    return str(Path(__file__).resolve())

def create_launchagent():
    """创建 LaunchAgent plist 文件"""
    LAUNCHAGENT_DIR.mkdir(parents=True, exist_ok=True)
    
    python_path = get_python_path()
    script_path = get_script_path()
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.broom.desktop</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>LaunchEvents</key>
    <dict/>
</dict>
</plist>
'''
    
    with open(LAUNCHAGENT_FILE, "w") as f:
        f.write(plist_content)
    
    # 加载 LaunchAgent
    subprocess.run(["launchctl", "load", str(LAUNCHAGENT_FILE)], 
                   capture_output=True)
    print(f"已创建 LaunchAgent: {LAUNCHAGENT_FILE}")

def remove_launchagent():
    """删除 LaunchAgent plist 文件"""
    if LAUNCHAGENT_FILE.exists():
        # 卸载 LaunchAgent
        subprocess.run(["launchctl", "unload", str(LAUNCHAGENT_FILE)], 
                       capture_output=True)
        LAUNCHAGENT_FILE.unlink()
        print(f"已删除 LaunchAgent: {LAUNCHAGENT_FILE}")

def is_launchagent_enabled():
    """检查 LaunchAgent 是否已启用"""
    return LAUNCHAGENT_FILE.exists()


# ─── 提醒阈值选项 ────────────────────────────────────────
ALERT_THRESHOLDS = {
    1: "1 GB",
    3: "3 GB",
    5: "5 GB",
    10: "10 GB",
}

# ─── 风格常量 ───────────────────────────────────────────
STYLE_PIE = "pie"
STYLE_TEXT = "text"
STYLE_BAR = "bar"

STYLE_LABELS = {
    STYLE_PIE: "饼图",
    STYLE_TEXT: "纯文字",
    STYLE_BAR: "进度条",
}


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
    """非线性映射：0-90% → 0-80%，90-100% → 80-100%"""
    if actual_pct <= 0.9:
        return actual_pct / 0.9 * 0.8
    else:
        return 0.8 + (actual_pct - 0.9) / 0.1 * 0.2


def draw_pie_image(percentage, size=18):
    """绘制黑白饼图图标"""
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
    """绘制黑白小进度条"""
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


# ─── 磁盘信息 ────────────────────────────────────────────
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


# ─── broom 广告 ─────────────────────────────────────────
from AppKit import NSAlert

def show_broom_ad():
    """显示 broom skill 介绍"""
    alert = NSAlert.alloc().init()
    alert.setMessageText_("Broom 清理")
    alert.setInformativeText_(
        "Broom 是一个 AI agent 驱动的智能磁盘清理工具。\n"
        "你可以使用它了解当前电脑的缓存、下载、应用数据等，\n"
        "同时自己定制清理方案，安全地释放空间。\n\n"
        "【安装方法】\n\n"
        "1、复制以下信息发送给你的 agent：\n"
        "\"使用https://github.com/hisunfei/broom，为我清理电脑；\"\n\n"
        "2、首次安装后会自动清理一次，后续只需对 Agent 说：\"broom\"即可开始清理。\n\n"
        "3、如果你想让它自动进行清理，可以告诉 agent：\n"
        "\"每周一上午10 点，使用broom skill自动为我清理电脑（https://github.com/hisunfei/broom）；\""
    )
    alert.addButtonWithTitle_("关闭")
    alert.runModal()


# ─── 主类 ────────────────────────────────────────────────
class DiskMonitor(NSObject):

    statusItem = None
    timer = None
    currentStyle = STYLE_PIE
    diskInfo = None
    config = None
    lastAlertTime = 0

    def init(self):
        self = objc.super(DiskMonitor, self).init()
        if self is None:
            return None
        
        self.config = load_config()
        self.currentStyle = self.config.get("style", STYLE_PIE)
        self.diskInfo = get_disk_info()
        self.setupStatusItem()
        self.renderStatusItem()
        
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            60.0, self, "tick:", None, True,
        )
        return self

    # ── 菜单栏 ──────────────────────────────────────────
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
            "Broom 清理", "showBroomAd:", ""
        )
        broomItem.setTarget_(self)
        menu.addItem_(broomItem)

        menu.addItem_(NSMenuItem.separatorItem())

        # 空间不足提醒
        alertItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("空间不足提醒", "", "")
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

        menu.addItem_(NSMenuItem.separatorItem())

        # 开机启动
        launchItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("开机启动", "", "")
        launchSubmenu = NSMenu.alloc().init()
        
        enableItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("启用", "enableLaunchAtStartup:", "")
        enableItem.setTarget_(self)
        if self.config.get("launch_at_startup", False):
            enableItem.setState_(1)
        launchSubmenu.addItem_(enableItem)
        
        disableItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("禁用", "disableLaunchAtStartup:", "")
        disableItem.setTarget_(self)
        if not self.config.get("launch_at_startup", False):
            disableItem.setState_(1)
        launchSubmenu.addItem_(disableItem)
        
        launchItem.setSubmenu_(launchSubmenu)
        menu.addItem_(launchItem)

        menu.addItem_(NSMenuItem.separatorItem())

        # 显示风格
        styleItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("显示风格", "", "")
        styleSubmenu = NSMenu.alloc().init()
        for key, label in STYLE_LABELS.items():
            mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label, "switchStyle:", "")
            mi.setTarget_(self)
            mi.setRepresentedObject_(key)
            if key == self.currentStyle:
                mi.setState_(1)
            styleSubmenu.addItem_(mi)
        styleItem.setSubmenu_(styleSubmenu)
        menu.addItem_(styleItem)

        menu.addItem_(NSMenuItem.separatorItem())

        # 退出
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("退出", "quitClicked:", "q")
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)

        self.statusItem.setMenu_(menu)

    # ── 渲染 ────────────────────────────────────────────
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
            btn.setTitle_(f"{fmt_size(freeGB)} 可用")

        elif self.currentStyle == STYLE_BAR:
            btn.setImage_(draw_bar_image(pct, width=24, height=12))
            btn.setTitle_(f" {fmt_size(freeGB)}")

        self.updateDetailMenu()

    def updateDetailMenu(self):
        menu = self.statusItem.menu()
        info = self.diskInfo

        # 清除旧详情
        while menu.numberOfItems() > 0:
            t = menu.itemAtIndex_(0).title()
            if t in ("Broom 清理", "空间不足提醒", "显示风格", "退出", ""):
                break
            menu.removeItemAtIndex_(0)

        lines = [
            f"已用  {fmt_size(info['usedGB'])}  ({info['percentage']:.0%})",
            f"可用  {fmt_size(info['freeGB'])}",
            f"总计  {fmt_size(info['totalGB'])}",
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
        """显示 broom 广告"""
        show_broom_ad()

    def setAlertThreshold_(self, sender):
        """设置提醒阈值"""
        gb = sender.representedObject()
        if gb and gb in ALERT_THRESHOLDS:
            self.config["alert_threshold_gb"] = gb
            save_config(self.config)
            # 更新勾选状态
            for item in sender.menu().itemArray():
                if item.representedObject() in ALERT_THRESHOLDS:
                    item.setState_(1 if item.representedObject() == gb else 0)
            print(f"提醒阈值已设置为: {ALERT_THRESHOLDS[gb]}")

    def checkAlert(self):
        """检查是否需要提醒"""
        import time
        freeGB = self.diskInfo["freeGB"]
        threshold = self.config.get("alert_threshold_gb", 5)
        
        if freeGB < threshold:
            now = time.time()
            if now - self.lastAlertTime > 3600:
                self.lastAlertTime = now
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "可用空间仅剩 {freeGB:.1f} GB，低于设置的 {threshold} GB 阈值。建议使用 Broom 清理磁盘。" with title "⚠️ 磁盘空间不足" sound name "Basso"'
                ], capture_output=True)
                print(f"已发送提醒：可用空间 {freeGB:.1f} GB < 阈值 {threshold} GB")

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

    def enableLaunchAtStartup_(self, sender):
        """启用开机启动"""
        self.config["launch_at_startup"] = True
        save_config(self.config)
        create_launchagent()
        # 更新菜单勾选状态
        menu = sender.menu()
        for item in menu.itemArray():
            if item.title() == "启用":
                item.setState_(1)
            elif item.title() == "禁用":
                item.setState_(0)
        print("已启用开机启动")

    def disableLaunchAtStartup_(self, sender):
        """禁用开机启动"""
        self.config["launch_at_startup"] = False
        save_config(self.config)
        remove_launchagent()
        # 更新菜单勾选状态
        menu = sender.menu()
        for item in menu.itemArray():
            if item.title() == "启用":
                item.setState_(0)
            elif item.title() == "禁用":
                item.setState_(1)
        print("已禁用开机启动")

    def quitClicked_(self, _):
        if self.timer:
            self.timer.invalidate()
        NSApplication.sharedApplication().terminate_(self)


# ─── 入口 ────────────────────────────────────────────────
def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    monitor = DiskMonitor.alloc().init()

    print("broom-桌面 已启动")
    print("  菜单栏显示磁盘空间")
    print("  点击「了解 broom 清理工具」查看使用说明")
    print("  按 Ctrl+C 退出")

    app.run()


if __name__ == "__main__":
    main()
