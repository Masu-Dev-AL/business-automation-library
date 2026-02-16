"""
Setup Verification Script
Checks if all components are properly configured
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
load_dotenv(env_path)


def check_env_variables():
    """Check if required environment variables are set"""
    print("\n1. Checking Environment Variables...")
    required_vars = [
        'WC_URL',
        'WC_CONSUMER_KEY',
        'WC_CONSUMER_SECRET',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value and 'your_' not in value.lower() and 'xxx' not in value.lower():
            print(f"   [OK] {var} is set")
        else:
            print(f"   [MISSING] {var} is not configured")
            missing.append(var)

    return len(missing) == 0


def check_woocommerce_connection():
    """Test WooCommerce API connection"""
    print("\n2. Checking WooCommerce Connection...")

    try:
        import requests
        from requests.auth import HTTPBasicAuth

        wc_url = os.getenv('WC_URL')
        wc_key = os.getenv('WC_CONSUMER_KEY')
        wc_secret = os.getenv('WC_CONSUMER_SECRET')

        if not all([wc_url, wc_key, wc_secret]):
            print("   [SKIP] WooCommerce credentials not configured")
            return False

        auth = HTTPBasicAuth(wc_key, wc_secret)
        response = requests.get(f"{wc_url}/products", auth=auth, params={"per_page": 1}, timeout=10)

        if response.status_code == 200:
            print(f"   [OK] Connected to WooCommerce at {wc_url}")
            products = response.json()
            print(f"   [OK] API responding - found {len(products)} product(s)")
            return True
        else:
            print(f"   [FAIL] WooCommerce returned status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print("   [FAIL] Cannot connect to WooCommerce")
        print("   Make sure Local by Flywheel is running!")
        return False
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return False


def check_postgresql_connection():
    """Test PostgreSQL database connection"""
    print("\n3. Checking PostgreSQL Connection...")

    try:
        import psycopg2

        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME', 'ecommerce_inventory'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   [OK] Connected to PostgreSQL")
        print(f"   [OK] Version: {version[:50]}...")

        # Check if tables exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name LIKE 'dim_%' OR table_name LIKE 'fact_%'
        """)
        table_count = cursor.fetchone()[0]
        if table_count > 0:
            print(f"   [OK] Found {table_count} schema tables")
        else:
            print("   [WARN] No schema tables found - run sql/schema.sql")

        conn.close()
        return True

    except ImportError:
        print("   [FAIL] psycopg2 not installed - run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"   [FAIL] Database connection error: {e}")
        return False


def check_python_packages():
    """Check if required Python packages are installed"""
    print("\n4. Checking Python Packages...")

    packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'psycopg2': 'psycopg2-binary',
        'requests': 'requests',
        'dotenv': 'python-dotenv',
        'streamlit': 'streamlit',
        'plotly': 'plotly',
    }

    missing = []
    for import_name, package_name in packages.items():
        try:
            __import__(import_name)
            print(f"   [OK] {package_name}")
        except ImportError:
            print(f"   [MISSING] {package_name}")
            missing.append(package_name)

    if missing:
        print(f"\n   Install missing packages: pip install {' '.join(missing)}")
        return False
    return True


def check_project_structure():
    """Check if project folder structure exists"""
    print("\n5. Checking Project Structure...")

    base_path = os.path.dirname(os.path.dirname(__file__))
    required_dirs = [
        'scripts',
        'dashboard',
        'dashboard/pages',
        'config',
        'sql'
    ]

    required_files = [
        'requirements.txt',
        'sql/schema.sql',
        'config/.env.example'
    ]

    all_good = True

    for dir_name in required_dirs:
        dir_path = os.path.join(base_path, dir_name)
        if os.path.isdir(dir_path):
            print(f"   [OK] {dir_name}/")
        else:
            print(f"   [MISSING] {dir_name}/")
            all_good = False

    for file_name in required_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.isfile(file_path):
            print(f"   [OK] {file_name}")
        else:
            print(f"   [MISSING] {file_name}")
            all_good = False

    # Check for .env
    env_file = os.path.join(base_path, 'config', '.env')
    if os.path.isfile(env_file):
        print(f"   [OK] config/.env")
    else:
        print(f"   [WARN] config/.env not found - copy from .env.example")

    return all_good


def main():
    print("=" * 60)
    print("E-commerce Inventory Pipeline - Setup Verification")
    print("=" * 60)

    results = {
        'Project Structure': check_project_structure(),
        'Python Packages': check_python_packages(),
        'Environment Variables': check_env_variables(),
        'PostgreSQL': check_postgresql_connection(),
        'WooCommerce': check_woocommerce_connection(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for component, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {component}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("All checks passed! You're ready to proceed.")
        print("\nNext steps:")
        print("1. Run generate_test_data.py to populate WooCommerce")
        print("2. Run the ETL scripts to load data into PostgreSQL")
        print("3. Launch the Streamlit dashboard")
    else:
        print("Some checks failed. Please fix the issues above.")
        print("\nSetup steps:")
        print("1. Copy config/.env.example to config/.env and fill in values")
        print("2. Install packages: pip install -r requirements.txt")
        print("3. Set up Local by Flywheel with WooCommerce")
        print("4. Create PostgreSQL database and run sql/schema.sql")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
