import os
import sys
import shutil

def deploy_openai():
    src = "testing_env/openai_version/app"
    dst = "app"
    
    print(f"Copying logic from {src} to {dst}...")
    
    # We want to copy specific logic files that might have changed
    # FlowManager, Main, etc.
    # For safety, let's copy the services folder and main.py
    
    # 1. Main
    shutil.copy2(os.path.join(src, "main.py"), os.path.join(dst, "main.py"))
    
    # 2. Services
    if os.path.exists(os.path.join(dst, "services")):
        shutil.rmtree(os.path.join(dst, "services"))
    shutil.copytree(os.path.join(src, "services"), os.path.join(dst, "services"))
    
    print("Deployment complete. Please restart your server.")

def deploy_google():
    src = "testing_env/google_version/app"
    dst = "app"
    
    print(f"Copying logic from {src} to {dst}...")
    
    shutil.copy2(os.path.join(src, "main.py"), os.path.join(dst, "main.py"))
    
    if os.path.exists(os.path.join(dst, "services")):
        shutil.rmtree(os.path.join(dst, "services"))
    shutil.copytree(os.path.join(src, "services"), os.path.join(dst, "services"))
    
    print("Deployment complete. Please restart your server.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deploy_script.py [openai|google]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == "openai":
        deploy_openai()
    elif mode == "google":
        deploy_google()
    else:
        print("Invalid mode.")
