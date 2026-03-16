
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# --- MOCKING SETUP ---
# Mock settings
mock_settings = MagicMock()
mock_settings.cluster_host = "test-cluster"
mock_settings.cluster_vasp_path = "vasp_std"
mock_settings.cluster_vaspkit_path = "vaspkit"
mock_settings.cluster_work_dir = "/work"
# Fix: Add database_url to mock settings to avoid SQLAlchemy initialization error
mock_settings.database_url = "sqlite+aiosqlite:///:memory:"

module_config = MagicMock()
module_config.settings = mock_settings
sys.modules["app.config"] = module_config

# Mock paramiko
sys.modules["paramiko"] = MagicMock()

# Mock pymatgen to avoid numpy errors
mock_pymatgen = MagicMock()
sys.modules["pymatgen"] = mock_pymatgen
sys.modules["pymatgen.core"] = mock_pymatgen
sys.modules["pymatgen.core.Structure"] = MagicMock()

# Add backend to path
sys.path.append('/home/mordmora/vasp-ui/backend')

# Import app modules AFTER mocking
from app.schemas.project import JobSubmitRequest, ProjectStatus
from app.models.project import Project
from app.api.routes.relax import submit_relax_job

class TestRelaxServiceLogic(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = AsyncMock()
        self.mock_bg_tasks = MagicMock()
        
        self.mock_project = Project(
            id=1,
            name="Test Project",
            status=ProjectStatus.READY,
            remote_path="/work/project_1",
            poscar="POSCAR",
            job_id=None
        )

    @patch("app.api.routes.relax.SSHManager")
    def test_submit_logic_with_execution_commands(self, MockSSHManager):
        # Setup mocks
        mock_ssh = MockSSHManager.return_value.__enter__.return_value
        mock_ssh.execute_command.return_value = ("Submitted batch job 9999", "", 0)
        mock_ssh.file_exists.return_value = True
        
        # Mock DB project fetch
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.mock_project
        self.mock_db.execute.return_value = mock_result
        
        # Request with execution commands
        request = JobSubmitRequest(
            project_id=1,
            ncores=16,
            execution_commands=[
                "module load intel/2024",
                "export OMP_NUM_THREADS=4"
            ]
        )
        
        # Call function directly (async test runner would be better but we can run loop manually)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            submit_relax_job(request=request, background_tasks=self.mock_bg_tasks, db=self.mock_db)
        )
        loop.close()
        
        # Assertions
        self.assertEqual(response.status, ProjectStatus.RUNNING)
        self.assertEqual(response.job_id, "9999")
        
        # Verify Script Content
        upload_calls = mock_ssh.upload_text_file.call_args_list
        job_script = None
        for args, _ in upload_calls:
            content, path = args
            if path.endswith("job.sh"):
                job_script = content
                break
        
        self.assertIsNotNone(job_script)
        print("\nGenerated Job Script:")
        print(job_script)
        
        self.assertIn("module load intel/2024", job_script)
        self.assertIn("export OMP_NUM_THREADS=4", job_script)
        self.assertIn("mpirun -np 16", job_script)
        
        print("\nSUCCESS: Execution commands were correctly injected into the job script.")

if __name__ == "__main__":
    unittest.main()
