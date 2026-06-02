// S04-T07: Tauri 2 库入口 — 最小应用启动，不注册自定义命令
// 后续任务如需添加 Tauri commands，在对应任务单授权下扩展

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("启动 Tauri 应用时发生错误");
}
