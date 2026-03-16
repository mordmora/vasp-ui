
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# --- MOCKING SETUP ---
mock_settings = MagicMock()
mock_settings.cluster_host = "test-cluster"
mock_settings.cluster_vasp_path = "vasp_std_gpu"
mock_settings.cluster_vaspkit_path = "vaspkit"
mock_settings.cluster_work_dir = "/work"
mock_settings.database_url = "sqlite+aiosqlite:///:memory:"

module_config = MagicMock()
module_config.settings = mock_settings
sys.modules["app.config"] = module_config

# Mock paramiko
sys.modules["paramiko"] = MagicMock()

# Mock pymatgen
mock_pymatgen = MagicMock()
sys.modules["pymatgen"] = mock_pymatgen
sys.modules["pymatgen.core"] = mock_pymatgen
sys.modules["pymatgen.core.Structure"] = MagicMock()

# Add backend to path
sys.path.append('/home/mordmora/vasp-ui/backend')

# Import app modules AFTER mocking
from app.models.project import Project, ProjectStatus
from app.api.routes.relax import get_relax_status

class TestMonitorLogic(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = AsyncMock()
        
        self.mock_project = Project(
            id=1,
            name="Test Project",
            status=ProjectStatus.RUNNING,
            remote_path="/work/project_1",
            job_id="12345",
            error_log=None
        )

    @patch("app.api.routes.relax.SSHManager")
    def test_job_failed_with_stderr(self, MockSSHManager):
        # Setup mocks
        mock_ssh = MockSSHManager.return_value.__enter__.return_value
        
        # 1. squeue returns empty (job finished)
        mock_ssh.execute_command.side_effect = [
            ("", "", 0),  # squeue output empty
        ]
        
        # 2. Files existence checks
        # file_exists calls: OUTCAR (False), CONTCAR (False), err file (True), out file (True)
        def file_exists_side_effect(path):
            if path.endswith("OUTCAR"): return False
            if path.endswith("CONTCAR"): return False
            if path.endswith(".err"): return True
            if path.endswith(".out"): return True
            return False
            
        mock_ssh.file_exists.side_effect = file_exists_side_effect
        
        # 3. Read file content
        def read_file_side_effect(path):
            if path.endswith(".err"):
                 return "slurmstepd: error: execve(): vasp_std: No such file or directory"
            if path.endswith(".out"):
                 return "Starting job..."
            return ""
            
        mock_ssh.read_remote_file.side_effect = read_file_side_effect
        
        # Mock DB project fetch
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.mock_project
        self.mock_db.execute.return_value = mock_result
        
        # Execute test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                get_relax_status(project_id=1, db=self.mock_db)
            )
        finally:
            loop.close()
        
        # Assertions
        print(f"Status: {response.status}")
        print(f"Current Step: {response.current_step}")
        print(f"Error Details: {response.error_details}")
        
        self.assertEqual(response.status, ProjectStatus.FAILED)
        self.assertEqual(response.current_step, "Job failed - startup error")
        self.assertIn("vasp_std: No such file", response.error_details)
        print("test_job_failed_with_stderr: PASSED")

if __name__ == "__main__":
    unittest.main()
