"""
Binance Sentinel
Research material reading and text extraction.
"""

from pathlib import Path


SUPPORTED_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
}


class MaterialReader:
    """
    Reads research material and converts supported files into text.
    """

    def read_file(self, file_path: str) -> str:
        """
        Read a supported research file and return its text.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Research file does not exist: {path}"
            )

        extension = path.suffix.lower()

        if extension not in SUPPORTED_TEXT_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Currently supported: "
                f"{', '.join(sorted(SUPPORTED_TEXT_EXTENSIONS))}"
            )

        return path.read_text(encoding="utf-8")

    def get_file_info(self, file_path: str) -> dict:
        """
        Return basic information about a research file.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Research file does not exist: {path}"
            )

        return {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "supported": path.suffix.lower()
            in SUPPORTED_TEXT_EXTENSIONS,
        }