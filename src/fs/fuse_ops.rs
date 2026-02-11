use crate::fs::inode_table::InodeTable;
use anyhow::{Context, Result};
use fuser::{
    FileAttr, FileType, Filesystem, ReplyAttr, ReplyData, ReplyDirectory, ReplyEntry,
    ReplyOpen, Request,
};
use std::ffi::OsStr;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, SystemTime};
use tokio::runtime::Runtime;
use tokio::sync::RwLock;

/// Egnyte API client interface (async)
#[async_trait::async_trait]
pub trait EgnyteAPI: Send + Sync {
    async fn list_folder(&self, path: &str) -> Result<Vec<EgnyteEntry>>;
    async fn get_file_info(&self, path: &str) -> Result<EgnyteEntry>;
    async fn download_file(&self, path: &str) -> Result<Vec<u8>>;
}

/// Entry from Egnyte API
#[derive(Debug, Clone)]
pub struct EgnyteEntry {
    pub name: String,
    pub path: String,
    pub is_folder: bool,
    pub size: u64,
    pub modified_time: SystemTime,
}

/// FUSE filesystem implementation for Egnyte
pub struct EgnyteFuse {
    /// Inode table for path <-> inode mapping
    inode_table: Arc<InodeTable>,
    /// Tokio runtime for async operations
    rt: Arc<Runtime>,
    /// API client
    api_client: Arc<dyn EgnyteAPI>,
    /// Open file handles (inode -> file data)
    open_files: Arc<RwLock<std::collections::HashMap<u64, Vec<u8>>>>,
}

impl EgnyteFuse {
    /// Create a new EgnyteFuse filesystem
    pub fn new(api_client: Arc<dyn EgnyteAPI>) -> Result<Self> {
        let rt = Runtime::new().context("Failed to create Tokio runtime")?;
        
        Ok(Self {
            inode_table: Arc::new(InodeTable::new()),
            rt: Arc::new(rt),
            api_client,
            open_files: Arc::new(RwLock::new(std::collections::HashMap::new())),
        })
    }

    /// Convert path to Egnyte API path
    fn to_egnyte_path(&self, path: &Path) -> String {
        let path_str = path.to_string_lossy();
        if path_str == "/" {
            "/".to_string()
        } else {
            path_str.to_string()
        }
    }

    /// Get file attributes for a path
    fn get_attr_internal(&self, path: &Path) -> Result<FileAttr> {
        let egnyte_path = self.to_egnyte_path(path);
        let entry = self
            .rt
            .block_on(self.api_client.get_file_info(&egnyte_path))
            .context("Failed to get file info")?;

        let inode = self.inode_table.get_or_create_inode(path);
        let file_type = if entry.is_folder {
            FileType::Directory
        } else {
            FileType::RegularFile
        };

        let attr = FileAttr {
            ino: inode,
            size: entry.size,
            blocks: (entry.size + 511) / 512, // 512-byte blocks
            atime: entry.modified_time,
            mtime: entry.modified_time,
            ctime: entry.modified_time,
            crtime: entry.modified_time,
            kind: file_type,
            perm: if entry.is_folder { 0o755 } else { 0o644 },
            nlink: 1,
            uid: unsafe { libc::getuid() },
            gid: unsafe { libc::getgid() },
            rdev: 0,
            flags: 0,
            blksize: 512,
        };

        Ok(attr)
    }

    /// Read directory entries
    fn readdir_internal(&self, path: &Path) -> Result<Vec<(u64, FileType, String)>> {
        let egnyte_path = self.to_egnyte_path(path);
        let entries = self
            .rt
            .block_on(self.api_client.list_folder(&egnyte_path))
            .context("Failed to list folder")?;

        let mut result = Vec::new();
        
        // Add "." and ".." entries
        let current_inode = self.inode_table.get_or_create_inode(path);
        result.push((current_inode, FileType::Directory, ".".to_string()));
        
        if path != Path::new("/") {
            if let Some(parent) = path.parent() {
                let parent_inode = self.inode_table.get_or_create_inode(parent);
                result.push((parent_inode, FileType::Directory, "..".to_string()));
            }
        } else {
            result.push((current_inode, FileType::Directory, "..".to_string()));
        }

        // Add directory entries
        for entry in entries {
            let entry_path = if path == Path::new("/") {
                Path::new("/").join(&entry.name)
            } else {
                path.join(&entry.name)
            };
            
            let inode = self.inode_table.get_or_create_inode(&entry_path);
            let file_type = if entry.is_folder {
                FileType::Directory
            } else {
                FileType::RegularFile
            };
            
            result.push((inode, file_type, entry.name));
        }

        Ok(result)
    }

    /// Read file content
    fn read_file_internal(&self, path: &Path) -> Result<Vec<u8>> {
        let egnyte_path = self.to_egnyte_path(path);
        self.rt
            .block_on(self.api_client.download_file(&egnyte_path))
            .context("Failed to download file")
    }
}

