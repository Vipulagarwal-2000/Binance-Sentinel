"""
Binance Sentinel
Research material management.
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from config import CASES_DIR


class FileManager:
    """
    Manages research material attached to a Sentinel research case.
    """

    def __init__(self, cases_dir: Path = CASES_DIR):
        self.cases_dir = cases_dir

    def _case_directory(self, case_id: str) -> Path:
        return self.cases_dir / case_id

    def _materials_directory(self, case_id: str) -> Path:
        directory = self._case_directory(case_id) / "materials"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _metadata_file(self, case_id: str) -> Path:
        return self._materials_directory(case_id) / "metadata.json"

    def add_file(
        self,
        case_id: str,
        source_file: str,
        name: str,
        category: str,
        tags=None,
    ) -> dict:
        """
        Add a research file to a case.

        The original file is copied into the case's materials directory.
        """

        source = Path(source_file)

        if not source.exists():
            raise FileNotFoundError(
                f"Source file does not exist: {source}"
            )

        case_directory = self._case_directory(case_id)

        if not case_directory.exists():
            raise FileNotFoundError(
                f"Research case '{case_id}' does not exist."
            )

        materials_directory = self._materials_directory(case_id)

        safe_name = self._safe_filename(name, source.suffix)

        destination = materials_directory / safe_name

        shutil.copy2(source, destination)

        metadata = {
            "id": self._generate_material_id(),
            "name": name,
            "filename": safe_name,
            "category": category,
            "tags": tags or [],
            "source": str(source),
            "added_at": datetime.now().isoformat(),
        }

        materials = self.list_materials(case_id)
        materials.append(metadata)

        self._save_metadata(case_id, materials)

        return metadata

    def list_materials(self, case_id: str) -> list:
        """
        Return all research material attached to a case.
        """

        metadata_file = self._metadata_file(case_id)

        if not metadata_file.exists():
            return []

        with metadata_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def remove_file(self, case_id: str, material_id: str):
        """
        Remove a research material item from a case.
        """

        materials = self.list_materials(case_id)

        remaining = []
        removed = None

        for material in materials:
            if material["id"] == material_id:
                removed = material
            else:
                remaining.append(material)

        if removed is None:
            raise ValueError(
                f"Material '{material_id}' was not found."
            )

        file_path = (
            self._materials_directory(case_id)
            / removed["filename"]
        )

        if file_path.exists():
            file_path.unlink()

        self._save_metadata(case_id, remaining)

    def _save_metadata(self, case_id: str, materials: list):
        """
        Save material metadata.
        """

        metadata_file = self._metadata_file(case_id)

        with metadata_file.open("w", encoding="utf-8") as file:
            json.dump(
                materials,
                file,
                indent=4,
                ensure_ascii=False,
            )

    @staticmethod
    def _safe_filename(name: str, suffix: str) -> str:
        """
        Convert a user-provided name into a safe filename.
        """

        cleaned = re.sub(r'[<>:"/\\|?*]', "", name)
        cleaned = cleaned.strip()

        if not cleaned:
            cleaned = "research_material"

        if not cleaned.lower().endswith(suffix.lower()):
            cleaned += suffix

        return cleaned

    @staticmethod
    def _generate_material_id() -> str:
        """
        Generate a simple unique material ID.
        """

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")

        return f"MAT_{timestamp}"