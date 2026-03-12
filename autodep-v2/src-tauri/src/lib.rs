
use std::process::Command;

#[tauri::command]
fn analyze_project(project_path: String) -> Result<String, String> {
    let jar_path = "/home/igor/projetos/tcc/structural/target/structural-1.0-SNAPSHOT-jar-with-dependencies.jar";
    
    let output = Command::new("java")
        .arg("-jar")
        .arg(jar_path)
        .arg(&project_path)
        .output()
        .map_err(|e| format!("Failed to execute Java command: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        Err(format!("Analysis failed with error: {}", stderr))
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_dialog::init())
    .invoke_handler(tauri::generate_handler![analyze_project])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
