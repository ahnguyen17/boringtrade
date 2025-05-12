"""
Check if all the required dependencies are installed.
"""
import importlib.util
import sys

def check_dependency(package_name, friendly_name=None):
    """Check if a package is installed."""
    if friendly_name is None:
        friendly_name = package_name
    
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"❌ {friendly_name} is NOT installed")
        return False
    else:
        print(f"✅ {friendly_name} is installed")
        return True

def main():
    """Check all dependencies."""
    print("Checking dependencies for BoringTrade trading bot...")
    print("\nCore dependencies:")
    core_deps = [
        ("flask", "Flask"),
        ("flask_socketio", "Flask-SocketIO"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("matplotlib", "Matplotlib"),
        ("requests", "Requests"),
        ("dotenv", "python-dotenv"),
        ("websocket", "websocket-client")
    ]
    
    core_installed = all(check_dependency(pkg, name) for pkg, name in core_deps)
    
    print("\nOptional dependencies:")
    optional_deps = [
        ("ccxt", "CCXT"),
        ("talib", "TA-Lib"),
        ("pytest", "pytest")
    ]
    
    optional_installed = all(check_dependency(pkg, name) for pkg, name in optional_deps)
    
    print("\nSummary:")
    if core_installed:
        print("✅ All core dependencies are installed")
    else:
        print("❌ Some core dependencies are missing")
        print("   Run: pip install -r requirements.txt")
    
    if optional_installed:
        print("✅ All optional dependencies are installed")
    else:
        print("⚠️ Some optional dependencies are missing")
        print("   This is okay, but some features may not work")
    
    print("\nRecommendations:")
    if not core_installed:
        print("1. Install core dependencies:")
        print("   pip install -r requirements.txt")
        print("\n2. If you just want to see the dashboard:")
        print("   pip install flask")
        print("   python simple_dashboard.py")
    elif not optional_installed:
        print("1. Install optional dependencies if needed:")
        print("   pip install ccxt pytest")
        print("   # Note: TA-Lib requires special installation steps")
    else:
        print("All dependencies are installed! You can run the bot with:")
        print("python run.py")

if __name__ == "__main__":
    main()
