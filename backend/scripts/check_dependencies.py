
import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

try:
    from app.core.ssh_manager import SSHManager
    from app.config import settings
except Exception:
    # Handle the case where settings cannot be initialized (missing .env)
    # We will handle this gracefully in main() or print error here
    pass

def print_config_error():
    print("\n\033[91mError: Configuration invalid or missing.\033[0m")
    print("Please ensure you have a '.env' file in the 'backend' directory with the following variables:")
    print("  CLUSTER_HOST")
    print("  CLUSTER_USER")
    print("  CLUSTER_VASP_PATH")
    print("  CLUSTER_VASPKIT_PATH")
    print("  CLUSTER_POTCAR_PATH")
    print("  CLUSTER_WORK_DIR")
    print("\nYou can copy '.env.example' to '.env' and fill in your details:\n")
    print("  cp .env.example .env\n")


async def check_dependencies(nodelist=None):
    """
    Check for VASP dependencies on the cluster/node.
    """
    try:
        from app.config import settings
    except Exception:
        print_config_error()
        return

    print(f"Connecting to cluster ({settings.cluster_host})...")
    
    try:
        with SSHManager() as ssh:
            # If a specific node is requested, we might need to SSH into it from the login node
            # But usually we check if the modules/binaries are available in the path.
            # Assuming shared filesystem or checking standard paths.
            
            print("Connection established.")
            
            # Debug: Print PATH
            stdout, _, _ = ssh.execute_command("echo $PATH")
            print(f"Remote PATH: {stdout.strip()}")
            
            if nodelist:
                print(f"checking on node(s): {nodelist}")
                # This would require srun or similar if we want to check on the compute node specifically
                # For now, let's check on the login node as a proxy, or use srun if possible.
                # simpler to just check if `srun` works with those binaries if needed, 
                # but user just asked to check if they are installed.
            
            # 1. VASPKIT
            # Try to find it normally
            check_binary(ssh, "VASPKIT", settings.cluster_vaspkit_path, "--version")
            
            # If default lookup failed, try looking with .bashrc sourced
            if settings.cluster_vaspkit_path == "vaspkit":
                 print("  > Retrying with .bashrc sourced...")
                 cmd = "source ~/.bashrc && command -v vaspkit"
                 stdout, _, exit_code = ssh.execute_command(cmd)
                 if exit_code == 0:
                     print(f"  [OK] Found with .bashrc at: {stdout.strip()}")
                     print("  (!) Hint: Use this absolute path in your .env file.")
                 else:
                     print("  [FAIL] Still not found even with .bashrc.")
            
            # 2. VASP CPU
            # Checking for 'vasp_std_cpu' specifically as requested
            check_binary(ssh, "VASP CPU (vasp_std_cpu)", "vasp_std_cpu", "--version") # VASP typically doesn't have --version, but we check existence
            
            # 3. VASP GPU
            # Checking for 'vasp_std_gpu' specifically as requested
            check_binary(ssh, "VASP GPU (vasp_std_gpu)", "vasp_std_gpu", "--version")
            
            # 4. Configured VASP
            check_binary(ssh, "Configured VASP Path", settings.cluster_vasp_path, "")

            # 5. Scheduler (sbatch)
            print(f"\nChecking Scheduler (sbatch)...")
            cmd = "command -v sbatch"
            stdout, _, exit_code = ssh.execute_command(cmd)
            if exit_code == 0:
                print(f"  [OK] Found at: {stdout.strip()}")
            else:
                print("  [MISSING] Not found in default PATH.")
                print("  > Retrying with .bashrc sourced...")
                cmd = "source ~/.bashrc && command -v sbatch"
                stdout, _, exit_code = ssh.execute_command(cmd)
                if exit_code == 0:
                     print(f"  [OK] Found with .bashrc at: {stdout.strip()}")
                     print("  (!) This implies we need to use absolute path or source .bashrc for submission.")
                else:
                     print("  [FAIL] sbatch not found.")

    except Exception as e:
        print(f"Error: {e}")

def check_binary(ssh, name, command, version_flag="--version"):
    print(f"\nChecking {name}...")
    
    # Check if executable exists using `command -v`
    # We strip arguments from command if it's a path like "/path/to/vasp args"
    cmd_base = command.split()[0]
    
    check_cmd = f"command -v {cmd_base}"
    stdout, stderr, exit_code = ssh.execute_command(check_cmd)
    
    if exit_code == 0:
        path = stdout.strip()
        print(f"  [OK] Found at: {path}")
        
        # Try to get version
        if version_flag:
            ver_cmd = f"{command} {version_flag}"
            # Some programs output version to stderr
            stdout, stderr, exit_code = ssh.execute_command(ver_cmd)
            output = stdout.strip() or stderr.strip()
            # Limit output length
            print(f"  Version Output: {output.splitlines()[0] if output else 'No output'}")
    else:
        print(f"  [MISSING] Could not find executable: {command}")
        print(f"  Error: {stderr.strip()}")

if __name__ == "__main__":
    # nodelist arg could be added here
    asyncio.run(check_dependencies())
