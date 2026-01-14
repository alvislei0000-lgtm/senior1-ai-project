# Git 和 GitHub 設定指南

## 步驟1：安裝 Git

### Windows 系統

1. **下載 Git**
   - 前往：https://git-scm.com/download/win
   - 下載 "Git for Windows" 安裝程式

2. **安裝 Git**
   - 執行下載的安裝程式
   - 大部分選項使用預設值即可
   - 建議選擇 "Git Bash Here" 和 "Git GUI Here"
   - 安裝完成後重新啟動電腦

3. **驗證安裝**
   ```bash
   git --version
   ```
   應該會看到類似：`git version 2.42.0.windows.1`

### macOS 系統

```bash
# 使用 Homebrew 安裝
brew install git

# 或使用 Xcode Command Line Tools
xcode-select --install
```

### Linux 系統

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install git

# CentOS/RHEL
sudo yum install git
```

## 步驟2：Git 基本設定

安裝完成後，開啟命令提示字元或 PowerShell：

```bash
# 設定使用者名稱（請使用你的真實姓名）
git config --global user.name "你的姓名"

# 設定電子郵件（請使用你的 GitHub 註冊郵件）
git config --global user.email "your-email@example.com"

# 設定預設分支名稱為 main
git config --global init.defaultBranch main

# 檢查設定
git config --list
```

## 步驟3：建立 GitHub 帳號和倉庫

### 3.1 建立 GitHub 帳號

1. 前往：https://github.com
2. 點擊 "Sign up"
3. 填入資訊並驗證郵件

### 3.2 建立新倉庫

1. 登入 GitHub 後，點擊右上角 **"+"** → **"New repository"**
2. 倉庫設定：
   - **Repository name**: `senior1-ai-project`
   - **Description**: `硬體基準分析系統 - 前後端完整專案`
   - **Visibility**: 選擇 **Public**（公開）
3. **重要**：請勿勾選任何初始化選項：
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license
4. 點擊 **"Create repository"**

## 步驟4：初始化本地專案並上傳

### 4.1 初始化 Git 倉庫

```bash
# 進入專案目錄
cd "D:\cursor\senior1 ai project"

# 初始化 Git 倉庫
git init

# 檢查狀態
git status
```

### 4.2 添加檔案到 Git

```bash
# 添加所有檔案
git add .

# 檢查將要提交的檔案
git status

# 提交檔案
git commit -m "Initial commit - Senior1 AI Project 硬體基準分析系統"
```

### 4.3 連接 GitHub 倉庫

```bash
# 添加遠端倉庫（請將 YOUR_USERNAME 替換為你的 GitHub 用戶名）
git remote add origin https://github.com/YOUR_USERNAME/senior1-ai-project.git

# 檢查遠端倉庫
git remote -v
```

### 4.4 上傳到 GitHub

```bash
# 推送程式碼到 GitHub
git push -u origin main

# 如果出現錯誤，可能需要先拉取
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## 步驟5：驗證上傳成功

1. 前往你的 GitHub 倉庫頁面
2. 應該能看到所有檔案都已上傳
3. 確認有以下重要檔案：
   - `Dockerfile.backend`
   - `Dockerfile.frontend`
   - `railway.toml`
   - `nginx.conf`
   - `frontend/` 目錄
   - `backend/` 目錄

## 常見問題解決

### 問題1：無法連接 GitHub
```
fatal: remote origin already exists
```
**解決方案**：
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/senior1-ai-project.git
```

### 問題2：推送被拒絕
```
! [rejected] main -> main (fetch first)
```
**解決方案**：
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 問題3：檔案太大
如果有檔案太大（>100MB），GitHub 會拒絕推送。

**解決方案**：
1. 檢查大檔案：
   ```bash
   git ls-files | xargs ls -lh | awk '{if($5 > 100000000) print $9, $5}'
   ```
2. 如果有大檔案，考慮添加到 `.gitignore`

### 問題4：認證失敗
```
Support for password authentication was removed
```
**解決方案**：
- 使用 Personal Access Token 而非密碼
- 在 GitHub Settings → Developer settings → Personal access tokens 生成 Token
- 使用 Token 作為密碼

## 下一步

完成 Git 和 GitHub 設定後，繼續進行步驟2：Railway 部署！

🎉 **恭喜！** 你已經完成了部署準備工作。