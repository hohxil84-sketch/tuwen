// S04-T07: Tauri 2 最小入口 — 窗口创建和平台初始化
// 禁止在 main 中扩展非任务单授权功能（不添加托盘、全局快捷键、自动启动、updater）

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    ad_assistant_desktop_lib::run()
}
