# Push to GitHub - Step-by-Step Guide

## Prerequisites

1. You need a GitHub account
2. You need Git installed on Windows

**Check if Git is installed:**
```bash
git --version
```

If not installed, download from: https://git-scm.com/download/win

---

## Option 1: Automated Script (Easiest)

Run this script to commit everything:

```bash
cd c:\Users\Notandi\Desktop\agi\engram-system
.\push_to_github.bat
```

It will ask for your GitHub repository URL.

---

## Option 2: Manual Steps

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `engram-system` (or whatever you want)
3. Description: "An intelligent, self-evolving memory system with truth-seeking AI"
4. Choose **Public** or **Private**
5. **DON'T** initialize with README (we already have one)
6. Click **Create repository**

### Step 2: Initialize Git Locally

Open PowerShell in your project folder:

```bash
cd c:\Users\Notandi\Desktop\agi\engram-system

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial release: Engram Memory System v1.0 - 16 phases complete with Truth Guard"
```

### Step 3: Connect to GitHub

Replace `YOUR_USERNAME` with your GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/engram-system.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Enter Credentials

When prompted:
- **Username**: Your GitHub username
- **Password**: Your GitHub **Personal Access Token** (not your password!)

**To create a Personal Access Token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "Engram System Push"
4. Select scope: `repo` (full control)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. Use this as your password when pushing

---

## Verify It Worked

After pushing, visit:
```
https://github.com/YOUR_USERNAME/engram-system
```

You should see all your files! 🎉

---

## Common Issues

### "fatal: not a git repository"
Run `git init` first

### "permission denied"
Make sure you're using your Personal Access Token, not your password

### "repository not found"
Double-check the repository name and your username in the URL

---

## Quick Reference

```bash
# Make future changes
git add .
git commit -m "Your change description"
git push

# Check status
git status

# See what changed
git diff
```

---

**Ready? Let's push to GitHub!** 🚀
