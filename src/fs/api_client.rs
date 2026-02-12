use anyhow::{Context, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::time::{sleep, Duration, Instant};

/// Configuration loaded from ~/.config/egnyte-desktop/config.json
#[derive(Debug, Deserialize)]
struct Config {
    domain: Option<String>,
    client_id: Option<String>,
    #[serde(flatten)]
    extra: HashMap<String, serde_json::Value>,
}

/// Python tokens.json format: access_token, expires_in, issued_at (refresh_token in keyring)
#[derive(Debug, Deserialize)]
struct TokenFile {
    access_token: Option<String>,
    expires_in: Option<u64>,
    issued_at: Option<i64>,
}

/// Get refresh_token from system keyring (egnyte-desktop / refresh_token)
fn get_refresh_token_from_keyring() -> Result<Option<String>> {
    let entry = keyring::Entry::new("egnyte-desktop", "refresh_token")?;
    match entry.get_password() {
        Ok(pwd) if !pwd.is_empty() => Ok(Some(pwd)),
        _ => Ok(None),
    }
}

/// Get client_secret from system keyring (egnyte-desktop / client_secret)
fn get_client_secret_from_keyring() -> Result<Option<String>> {
    let entry = keyring::Entry::new("egnyte-desktop", "client_secret")?;
    match entry.get_password() {
        Ok(pwd) if !pwd.is_empty() => Ok(Some(pwd)),
        _ => Ok(None),
    }
}

/// Egnyte API entry (file or folder)
#[derive(Debug, Clone, Deserialize)]
pub struct EgnyteEntry {
    pub name: String,
    pub path: String,
    #[serde(rename = "isFolder")]
    pub is_folder: bool,
    #[serde(rename = "size", default)]
    pub size: u64,
    #[serde(rename = "lastModified", deserialize_with = "deserialize_timestamp")]
    pub modified_time: SystemTime,
}

fn deserialize_timestamp<'de, D>(deserializer: D) -> Result<SystemTime, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let timestamp_ms: u64 = serde::Deserialize::deserialize(deserializer)?;
    let timestamp = timestamp_ms / 1000; // Convert ms to seconds
    let duration = Duration::from_secs(timestamp);
    SystemTime::UNIX_EPOCH
        .checked_add(duration)
        .ok_or_else(|| serde::de::Error::custom("Invalid timestamp"))
}

/// Real Egnyte API client implementation
pub struct EgnyteAPIClient {
    client: Client,
    base_url: String,
    domain: String,
    config_dir: PathBuf,
    inner: tokio::sync::RwLock<ClientInner>,
    rate_limiter: RateLimiter,
}

struct ClientInner {
    access_token: Option<String>,
    token_expires_at: Option<Instant>,
}

struct RateLimiter {
    min_interval: Duration,
    last_call: tokio::sync::Mutex<Option<Instant>>,
}

impl RateLimiter {
    fn new(qps: f64) -> Self {
        Self {
            min_interval: Duration::from_secs_f64(1.0 / qps),
            last_call: tokio::sync::Mutex::new(None),
        }
    }

    async fn wait_if_needed(&self) {
        let mut last = self.last_call.lock().await;
        if let Some(last_call) = *last {
            let elapsed = last_call.elapsed();
            if elapsed < self.min_interval {
                sleep(self.min_interval - elapsed).await;
            }
        }
        *last = Some(Instant::now());
    }
}

