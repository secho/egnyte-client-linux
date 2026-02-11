use anyhow::Result;
use egnyte_fuse::fs::fuse_ops::{EgnyteAPI, EgnyteEntry, EgnyteFuse};
use fuser::MountOption;
use std::env;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::SystemTime;

/// Simple mock API client for testing (to be replaced with real implementation)
struct MockAPI;

#[async_trait::async_trait]
impl EgnyteAPI for MockAPI {
    async fn list_folder(&self, _path: &str) -> Result<Vec<EgnyteEntry>> {
        // Mock implementation - returns empty for now
        // In real implementation, this would call Egnyte API
        Ok(vec![])
    }

    async fn get_file_info(&self, path: &str) -> Result<EgnyteEntry> {
        // Mock implementation
        Ok(EgnyteEntry {
            name: PathBuf::from(path)
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string(),
            path: path.to_string(),
            is_folder: path == "/" || path.ends_with('/'),
            size: 0,
            modified_time: SystemTime::now(),
        })
    }

    async fn download_file(&self, _path: &str) -> Result<Vec<u8>> {
        // Mock implementation
        Ok(vec![])
    }
}

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <mountpoint>", args[0]);
        std::process::exit(1);
    }

    let mountpoint = &args[1];
    let mount_path = PathBuf::from(mountpoint);

    // Create API client (mock for now)
    let api_client: Arc<dyn EgnyteAPI> = Arc::new(MockAPI);

    // Create FUSE filesystem
    let fs = EgnyteFuse::new(api_client)?;

    // Mount options: writeback cache, parallel dirops
    let options = vec![
        MountOption::RW,
        MountOption::FSName("egnyte".to_string()),
        MountOption::Subtype("egnyte-fuse".to_string()),
        MountOption::AllowOther,
    ];

    // Mount the filesystem
    fuser::mount2(fs, mount_path, &options)?;

    Ok(())
}
