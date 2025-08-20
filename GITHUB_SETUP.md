# GitHub Setup Guide for PLUMATOTM

This guide will walk you through uploading your PLUMATOTM engine to GitHub step by step.

## Step 1: Create a GitHub Account

1. Go to [github.com](https://github.com)
2. Click "Sign up" and create a new account
3. Verify your email address

## Step 2: Install Git (if not already installed)

### Windows:
1. Download Git from [git-scm.com](https://git-scm.com)
2. Install with default settings
3. Open PowerShell or Command Prompt

### macOS:
```bash
# Install via Homebrew
brew install git

# Or download from git-scm.com
```

### Linux:
```bash
sudo apt-get install git  # Ubuntu/Debian
sudo yum install git      # CentOS/RHEL
```

## Step 3: Configure Git

Open your terminal/command prompt and run:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 4: Create a New Repository on GitHub

1. Go to [github.com](https://github.com)
2. Click the "+" icon in the top right
3. Select "New repository"
4. Fill in the details:
   - **Repository name**: `plumatotm`
   - **Description**: `PLUMATOTM - Astrological Animal Compatibility Engine`
   - **Visibility**: Choose Public or Private
   - **DO NOT** check "Add a README file" (we already have one)
   - **DO NOT** check "Add .gitignore" (we already have one)
5. Click "Create repository"

## Step 5: Initialize Git in Your Local Project

Open your terminal/command prompt, navigate to your project folder, and run:

```bash
# Navigate to your project directory
cd "D:\OneDrive\PLUMASTRO\CURSOR"

# Initialize Git repository
git init

# Add all files to Git
git add .

# Make your first commit
git commit -m "Initial commit: PLUMATOTM engine"

# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/plumatotm.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 6: Verify Upload

1. Go to your GitHub repository page
2. You should see all your files uploaded
3. Check that the README.md displays correctly

## Step 7: Test Your Repository

1. Clone your repository to a different location to test:
```bash
git clone https://github.com/YOUR_USERNAME/plumatotm.git test-plumatotm
cd test-plumatotm
```

2. Test that everything works:
```bash
# Install dependencies
pip install -r requirements.txt

# Test the core engine
python plumatotm_core.py --help
```

## Step 8: Update Files (Future Changes)

When you make changes to your code:

```bash
# Add your changes
git add .

# Commit with a descriptive message
git commit -m "Description of your changes"

# Push to GitHub
git push
```

## Troubleshooting

### If you get authentication errors:
1. GitHub now uses personal access tokens instead of passwords
2. Go to GitHub Settings → Developer settings → Personal access tokens
3. Generate a new token with "repo" permissions
4. Use the token as your password when prompted

### If you get "fatal: remote origin already exists":
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/plumatotm.git
```

### If you need to update the remote URL:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/plumatotm.git
```

## Next Steps

Once your repository is on GitHub:

1. **Deploy to Render**: Follow the deployment guide in `DEPLOYMENT_GUIDE.md`
2. **Set up CI/CD**: Consider adding GitHub Actions for automated testing
3. **Add Issues**: Create issues for bugs or feature requests
4. **Add Wiki**: Create documentation pages
5. **Add Releases**: Tag important versions

## Repository URL

Your repository will be available at:
`https://github.com/YOUR_USERNAME/plumatotm`

## Support

If you encounter any issues:
1. Check GitHub's documentation
2. Search for similar issues on Stack Overflow
3. Ask for help in GitHub's community forums

---

**Congratulations!** Your PLUMATOTM engine is now on GitHub and ready for deployment! 🎉
