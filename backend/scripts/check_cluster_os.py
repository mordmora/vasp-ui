
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.core.ssh_manager import SSHManager
from app.config import settings

async def check_os():
    with SSHManager() as ssh:
        print("Checking Remote OS...")
        # Check OS release
        cmd = "cat /etc/os-release"
        stdout, _, _ = ssh.execute_command(cmd)
        print(f"--- /etc/os-release ---\n{stdout.strip()}\n-----------------------")
        
        # Check if slurm is installed (dpkg or rpm)
        print("\nChecking for SLURM packages...")
        
        # Try Debian/Ubuntu
        cmd = "dpkg -l | grep slurm"
        stdout, _, _ = ssh.execute_command(cmd)
        if stdout.strip():
            print("Found via dpkg:")
            print(stdout)
        else:
            # Try RHEL/CentOS
            cmd = "rpm -qa | grep slurm"
            stdout, _, _ = ssh.execute_command(cmd)
            if stdout.strip():
                print("Found via rpm:")
                print(stdout)
            else:
                 print("No SLURM packages found via dpkg or rpm.")
                 
        # Check standard config directories
        dirs = ["/etc/slurm", "/etc/slurm-llnl", "/usr/local/etc/slurm"]
        print("\nChecking config directories:")
        for d in dirs:
            exists = ssh.file_exists(d)
            print(f"  {d}: {'EXISTS' if exists else 'MISSING'}")

if __name__ == "__main__":
    # Mock settings if needed or rely on .env
    asyncio.run(check_os())
