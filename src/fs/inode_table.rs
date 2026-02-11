use dashmap::DashMap;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

/// Inode table for mapping paths to inodes and vice versa
pub struct InodeTable {
    /// Path -> Inode mapping
    path_to_inode: DashMap<PathBuf, u64>,
    /// Inode -> Path mapping
    inode_to_path: DashMap<u64, PathBuf>,
    /// Next inode number (starts at 2, as 1 is root)
    next_inode: AtomicU64,
}

impl InodeTable {
    /// Create a new inode table with root inode (1) for "/"
    pub fn new() -> Self {
        let table = Self {
            path_to_inode: DashMap::new(),
            inode_to_path: DashMap::new(),
            next_inode: AtomicU64::new(2),
        };
        
        // Initialize root inode
        let root_path = PathBuf::from("/");
        table.path_to_inode.insert(root_path.clone(), 1);
        table.inode_to_path.insert(1, root_path);
        
        table
    }

    /// Get or create an inode for a given path
    pub fn get_or_create_inode(&self, path: &Path) -> u64 {
        let path_buf = path.to_path_buf();
        
        // Check if path already has an inode
        if let Some(inode) = self.path_to_inode.get(&path_buf) {
            return *inode;
        }
        
        // Create new inode
        let inode = self.next_inode.fetch_add(1, Ordering::Relaxed);
        self.path_to_inode.insert(path_buf.clone(), inode);
        self.inode_to_path.insert(inode, path_buf);
        
        inode
    }

    /// Get inode for a path, returning None if not found
    pub fn get_inode(&self, path: &Path) -> Option<u64> {
        self.path_to_inode.get(path).map(|entry| *entry)
    }

    /// Get path for an inode, returning None if not found
    pub fn get_path(&self, inode: u64) -> Option<PathBuf> {
        self.inode_to_path.get(&inode).map(|entry| entry.clone())
    }

    /// Remove an inode and its path mapping
    pub fn remove(&self, inode: u64) {
        if let Some((_, path)) = self.inode_to_path.remove(&inode) {
            self.path_to_inode.remove(&path);
        }
    }

    /// Remove a path and its inode mapping
    pub fn remove_path(&self, path: &Path) {
        if let Some((_, inode)) = self.path_to_inode.remove(path) {
            self.inode_to_path.remove(&inode);
        }
    }
}

impl Default for InodeTable {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_root_inode() {
        let table = InodeTable::new();
        assert_eq!(table.get_inode(Path::new("/")), Some(1));
        assert_eq!(table.get_path(1), Some(PathBuf::from("/")));
    }

    #[test]
    fn test_get_or_create() {
        let table = InodeTable::new();
        let path = Path::new("/test");
        let inode1 = table.get_or_create_inode(path);
        let inode2 = table.get_or_create_inode(path);
        assert_eq!(inode1, inode2);
        assert_eq!(table.get_path(inode1), Some(PathBuf::from("/test")));
    }
}
