import logging
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple
from config import settings

logger = logging.getLogger(__name__)


class HtmlConverter:
    """Конвертер HTML файлов в Markdown с использованием tidy и pandoc."""

    def __init__(self):
        self.output_format = "markdown_strict+grid_tables+superscript+subscript"
        self._validate_tools()

    @staticmethod
    def _validate_tools() -> None:
        """Проверка доступности бинарников в PATH один раз при инициализации."""
        for tool in ['tidy', 'pandoc']:
            if not shutil.which(tool):
                raise RuntimeError(f"Инструмент '{tool}' не найден в системе PATH.")

    def convert_file(self, html_path: Path, output_path: Path) -> bool:
        """Конвертирует один HTML файл в Markdown."""
        tidy_cmd = [
            "tidy", "-quiet", "--show-warnings", "no",
            "--force-output", "yes", "-utf8", str(html_path)
        ]
        
        pandoc_cmd = [
            "pandoc",
            "-f", "html",
            "-t", self.output_format,
            f"--lua-filter={settings.lua_filter_path}",
            "--wrap=none",
            "-o", str(output_path)
        ]

        try:
            tidy_proc = subprocess.Popen(tidy_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            pandoc_proc = subprocess.Popen(
                pandoc_cmd,
                stdin=tidy_proc.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if tidy_proc.stdout:
                tidy_proc.stdout.close()

            _, stderr = pandoc_proc.communicate(timeout=300)
            
            if pandoc_proc.returncode != 0:
                err_text = stderr.decode('utf-8', errors='ignore')[:200] if stderr else "Unknown error"
                logger.error(f"Ошибка Pandoc для {html_path}: {err_text}")
                return False

            return output_path.exists() and output_path.stat().st_size > 0

        except Exception as e:
            logger.error(f"Исключение при конвертации {html_path}: {e}")
            if output_path.exists() and output_path.stat().st_size == 0:
                output_path.unlink()
            return False

    def convert_directory(self, root_dir: Path) -> Tuple[int, int]:
        """Сканирует директорию и конвертирует все найденные HTML файлы."""
        html_files: List[Path] = []
        for pattern in ["*.htm", "*.html", "index.htm"]:
            html_files.extend(root_dir.rglob(pattern))
        
        html_files = list(set(html_files))
        success_count, skipped_count = 0, 0

        for html_path in html_files:
            output_path = html_path.parent / f"{html_path.stem}.md"
            if output_path.exists() and output_path.stat().st_size > 0:
                skipped_count += 1
                continue
            
            if self.convert_file(html_path, output_path):
                success_count += 1

        return success_count, skipped_count