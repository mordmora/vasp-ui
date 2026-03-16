
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.core.ssh_manager import SSHManager

async def read_bashrc():
    with SSHManager() as ssh:
        print("Reading ~/.bashrc...")
        content = ssh.read_remote_file(".bashrc")
        print("--- ~/.bashrc Content ---")
        print(content)
        print("-------------------------")
        
        # Also check .profile or .bash_profile
        try:
            profile = ssh.read_remote_file(".profile")
            print("\n--- ~/.profile Content ---")
            print(profile)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(read_bashrc())
