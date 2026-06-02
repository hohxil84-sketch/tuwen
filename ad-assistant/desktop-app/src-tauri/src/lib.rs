// S04-T07: Tauri 2 库入口 — 最小应用启动，不注册自定义命令
// S05-R08: 接入 Windows 原生窗口阴影（window-shadows-v2 crate → DWM API）
// 后续任务如需添加 Tauri commands，在对应任务单授权下扩展

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // 为所有窗口启用平台原生阴影
            // - Windows: DwmExtendFrameIntoClientArea + DWMWA_USE_IMMERSIVE_DARK_MODE
            // - macOS:   NSWindow.hasShadow
            // - Linux:   无操作（平台不支持）
            window_shadows_v2::set_shadows(app, true);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("启动 Tauri 应用时发生错误");
}
