
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.core.ssh_manager import SSHManager

async def debug_libs():
    with SSHManager() as ssh:
        print("Debugging Library Resolution in Non-Interactive Mode...")
        
        # The exact exports we are using in the submission script
        env_setup = """
        export NVARCH=`uname -s`_`uname -m`
        export NVCOMPILERS=/opt/nvidia/hpc_sdk
        export MANPATH=$MANPATH:$NVCOMPILERS/$NVARCH/25.7/compilers/man
        export PATH=$NVCOMPILERS/$NVARCH/25.7/compilers/bin:$PATH
        export PATH=$NVCOMPILERS/$NVARCH/25.7/comm_libs/mpi/bin:$PATH
        export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$NVCOMPILERS/$NVARCH/25.7/compilers/extras/qd/lib:/home/deluque/SOFTWARE/TEST_New_HDF5/HDF5_HPCSDK/hdf5-1.14.6/build/lib
        export OMPI_MCA_coll_hcoll_enable=0
        export OMPI_MCA_btl=self,tcp
        export OMPI_MCA_pml=ob1
        export OMP_NUM_THREADS=1
        export PATH=$PATH:/home/deluque/vaspkit.1.3.5/bin
        """
        
        # Command to check ldd and environment
        cmd = f"""
        {env_setup}
        echo "--- LD_LIBRARY_PATH ---"
        echo $LD_LIBRARY_PATH
        echo "--- LDD OUTPUT ---"
        ldd /usr/local/bin/vasp_std_gpu | grep -i 'omp\|qd\|hdf5'
        echo "--- FULL LDD ---"
        ldd /usr/local/bin/vasp_std_gpu
        """
        
        stdout, stderr, exit_code = ssh.execute_command(cmd)
        print(stdout)
        if stderr:
            print("STDERR:", stderr)

if __name__ == "__main__":
    asyncio.run(debug_libs())
