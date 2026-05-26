# 🧹 Cleanup Guide - Remove Accidentally Installed Packages

If you accidentally installed the requirements.txt packages in your base Python environment, here are your options:

## Option 1: Uninstall Packages (Quick & Easy)

Run this command to uninstall all packages from requirements.txt:

```bash
pip uninstall -y -r requirements.txt
```

Or use the provided script:

```bash
chmod +x uninstall_packages.sh
./uninstall_packages.sh
```

**Note:** This will only remove the packages listed in requirements.txt. Some dependencies may remain if they're used by other packages.

## Option 2: Create a Virtual Environment (Recommended Going Forward)

Instead of cleaning up, create a virtual environment for this project:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install packages in the virtual environment
pip install -r requirements.txt

# Now you can run the project safely
python main_api.py
```

**Benefits:**
- Keeps your base environment clean
- Isolates project dependencies
- Easy to delete (just remove the `venv` folder)

## Option 3: Use Conda Environment (If you use Conda)

```bash
# Create conda environment
conda create -n rag_builder python=3.10

# Activate it
conda activate rag_builder

# Install packages
pip install -r requirements.txt
```

## Option 4: Complete Reset (Nuclear Option)

If you want to completely reset your base Python environment:

**⚠️ WARNING: This will remove ALL packages from your base environment!**

```bash
# List all installed packages
pip freeze > all_packages.txt

# Uninstall everything
pip uninstall -y -r all_packages.txt

# Reinstall only pip
python -m ensurepip --upgrade
```

## Checking What's Installed

To see what packages are currently installed:

```bash
pip list
```

To see only packages from requirements.txt:

```bash
pip freeze | grep -f <(cat requirements.txt | cut -d'=' -f1)
```

## Best Practices Going Forward

1. **Always use virtual environments** for projects
2. Never install project dependencies in base environment
3. Add `venv/` to `.gitignore` (already done in this project)
4. Document the Python version and dependencies

## Quick Virtual Environment Setup

Add this to your workflow:

```bash
# One-time setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Daily usage
source venv/bin/activate  # Activate when you start working
# ... do your work ...
deactivate  # Deactivate when done
```

## Automated Setup Script

I've also created a `setup_venv.sh` script for you (see below).

---

**Recommendation:** Use Option 2 (Virtual Environment) - it's the cleanest solution and follows Python best practices.