impl Filesystem for EgnyteFuse {
    fn init(
        &mut self,
        _req: &Request<'_>,
        config: &mut fuser::KernelConfig,
    ) -> Result<(), libc::c_int> {
        // Configure FUSE: writeback cache, parallel dirops, max_readahead 256KB, max_write 1MB
        let _ = config.set_max_readahead(256 * 1024);
        let _ = config.set_max_write(1024 * 1024);
        Ok(())
    }

    fn lookup(&mut self, _req: &Request<'_>, parent: u64, name: &OsStr, reply: ReplyEntry) {
        // Bridge to Tokio runtime
        let inode_table = Arc::clone(&self.inode_table);
        let rt = Arc::clone(&self.rt);
        let api_client = Arc::clone(&self.api_client);
        let name_str = name.to_string_lossy().to_string();

        // Get parent path
        let parent_path = match inode_table.get_path(parent) {
            Some(p) => p,
            None => {
                reply.error(libc::ENOENT);
                return;
            }
        };

        // Build child path
        let child_path = if parent_path == PathBuf::from("/") {
            PathBuf::from("/").join(&name_str)
        } else {
            parent_path.join(&name_str)
        };

        // Spawn onto Tokio runtime
        let handle = rt.spawn(async move {
            let egnyte_path = if child_path == PathBuf::from("/") {
                "/".to_string()
            } else {
                child_path.to_string_lossy().to_string()
            };

            // Get file info from API
            let entry = match api_client.get_file_info(&egnyte_path).await {
                Ok(e) => e,
                Err(_) => return Err(libc::ENOENT),
            };

            // Get or create inode
            let inode = inode_table.get_or_create_inode(&child_path);

            // Build file attributes
            let file_type = if entry.is_folder {
                FileType::Directory
            } else {
                FileType::RegularFile
            };

            let attr = FileAttr {
                ino: inode,
                size: entry.size,
                blocks: (entry.size + 511) / 512,
                atime: entry.modified_time,
                mtime: entry.modified_time,
                ctime: entry.modified_time,
                crtime: entry.modified_time,
                kind: file_type,
                perm: if entry.is_folder { 0o755 } else { 0o644 },
                nlink: 1,
                uid: unsafe { libc::getuid() },
                gid: unsafe { libc::getgid() },
                rdev: 0,
                flags: 0,
                blksize: 512,
            };

            Ok((inode, attr, Duration::from_secs(1)))
        });

        // Block on the result
        match rt.block_on(handle) {
            Ok(Ok((_inode, attr, ttl))) => {
                reply.entry(&ttl, &attr, 0);
            }
            _ => {
                reply.error(libc::ENOENT);
            }
        }
    }

    fn getattr(&mut self, _req: &Request<'_>, inode: u64, reply: ReplyAttr) {
        let inode_table = Arc::clone(&self.inode_table);
        let rt = Arc::clone(&self.rt);
        let api_client = Arc::clone(&self.api_client);

        let path = match inode_table.get_path(inode) {
            Some(p) => p,
            None => {
                reply.error(libc::ENOENT);
                return;
            }
        };

        let handle = rt.spawn(async move {
            let egnyte_path = if path == PathBuf::from("/") {
                "/".to_string()
            } else {
                path.to_string_lossy().to_string()
            };

            let entry = match api_client.get_file_info(&egnyte_path).await {
                Ok(e) => e,
                Err(_) => return Err(libc::ENOENT),
            };

            let file_type = if entry.is_folder {
                FileType::Directory
            } else {
                FileType::RegularFile
            };

            let attr = FileAttr {
                ino: inode,
                size: entry.size,
                blocks: (entry.size + 511) / 512,
                atime: entry.modified_time,
                mtime: entry.modified_time,
                ctime: entry.modified_time,
                crtime: entry.modified_time,
                kind: file_type,
                perm: if entry.is_folder { 0o755 } else { 0o644 },
                nlink: 1,
                uid: unsafe { libc::getuid() },
                gid: unsafe { libc::getgid() },
                rdev: 0,
                flags: 0,
                blksize: 512,
            };

            Ok((attr, Duration::from_secs(1)))
        });

        match rt.block_on(handle) {
            Ok(Ok((attr, ttl))) => {
                reply.attr(&ttl, &attr);
            }
            _ => {
                reply.error(libc::ENOENT);
            }
        }
    }