impl EgnyteAPIClient {
    /// Create a new API client, loading config and tokens from ~/.config/egnyte-desktop/
    pub async fn new() -> Result<Self> {
        let config_dir = dirs::home_dir()
            .context("Could not find home directory")?
            .join(".config")
            .join("egnyte-desktop");

        // Load config
        let config_file = config_dir.join("config.json");
        let config: Config = if config_file.exists() {
            let content = tokio::fs::read_to_string(&config_file)
                .await
                .context("Failed to read config file")?;
            serde_json::from_str(&content).context("Failed to parse config file")?
        } else {
            return Err(anyhow::anyhow!(
                "Config file not found. Please run 'egnyte-cli config set domain YOUR_DOMAIN'"
            ));
        };

        let domain = config
            .domain
            .context("Domain not configured. Run: egnyte-cli config set domain YOUR_DOMAIN")?;

        let base_url = format!("https://{}.egnyte.com", domain);

        // Load tokens from tokens.json (Python format: access_token, expires_in, issued_at)
        let token_file = config_dir.join("tokens.json");
        let token_data: TokenFile = if token_file.exists() {
            let content = tokio::fs::read_to_string(&token_file)
                .await
                .context("Failed to read token file")?;
            serde_json::from_str(&content).unwrap_or_else(|_| TokenFile {
                access_token: None,
                expires_in: None,
                issued_at: None,
            })
        } else {
            return Err(anyhow::anyhow!(
                "Not authenticated. Please run 'egnyte-cli auth login'"
            ));
        };

        // Refresh token is in keyring (Python stores it there)
        let _refresh_token = get_refresh_token_from_keyring()?;
        if _refresh_token.is_none() {
            return Err(anyhow::anyhow!(
                "No refresh token in keyring. Please run 'egnyte-cli auth login'"
            ));
        }

        let access_token = token_data.access_token.clone();
        let token_expires_at = token_data
            .issued_at
            .and_then(|issued| {
                token_data.expires_in.map(|expires_in| {
                    let expires_at_secs = issued as u64 + expires_in;
                    let now = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap()
                        .as_secs();
                    if expires_at_secs > now {
                        Instant::now() + Duration::from_secs(expires_at_secs - now)
                    } else {
                        Instant::now() // Already expired
                    }
                })
            });

        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            client,
            base_url,
            domain,
            config_dir,
            inner: tokio::sync::RwLock::new(ClientInner {
                access_token,
                token_expires_at,
            }),
            rate_limiter: RateLimiter::new(10.0), // 10 QPS default
        })
    }

    /// Get a valid access token, refreshing if necessary
    async fn get_valid_token(&self) -> Result<String> {
        // Check if token is expired or about to expire (within 60 seconds)
        let needs_refresh = {
            let inner = self.inner.read().await;
            inner.token_expires_at.map_or(true, |exp| {
                exp.saturating_duration_since(Instant::now()) < Duration::from_secs(60)
            })
        };

        if needs_refresh {
            self.refresh_token().await?;
        }

        let inner = self.inner.read().await;
        inner
            .access_token
            .clone()
            .context("No access token available")
    }

    /// Refresh the access token
    async fn refresh_token(&self) -> Result<()> {
        let refresh_token = get_refresh_token_from_keyring()?
            .context("No refresh token in keyring. Please run 'egnyte-cli auth login'")?;

        let client_secret = get_client_secret_from_keyring()?
            .context("No client_secret in keyring. Run: egnyte-cli config set client_secret YOUR_SECRET")?;

        let config_file = self.config_dir.join("config.json");
        let config: Config = if config_file.exists() {
            let content = tokio::fs::read_to_string(&config_file)
                .await
                .context("Failed to read config file")?;
            serde_json::from_str(&content).context("Failed to parse config file")?
        } else {
            return Err(anyhow::anyhow!("Config file not found"));
        };

        let client_id = config
            .client_id
            .context("Client ID not configured")?;

        let refresh_url = format!("https://{}.egnyte.com/puboauth/token", self.domain);

        let params = [
            ("grant_type", "refresh_token"),
            ("refresh_token", refresh_token.as_str()),
            ("client_id", client_id.as_str()),
            ("client_secret", client_secret.as_str()),
        ];

        let response = self
            .client
            .post(&refresh_url)
            .form(&params)
            .send()
            .await
            .context("Failed to refresh token")?;

        if !response.status().is_success() {
            return Err(anyhow::anyhow!(
                "Token refresh failed. Please run 'egnyte-cli auth login'"
            ));
        }

        let token_data: serde_json::Value = response
            .json()
            .await
            .context("Failed to parse token response")?;

        let new_access_token = token_data
            .get("access_token")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .context("No access_token in response")?;

        let expires_in = token_data
            .get("expires_in")
            .and_then(|v| v.as_u64())
            .unwrap_or(3600);

        let issued_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64;

        // Save tokens in Python format (access_token, expires_in, issued_at)
        #[derive(serde::Serialize)]
        struct TokenFileOut {
            access_token: String,
            expires_in: u64,
            #[serde(rename = "token_type")]
            token_type: String,
            issued_at: i64,
        }
        let new_tokens = TokenFileOut {
            access_token: new_access_token.clone(),
            expires_in,
            token_type: "Bearer".to_string(),
            issued_at,
        };

        let token_file = self.config_dir.join("tokens.json");
        let token_json = serde_json::to_string_pretty(&new_tokens)
            .context("Failed to serialize tokens")?;
        tokio::fs::write(&token_file, token_json)
            .await
            .context("Failed to write token file")?;

        // Update inner state
        {
            let mut inner = self.inner.write().await;
            inner.access_token = Some(new_access_token);
            inner.token_expires_at = Some(Instant::now() + Duration::from_secs(expires_in));
        }

        Ok(())
    }

    /// Make an authenticated API request
    async fn request(
        &self,
        method: reqwest::Method,
        endpoint: &str,
    ) -> Result<reqwest::Response> {
        self.rate_limiter.wait_if_needed().await;

        let token = self.get_valid_token().await?;
        let url = format!("{}{}", self.base_url, endpoint);

        let mut retries = 5;
        let mut backoff = Duration::from_millis(500);

        loop {
            let response = self
                .client
                .request(method.clone(), &url)
                .header("Authorization", format!("Bearer {}", token))
                .header("Content-Type", "application/json")
                .send()
                .await
                .context("API request failed")?;

            if response.status() == 401 {
                // Token might be invalid, try refreshing
                self.refresh_token().await?;
                let new_token = self.get_valid_token().await?;
                let response = self
                    .client
                    .request(method.clone(), &url)
                    .header("Authorization", format!("Bearer {}", new_token))
                    .header("Content-Type", "application/json")
                    .send()
                    .await
                    .context("API request failed after refresh")?;
                
                if response.status().is_success() {
                    return Ok(response);
                }
            }

            if response.status() == 429 {
                // Rate limited, back off and retry
                if retries > 0 {
                    retries -= 1;
                    sleep(backoff).await;
                    backoff = backoff * 2;
                    continue;
                }
            }

            if !response.status().is_success() {
                return Err(anyhow::anyhow!(
                    "API request failed: {} {}",
                    response.status(),
                    response.text().await.unwrap_or_default()
                ));
            }

            return Ok(response);
        }
    }
}

