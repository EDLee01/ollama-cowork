"""工具执行器 - 支持 Docker 沙盒"""
import docker
from typing import Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class SandboxConfig:
    image: str = "local-cowork-sandbox:latest"
    memory_limit: str = "4g"
    cpu_limit: int = 4
    network_mode: str = "bridge"
    auto_remove: bool = True


class DockerExecutor:
    """Docker 沙盒执行器"""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.client = docker.from_env()
        self.container = None

    def start(self, workspace: str):
        """启动沙盒容器"""
        try:
            self.container = self.client.containers.run(
                self.config.image,
                detach=True,
                tty=True,
                volumes={
                    workspace: {"bind": "/workspace", "mode": "rw"}
                },
                working_dir="/workspace",
                mem_limit=self.config.memory_limit,
                cpu_count=self.config.cpu_limit,
                network_mode=self.config.network_mode,
                auto_remove=self.config.auto_remove
            )
            logger.info(f"沙盒容器已启动: {self.container.short_id}")
        except Exception as e:
            logger.error(f"启动沙盒失败: {e}")
            raise

    def execute(self, command: str, timeout: int = 30) -> tuple[int, str]:
        """在沙盒中执行命令"""
        if not self.container:
            raise RuntimeError("沙盒容器未启动")

        try:
            exit_code, output = self.container.exec_run(
                cmd=["sh", "-c", command],
                workdir="/workspace",
                demux=True
            )

            stdout = output[0].decode() if output[0] else ""
            stderr = output[1].decode() if output[1] else ""

            return exit_code, stdout + stderr
        except Exception as e:
            return 1, str(e)

    def stop(self):
        """停止沙盒容器"""
        if self.container:
            try:
                self.container.stop()
                logger.info("沙盒容器已停止")
            except:
                pass
            self.container = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
