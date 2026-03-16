
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.core.ssh_manager import SSHManager

async def find_library():
    with SSHManager() as ssh:
        print("Searching for libhdf5_fortran.so.310 on cluster...")
        # Search in common locations
        cmd = "find /usr /opt /home -name 'libhdf5_fortran.so.310' 2>/dev/null"
        stdout, _, _ = ssh.execute_command(cmd)
        
        paths = stdout.strip().split('\n')
        valid_paths = [p for p in paths if p.strip()]
        
        if valid_paths:
            print("FOUND at:")
            for p in valid_paths:
                print(f"  {p}")
                
            # Suggest the export command
            parent_dir = os.path.dirname(valid_paths[0])
            print(f"\nSUGGESTED FIX:\nAdd this to 'execution_commands':")
            print(f"export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{parent_dir}")
        else:
            print("NOT FOUND via standard search.")

if __name__ == "__main__":
    asyncio.run(find_library())
