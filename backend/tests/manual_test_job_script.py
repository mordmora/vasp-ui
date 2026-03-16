
import sys
import os
from unittest.mock import MagicMock

# --- MOCKING START ---
# Mock app.config
mock_config = MagicMock()
mock_config.settings.cluster_vasp_path = "vasp_std"
mock_config.settings.cluster_vaspkit_path = "vaspkit"
sys.modules["app.config"] = mock_config

# Mock app.core.ssh_manager
# We need to mock the module so the import in vaspkit_service works
sys.modules["app.core.ssh_manager"] = MagicMock()
# --- MOCKING END ---

# Add backend to path
sys.path.append('/home/mordmora/vasp-ui/backend')

from app.services.vaspkit_service import VASPKITService

def test_create_job_script():
    # Mock SSH Manager instance passed to constructor
    mock_ssh = MagicMock()
    
    service = VASPKITService(mock_ssh)
    
    # Test 1: Basic case (no nodelist/partition)
    script = service.create_job_script(
        work_dir="/tmp/test",
        job_name="test_job",
        ncores=4
    )
    assert "#SBATCH --nodelist" not in script
    assert "#SBATCH --partition" not in script
    print("Test 1 Passed: Basic case")
    
    # Test 2: With nodelist
    script = service.create_job_script(
        work_dir="/tmp/test",
        job_name="test_job",
        ncores=4,
        nodelist="node01"
    )
    assert "#SBATCH --nodelist=node01" in script
    assert "#SBATCH --partition" not in script
    print("Test 2 Passed: Nodelist only")
    
    # Test 3: With partition
    script = service.create_job_script(
        work_dir="/tmp/test",
        job_name="test_job",
        ncores=4,
        partition="gpu"
    )
    assert "#SBATCH --nodelist" not in script
    assert "#SBATCH --partition=gpu" in script
    print("Test 3 Passed: Partition only")
    
    # Test 4: Both
    script = service.create_job_script(
        work_dir="/tmp/test",
        job_name="test_job",
        ncores=4,
        nodelist="node02",
        partition="compute"
    )
    assert "#SBATCH --nodelist=node02" in script
    assert "#SBATCH --partition=compute" in script
    print("Test 4 Passed: Both")

if __name__ == "__main__":
    try:
        test_create_job_script()
        print("All tests passed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