    fn readdir(
        &mut self,
        _req: &Request<'_>,
        inode: u64,
        _fh: u64,
        offset: i64,
        mut reply: ReplyDirectory,
    ) {
        let inode_table = Arc::clone(&self.inode_table);
        let rt = Arc::clone(&self.rt);
        let api_client = Arc::clone(&self.api_client);

        let path = match inode_table.get_path(inode) {
            Some(p) => p,
            None => {
                reply.error(libc::ENOENT);
                return;
            }
        };

        let handle = rt.spawn(async move {
            let egnyte_path = if path == PathBuf::from("/") {
                "/".to_string()
            } else {
                path.to_string_lossy().to_string()
            };

            let entries = match api_client.list_folder(&egnyte_path).await {
                Ok(e) => e,
                Err(_) => return Err(libc::ENOENT),
            };

            let mut dir_entries = Vec::new();

            // Add "." and ".."
            dir_entries.push((inode, FileType::Directory, ".".to_string()));
            if path == PathBuf::from("/") {
                dir_entries.push((inode, FileType::Directory, "..".to_string()));
            } else if let Some(parent) = path.parent() {
                let parent_inode = inode_table.get_or_create_inode(parent);
                dir_entries.push((parent_inode, FileType::Directory, "..".to_string()));
            }

            // Add directory entries
            for entry in entries {
                let entry_path = if path == PathBuf::from("/") {
                    PathBuf::from("/").join(&entry.name)
                } else {
                    path.join(&entry.name)
                };

                let entry_inode = inode_table.get_or_create_inode(&entry_path);
                let file_type = if entry.is_folder {
                    FileType::Directory
                } else {
                    FileType::RegularFile
                };

                dir_entries.push((entry_inode, file_type, entry.name.clone()));
            }

            Ok(dir_entries)
        });

        match rt.block_on(handle) {
            Ok(Ok(dir_entries)) => {
                let mut offset = offset as usize;
                for (ino, kind, name) in dir_entries {
                    offset += 1;
                    if reply.add(ino, offset as i64, kind, name.as_str()) {
                        break;
                    }
                }
                reply.ok();
            }
            _ => {
                reply.error(libc::ENOENT);
            }
        }
    }

    fn open(&mut self, _req: &Request<'_>, inode: u64, _flags: i32, reply: ReplyOpen) {
        let inode_table = Arc::clone(&self.inode_table);
        let rt = Arc::clone(&self.rt);
        let api_client = Arc::clone(&self.api_client);
        let open_files = Arc::clone(&self.open_files);

        let path = match inode_table.get_path(inode) {
            Some(p) => p,
            None => {
                reply.error(libc::ENOENT);
                return;
            }
        };

        // Check if it's a directory
        let egnyte_path = if path == PathBuf::from("/") {
            "/".to_string()
        } else {
            path.to_string_lossy().to_string()
        };

        let handle = rt.spawn(async move {
            let entry = match api_client.get_file_info(&egnyte_path).await {
                Ok(e) => e,
                Err(_) => return Err(libc::ENOENT),
            };

            if entry.is_folder {
                // Directories don't need file handles
                return Ok(0);
            }

            // Download file content
            let content = match api_client.download_file(&egnyte_path).await {
                Ok(c) => c,
                Err(_) => return Err(libc::EIO),
            };

            // Store in open_files
            {
                let mut files = open_files.write().await;
                files.insert(inode, content);
            }

            Ok(0)
        });

        match rt.block_on(handle) {
            Ok(Ok(_)) => {
                reply.opened(inode, 0);
            }
            _ => {
                reply.error(libc::ENOENT);
            }
        }
    }

    fn read(
        &mut self,
        _req: &Request<'_>,
        inode: u64,
        _fh: u64,
        offset: i64,
        size: u32,
        _flags: i32,
        _lock_owner: Option<u64>,
        reply: ReplyData,
    ) {
        let open_files = Arc::clone(&self.open_files);
        let rt = Arc::clone(&self.rt);

        let handle = rt.spawn(async move {
            let files = open_files.read().await;
            let content = match files.get(&inode) {
                Some(c) => c,
                None => return Err(libc::EBADF),
            };

            let offset = offset as usize;
            let size = size as usize;
            let end = std::cmp::min(offset + size, content.len());

            if offset >= content.len() {
                return Ok(Vec::new());
            }

            Ok(content[offset..end].to_vec())
        });

        match rt.block_on(handle) {
            Ok(Ok(data)) => {
                reply.data(&data);
            }
            _ => {
                reply.error(libc::EBADF);
            }
        }
    }

    fn release(
        &mut self,
        _req: &Request<'_>,
        inode: u64,
        _fh: u64,
        _flags: i32,
        _lock_owner: Option<u64>,
        _flush: bool,
        reply: fuser::ReplyEmpty,
    ) {
        let open_files = Arc::clone(&self.open_files);
        let rt = Arc::clone(&self.rt);

        let handle: tokio::task::JoinHandle<Result<(), libc::c_int>> = rt.spawn(async move {
            let mut files = open_files.write().await;
            files.remove(&inode);
            Ok(())
        });

        match rt.block_on(handle) {
            Ok(Ok(_)) => {
                reply.ok();
            }
            _ => {
                reply.error(libc::EBADF);
            }
        }
    }
}

