"""Skills 加载器"""
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class Skill:
    name: str
    version: str
    description: str
    dependencies: list[str]
    triggers: list[str]
    best_practices: str
    examples: list[dict]
    handler_path: Optional[Path] = None


class SkillLoader:
    """Skills 加载器"""

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, Skill] = {}

    def load_all(self):
        """加载所有 Skills"""
        if not self.skills_dir.exists():
            logger.warning(f"Skills 目录不存在: {self.skills_dir}")
            return

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                self._load_skill(skill_dir)

        logger.info(f"已加载 {len(self.skills)} 个 Skills")

    def _load_skill(self, skill_dir: Path):
        """加载单个 Skill"""
        yaml_path = skill_dir / "skill.yaml"
        if not yaml_path.exists():
            return

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            skill = Skill(
                name=data.get("name", skill_dir.name),
                version=data.get("version", "1.0"),
                description=data.get("description", ""),
                dependencies=data.get("dependencies", []),
                triggers=data.get("triggers", []),
                best_practices=data.get("best_practices", ""),
                examples=data.get("examples", [])
            )

            handler_path = skill_dir / "handler.py"
            if handler_path.exists():
                skill.handler_path = handler_path

            self.skills[skill.name] = skill
            logger.debug(f"已加载 Skill: {skill.name}")
        except Exception as e:
            logger.error(f"加载 Skill 失败 {skill_dir}: {e}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """获取 Skill"""
        return self.skills.get(name)

    def match_skill(self, query: str) -> Optional[Skill]:
        """根据用户输入匹配 Skill"""
        query_lower = query.lower()
        for skill in self.skills.values():
            for trigger in skill.triggers:
                if trigger.lower() in query_lower:
                    return skill
        return None

    def get_prompt_context(self) -> str:
        """获取所有 Skills 的提示上下文"""
        if not self.skills:
            return "暂无加载的 Skills"

        lines = ["## 已加载的 Skills\n"]
        for skill in self.skills.values():
            lines.append(f"### {skill.name}")
            lines.append(f"{skill.description}\n")
            lines.append(skill.best_practices)
            lines.append("")

        return "\n".join(lines)