#[async_trait::async_trait]
impl crate::fs::fuse_ops::EgnyteAPI for EgnyteAPIClient {
    async fn list_folder(&self, path: &str) -> Result<Vec<crate::fs::fuse_ops::EgnyteEntry>> {
        let endpoint = format!("/pubapi/v1/fs{}", path);
        let response = self.request(reqwest::Method::GET, &endpoint).await?;
        let data: serde_json::Value = response.json().await.context("Failed to parse response")?;

        let mut entries = Vec::new();

        // Process folders
        if let Some(folders) = data.get("folders").and_then(|v| v.as_array()) {
            for folder in folders {
                if let Ok(entry) = serde_json::from_value::<EgnyteEntry>(folder.clone()) {
                    entries.push(crate::fs::fuse_ops::EgnyteEntry {
                        name: entry.name,
                        path: entry.path,
                        is_folder: true,
                        size: 0,
                        modified_time: entry.modified_time,
                    });
                }
            }
        }

        // Process files
        if let Some(files) = data.get("files").and_then(|v| v.as_array()) {
            for file in files {
                if let Ok(entry) = serde_json::from_value::<EgnyteEntry>(file.clone()) {
                    entries.push(crate::fs::fuse_ops::EgnyteEntry {
                        name: entry.name,
                        path: entry.path,
                        is_folder: false,
                        size: entry.size,
                        modified_time: entry.modified_time,
                    });
                }
            }
        }

        Ok(entries)
    }

    async fn get_file_info(&self, path: &str) -> Result<crate::fs::fuse_ops::EgnyteEntry> {
        let endpoint = format!("/pubapi/v1/fs{}", path);
        let response = self.request(reqwest::Method::GET, &endpoint).await?;
        let entry: EgnyteEntry = response
            .json()
            .await
            .context("Failed to parse file info")?;

        Ok(crate::fs::fuse_ops::EgnyteEntry {
            name: entry.name,
            path: entry.path,
            is_folder: entry.is_folder,
            size: entry.size,
            modified_time: entry.modified_time,
        })
    }

    async fn download_file(&self, path: &str) -> Result<Vec<u8>> {
        let endpoint = format!("/pubapi/v1/fs-content{}", path);
        let response = self.request(reqwest::Method::GET, &endpoint).await?;
        let bytes = response
            .bytes()
            .await
            .context("Failed to read file content")?;
        Ok(bytes.to_vec())
    }
}
