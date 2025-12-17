"""
Setup script для InfBez CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Чтение README для long_description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Чтение зависимостей из централизованного requirements.txt
def read_requirements(filename):
    """Чтение requirements из файла"""
    requirements = []
    req_file = Path(__file__).parent / filename

    if req_file.exists():
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии, пустые строки и -r директивы
                if line and not line.startswith('#') and not line.startswith('-r'):
                    requirements.append(line)

    return requirements

# Базовые зависимости для CLI
install_requires = read_requirements('requirements.txt')

setup(
    name="infbez-cli",
    version="1.0.0",
    author="InfBez Team",
    description="CLI интерфейс для криптографических операций InfBez",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/infbez",
    packages=find_packages(include=["cli", "cli.*", "algorithms", "algorithms.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security :: Cryptography",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require={
        "dev": read_requirements('requirements-dev.txt'),
    },
    entry_points={
        "console_scripts": [
            "infbez=cli.main:app",
        ],
    },
    include_package_data=True,
    package_data={
        "algorithms": ["*/consts.py"],
        "cli": ["*.py", "commands/*.py"],
    },
)
