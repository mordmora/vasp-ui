import paramiko
import asyncio
from pathlib import Path
from typing import Optional, Tuple, AsyncGenerator
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SSHManager:
    """Maneja conexiones SSH al cluster y operaciones remotas"""
    
    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        
    def connect(self) -> None:
        """Establece conexión SSH al cluster"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Conectar con password o SSH key
            if settings.cluster_ssh_key_path:
                self.client.connect(
                    hostname=settings.cluster_host,
                    port=settings.cluster_port,
                    username=settings.cluster_user,
                    key_filename=settings.cluster_ssh_key_path,
                    timeout=30
                )
            else:
                self.client.connect(
                    hostname=settings.cluster_host,
                    port=settings.cluster_port,
                    username=settings.cluster_user,
                    password=settings.cluster_password,
                    timeout=30
                )
            
            self.sftp = self.client.open_sftp()
            logger.info(f"Conexión SSH establecida a {settings.cluster_host}")
            
        except Exception as e:
            logger.error(f"Error al conectar SSH: {e}")
            raise
    
    def disconnect(self) -> None:
        """Cierra la conexión SSH"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        logger.info("Conexión SSH cerrada")
    
    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """
        Ejecuta un comando en el cluster
        
        Returns:
            Tuple[stdout, stderr, exit_code]
        """
        if not self.client:
            raise ConnectionError("No hay conexión SSH activa")
        
        stdin, stdout, stderr = self.client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        
        stdout_str = stdout.read().decode('utf-8')
        stderr_str = stderr.read().decode('utf-8')
        
        logger.debug(f"Comando: {command}")
        logger.debug(f"Exit code: {exit_code}")
        
        return stdout_str, stderr_str, exit_code
    
    def create_remote_directory(self, path: str) -> None:
        """Crea un directorio en el cluster"""
        command = f"mkdir -p {path}"
        stdout, stderr, exit_code = self.execute_command(command)
        
        if exit_code != 0:
            raise RuntimeError(f"Error creando directorio {path}: {stderr}")
        
        logger.info(f"Directorio creado: {path}")
    
    def upload_file(self, local_path: str, remote_path: str) -> None:
        """Sube un archivo al cluster"""
        if not self.sftp:
            raise ConnectionError("No hay conexión SFTP activa")
        
        try:
            self.sftp.put(local_path, remote_path)
            logger.info(f"Archivo subido: {local_path} -> {remote_path}")
        except Exception as e:
            logger.error(f"Error subiendo archivo: {e}")
            raise
    
    def upload_text_file(self, content: str, remote_path: str) -> None:
        """Sube contenido de texto como archivo al cluster"""
        if not self.sftp:
            raise ConnectionError("No hay conexión SFTP activa")
        
        try:
            with self.sftp.open(remote_path, 'w') as f:
                f.write(content)
            logger.info(f"Archivo de texto subido: {remote_path}")
        except Exception as e:
            logger.error(f"Error subiendo archivo de texto: {e}")
            raise
    
    def download_file(self, remote_path: str, local_path: str) -> None:
        """Descarga un archivo del cluster"""
        if not self.sftp:
            raise ConnectionError("No hay conexión SFTP activa")
        
        try:
            self.sftp.get(remote_path, local_path)
            logger.info(f"Archivo descargado: {remote_path} -> {local_path}")
        except Exception as e:
            logger.error(f"Error descargando archivo: {e}")
            raise
    
    def read_remote_file(self, remote_path: str) -> str:
        """Lee el contenido de un archivo remoto"""
        if not self.sftp:
            raise ConnectionError("No hay conexión SFTP activa")
        
        try:
            with self.sftp.open(remote_path, 'r') as f:
                content = f.read().decode('utf-8')
            return content
        except Exception as e:
            logger.error(f"Error leyendo archivo remoto: {e}")
            raise
    
    def file_exists(self, remote_path: str) -> bool:
        """Verifica si un archivo existe en el cluster"""
        if not self.sftp:
            raise ConnectionError("No hay conexión SFTP activa")
        
        try:
            self.sftp.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
    
    def __enter__(self):
        """Context manager: entrada"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: salida"""
        self.disconnect()


async def get_ssh_manager() -> AsyncGenerator[SSHManager, None]:
    """
    Dependency para obtener un SSHManager
    Uso: ssh = Depends(get_ssh_manager)
    """
    manager = SSHManager()
    try:
        manager.connect()
        yield manager
    finally:
        manager.disconnect()
