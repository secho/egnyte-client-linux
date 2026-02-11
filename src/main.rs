use anyhow::{Context, Result};
use egnyte_fuse::fs::api_client::EgnyteAPIClient;
use egnyte_fuse::fs::fuse_ops::EgnyteFuse;
use fuser::MountOption;
use std::env;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::runtime::Runtime;

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <mountpoint>", args[0]);
        eprintln!("\nExample: {} /mnt/egnyte", args[0]);
        eprintln!("\nNote: Make sure you have:");
        eprintln!("  1. Configured domain: egnyte-cli config set domain YOUR_DOMAIN");
        eprintln!("  2. Authenticated: egnyte-cli auth login");
        std::process::exit(1);
    }

    let mountpoint = &args[1];
    let mount_path = PathBuf::from(mountpoint);

    // Create Tokio runtime for async operations
    let rt = Runtime::new().context("Failed to create Tokio runtime")?;

    // Create real API client (loads config and tokens from ~/.config/egnyte-desktop/)
    let api_client = rt.block_on(async {
        EgnyteAPIClient::new()
            .await
            .context("Failed to create API client. Make sure you have configured and authenticated.")
    })?;

    // Create FUSE filesystem
    let api_client: Arc<dyn egnyte_fuse::fs::fuse_ops::EgnyteAPI> = Arc::new(api_client);
    let fs = EgnyteFuse::new(api_client)?;

    // Mount options: writeback cache, parallel dirops
    let options = vec![
        MountOption::RW,
        MountOption::FSName("egnyte".to_string()),
        MountOption::Subtype("egnyte-fuse".to_string()),
        MountOption::AllowOther,
        MountOption::AutoUnmount,
    ];

    println!("Mounting Egnyte filesystem at {}...", mountpoint);
    println!("Press Ctrl+C to unmount");

    // Mount the filesystem (this blocks until unmounted)
    fuser::mount2(fs, mount_path, &options)?;

    Ok(())
}
