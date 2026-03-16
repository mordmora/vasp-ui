
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(os.getcwd())

from app.core.ssh_manager import SSHManager
from app.services.vaspkit_service import VASPKITService
from app.config import settings
from app.api.routes.relax import get_relax_status
# Mock DB and Project for status check reuse
from unittest.mock import MagicMock, AsyncMock
from app.models.project import Project, ProjectStatus

# Simple POSCAR (Silicon)
POSCAR_CONTENT = """Si2
1.0
5.4307000000 0.0000000000 0.0000000000
0.0000000000 5.4307000000 0.0000000000
0.0000000000 0.0000000000 5.4307000000
Si
8
Direct
0.875000000 0.875000000 0.875000000
0.125000000 0.125000000 0.125000000
0.875000000 0.375000000 0.375000000
0.125000000 0.625000000 0.625000000
0.375000000 0.875000000 0.375000000
0.625000000 0.125000000 0.625000000
0.375000000 0.375000000 0.875000000
0.625000000 0.625000000 0.625000000
"""

async def run_real_test():
    print(f"--- Real Cluster Test ---")
    print(f"Host: {settings.cluster_host}")
    print(f"User: {settings.cluster_user}")
    
    # 1. Override VASP Path if needed (since .env might be outdated)
    # We detected vasp_std_gpu at /usr/local/bin/vasp_std_gpu
    if "path/to/vasp" in settings.cluster_vasp_path:
        print("(!) VASP path in .env is default. Using /usr/local/bin/vasp_std_gpu")
        settings.cluster_vasp_path = "/usr/local/bin/vasp_std_gpu"
    
    remote_path = f"{settings.cluster_work_dir}/test_api_flow"
    
    with SSHManager() as ssh:
        print(f"\n1. Connected to cluster.")
        
        # 2. Setup Directory
        print(f"2. Creating test directory: {remote_path}")
        ssh.create_remote_directory(remote_path)
        ssh.upload_text_file(POSCAR_CONTENT, f"{remote_path}/POSCAR")
        
        # 3. Generate Inputs (VASPKIT)
        print(f"3. Generating inputs with VASPKIT (remote)...")
        vaspkit = VASPKITService(ssh)
        try:
            files = vaspkit.generate_relax_inputs(
                work_dir=remote_path,
                encut=300, # Low cutoff for test
                kpoints_density=0.04
            )
            print("   [OK] Inputs generated.")
        except Exception as e:
            print(f"   [FAIL] VASPKIT generation failed: {e}")
            return

        # 4. Create Job Script
        print(f"4. creating job script...")
        # Since user mentioned libqdmod.so error, we inject a fix command if we can guess it, 
        # otherwise we just rely on what user said.
        # User said: "Cuidado con lo de intel ... NVHPC".
        # We'll try loading nvhpc if possible, or just print what we are doing.
        
        execution_commands = [
            "# Pre-execution commands for environment setup",
            "echo 'Loading environment from .bashrc exports...'",
            
            # NVHPC 2025 Exports (from .bashrc + Fixes)
            "export NVARCH=`uname -s`_`uname -m`",
            "export NVCOMPILERS=/opt/nvidia/hpc_sdk",
            "export MANPATH=$MANPATH:$NVCOMPILERS/$NVARCH/25.7/compilers/man",
            "export PATH=$NVCOMPILERS/$NVARCH/25.7/compilers/bin:$PATH",
            "export PATH=$NVCOMPILERS/$NVARCH/25.7/comm_libs/mpi/bin:$PATH",
            
            # FIX: Prepend NVHPC lib dir to ensure correct libgomp/libatomic are loaded
            "export LD_LIBRARY_PATH=$NVCOMPILERS/$NVARCH/25.7/compilers/lib:$LD_LIBRARY_PATH",
            
            # Additional libs (QD, Custom HDF5)
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$NVCOMPILERS/$NVARCH/25.7/compilers/extras/qd/lib:/home/deluque/SOFTWARE/TEST_New_HDF5/HDF5_HPCSDK/hdf5-1.14.6/build/lib",
            
            # OMPI Settings",
            "export OMPI_MCA_coll_hcoll_enable=0",
            "export OMPI_MCA_btl=self,tcp",
            "export OMPI_MCA_pml=ob1",
            "export OMP_NUM_THREADS=1",
            
            # Micromamba Initialization (simplified)
            "export PATH=$PATH:/home/deluque/vaspkit.1.3.5/bin",
            
            # FIX: Use manual HDF5 build instead of Micromamba (avoid symbol error)
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/deluque/SOFTWARE/TEST_New_HDF5/HDF5_HPCSDK/hdf5-1.14.6/build/lib",
            
            "command -v vasp_std_gpu"
        ]
        
        job_script = vaspkit.create_job_script(
            work_dir=remote_path,
            job_name="test_api",
            ncores=1, # Use 1 core for test
            walltime="00:10:00",
            execution_commands=execution_commands,
            partition="debug" # Optional: try debug partition? or default
        )
        ssh.upload_text_file(job_script, f"{remote_path}/job.sh")
        
        # 5. Submit
        print(f"5. Submitting job...")
        
        # Try SLURM first
        submit_cmd = f"cd {remote_path} && source ~/.bashrc && sbatch job.sh"
        stdout, stderr, exit_code = ssh.execute_command(submit_cmd)
        
        job_id = None
        mode = "SLURM"
        
        if exit_code == 0:
            job_id = stdout.strip().split()[-1]
            print(f"   [OK] Job submitted via SLURM. ID: {job_id}")
        else:
            print(f"   [INFO] SLURM failed ({stderr.strip()}). Trying Direct Execution...")
            mode = "DIRECT"
            
            # Direct Execution (Nohup)
            direct_cmd = (
                f"cd {remote_path} && "
                f"source ~/.bashrc && "
                f"nohup bash job.sh > vasp_nohup.out 2> vasp_nohup.err & "
                f"echo $!"
            )
            stdout, stderr, exit_code = ssh.execute_command(direct_cmd)
            
            if exit_code != 0:
                print(f"   [FAIL] Direct execution failed: {stderr}")
                return
                
            job_id = stdout.strip()
            print(f"   [OK] Job submitted via Nohup. PID: {job_id}")
        
        # 6. Monitor Status (Simulate API polling)
        print(f"6. Monitoring status (reading .err/.out)...")
        
        # Mocking project object to reuse logic if we wanted, 
        # but let's just check files directly to show user what the API sees.
        await asyncio.sleep(2) # Wait a bit for scheduler/process
        
        if mode == "SLURM":
            # Check queue
            cmd = f"squeue -j {job_id} --noheader"
            stdout, _, _ = ssh.execute_command(cmd)
            if stdout.strip():
                print(f"   Job status: RUNNING/QUEUED (SLURM)")
        else:
            # Check PID
            cmd = f"ps -p {job_id} -o comm="
            stdout, _, _ = ssh.execute_command(cmd)
            if stdout.strip():
                print(f"   Job status: RUNNING (PID {job_id})")
            else:
                print(f"   Job status: FINISHED (PID {job_id} not found)")

        # Check stderr/out (Adjusted for Direct Mode)
        err_file = f"{remote_path}/vasp_{job_id}.err" if mode == "SLURM" else f"{remote_path}/vasp_nohup.err"
        out_file = f"{remote_path}/vasp_{job_id}.out" if mode == "SLURM" else f"{remote_path}/vasp_nohup.out"
        
        if ssh.file_exists(err_file):
            err_content = ssh.read_remote_file(err_file)
            print(f"\n--- STDERR Content ({err_file}) ---")
            print(err_content)
            print("-----------------------------------")
        else:
            print(f"   (.err file not found yet at {err_file})")

        # Check stdout
        if ssh.file_exists(out_file):
            out_content = ssh.read_remote_file(out_file)
            print(f"\n--- STDOUT Content ({out_file}) ---")
            print(out_content[:500] + "..." if len(out_content) > 500 else out_content)
        else:
             print(f"   (.out file not found yet at {out_file})")
        
if __name__ == "__main__":
    asyncio.run(run_real_test())
