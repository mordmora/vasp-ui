
import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# --- MOCKING SETUP ---
mock_settings = MagicMock()
mock_settings.cluster_host = "test-cluster"
mock_settings.cluster_port = 22
mock_settings.cluster_user = "user"
mock_settings.cluster_password = "password"
mock_settings.cluster_ssh_key_path = None
mock_settings.cluster_work_dir = "/work"
mock_settings.cluster_vasp_path = "vasp"
mock_settings.cluster_vaspkit_path = "vaspkit"
mock_settings.cluster_potcar_path = "/potcar"
mock_settings.cors_origins = ["*"]
# IMPORTANTE: Definir URL válida para SQLAlchemy
mock_settings.database_url = "sqlite+aiosqlite:///:memory:"

module_config = MagicMock()
module_config.settings = mock_settings
sys.modules["app.config"] = module_config

# Mock paramiko
sys.modules["paramiko"] = MagicMock()

# IMPORANTE: Mockear pymatgen antes de importar app, para evitar errores de numpy
mock_pymatgen = MagicMock()
sys.modules["pymatgen"] = mock_pymatgen
sys.modules["pymatgen.core"] = mock_pymatgen
sys.modules["pymatgen.core.Structure"] = MagicMock()

# Add backend to path
sys.path.append('/home/mordmora/vasp-ui/backend')

from fastapi.testclient import TestClient
from app.main import app
from app.models.database import get_db
from app.core.ssh_manager import SSHManager
from app.models.project import Project, ProjectStatus

# --- TEST CLASS ---

class TestRelaxIntegration(unittest.TestCase):
    
    def setUp(self):
        # Mock DB Session
        self.mock_db_session = AsyncMock()
        
        # Override dependency
        async def override_get_db():
            yield self.mock_db_session
        
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        
        # Mock Project Data
        self.mock_project = Project(
            id=1,
            name="Test Project",
            status=ProjectStatus.READY,
            remote_path="/work/project_1",
            poscar="POSCAR CONTENT"
        )

    @patch("app.api.routes.relax.SSHManager")
    def test_submit_relax_job_with_node_selection(self, MockSSHManager):
        # Setup Mock SSH
        mock_ssh_instance = MockSSHManager.return_value.__enter__.return_value
        mock_ssh_instance.execute_command.return_value = ("Submitted batch job 12345", "", 0)
        mock_ssh_instance.file_exists.return_value = True 
        
        # Setup Mock DB Query Result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.mock_project
        self.mock_db_session.execute.return_value = mock_result
        
        # Payload with nodelist and partition
        payload = {
            "project_id": 1,
            "ncores": 8,
            "walltime": "12:00:00",
            "nodelist": "node-05",
            "partition": "high-mem"
        }
        
        # Executing request
        print("Sending POST request to /api/relax/submit...")
        response = self.client.post("/api/relax/submit", json=payload)
        
        # Print response if it failed
        if response.status_code != 200:
            print(f"Request failed: {response.json()}")
            
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["job_id"], "12345")
        
        # Verify SSH upload
        upload_calls = mock_ssh_instance.upload_text_file.call_args_list
        job_script_content = None
        for args, _ in upload_calls:
            content, path = args
            if path.endswith("job.sh"):
                job_script_content = content
                break
                
        self.assertIsNotNone(job_script_content, "job.sh was not uploaded")
        self.assertIn("#SBATCH --nodelist=node-05", job_script_content)
        self.assertIn("#SBATCH --partition=high-mem", job_script_content)
        print("test_submit_relax_job_with_node_selection: PASSED")

    @patch("app.api.routes.relax.SSHManager")
    def test_submit_relax_job_without_node_selection(self, MockSSHManager):
        # Setup Mock SSH
        mock_ssh_instance = MockSSHManager.return_value.__enter__.return_value
        mock_ssh_instance.execute_command.return_value = ("Submitted batch job 67890", "", 0)
        mock_ssh_instance.file_exists.return_value = True
        
        # Setup Mock DB
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.mock_project
        self.mock_db_session.execute.return_value = mock_result
        
        # Payload WITHOUT nodelist/partition
        payload = {
            "project_id": 1,
            "ncores": 4
        }
        
        # Executing request
        response = self.client.post("/api/relax/submit", json=payload)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Verify SSH content
        upload_calls = mock_ssh_instance.upload_text_file.call_args_list
        job_script_content = None
        for args, _ in upload_calls:
            content, path = args
            if path.endswith("job.sh"):
                job_script_content = content
                break
                
        self.assertIsNotNone(job_script_content)
        self.assertNotIn("#SBATCH --nodelist", job_script_content)
        self.assertNotIn("#SBATCH --partition", job_script_content)
        print("test_submit_relax_job_without_node_selection: PASSED")

    @patch("app.api.routes.relax.SSHManager")
    def test_submit_relax_job_with_execution_commands(self, MockSSHManager):
        # Setup Mock SSH
        mock_ssh_instance = MockSSHManager.return_value.__enter__.return_value
        mock_ssh_instance.execute_command.return_value = ("Submitted batch job 112233", "", 0)
        mock_ssh_instance.file_exists.return_value = True
        
        # Setup Mock DB
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.mock_project
        self.mock_db_session.execute.return_value = mock_result
        
        # Payload with execution commands
        payload = {
            "project_id": 1,
            "ncores": 4,
            "execution_commands": [
                "module load cuda/11.0",
                "export LD_LIBRARY_PATH=/libs:$LD_LIBRARY_PATH"
            ]
        }
        
        # Executing request
        response = self.client.post("/api/relax/submit", json=payload)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Verify Job Script Content
        upload_calls = mock_ssh_instance.upload_text_file.call_args_list
        job_script_content = None
        for args, _ in upload_calls:
            content, path = args
            if path.endswith("job.sh"):
                job_script_content = content
                break
                
        self.assertIsNotNone(job_script_content)
        self.assertIn("module load cuda/11.0", job_script_content)
        self.assertIn("export LD_LIBRARY_PATH=/libs:$LD_LIBRARY_PATH", job_script_content)
        # Verify order: commands should be before execution
        execution_pos = job_script_content.find("mpirun")
        command_pos = job_script_content.find("module load")
        self.assertLess(command_pos, execution_pos, "Setup commands must appear before execution")
        print("test_submit_relax_job_with_execution_commands: PASSED")

if __name__ == "__main__":
    unittest.main()
