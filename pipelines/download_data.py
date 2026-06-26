"""
Pipeline de ingestão: baixa o dataset de fraude do Kaggle e valida integridade.

Uso:
    uv run python pipelines/download_data.py
"""

import hashlib
import os
from pathlib import Path

import kaggle  # type: ignore[import-untyped]

# ── Configuração ──────────────────────────────────────────────────────────────

DATASET_REF = "mlg-ulb/creditcardfraud"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
TARGET_FILE = RAW_DIR / "creditcard.csv"

# Hash MD5 conhecido do arquivo oficial (garante que o arquivo não foi corrompido)
EXPECTED_MD5 = "e90efcb83d69faf99fcab8b0255024de"


# ── Funções ───────────────────────────────────────────────────────────────────

def _md5(path: Path) -> str:
    """Calcula o hash MD5 de um arquivo em blocos (não carrega tudo na memória)."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download() -> Path:
    """Baixa o dataset do Kaggle se ainda não existir localmente."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if TARGET_FILE.exists():
        print(f"Dataset ja existe em: {TARGET_FILE}")
        return TARGET_FILE

    print(f"Baixando dataset '{DATASET_REF}' do Kaggle...")
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        DATASET_REF,
        path=str(RAW_DIR),
        unzip=True,
        quiet=False,
    )
    print(f"Download concluido: {TARGET_FILE}")
    return TARGET_FILE


def validate(path: Path) -> None:
    """Valida tamanho mínimo e integridade MD5 do arquivo."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb < 130:
        raise ValueError(f"Arquivo suspeito - tamanho {size_mb:.1f}MB (esperado ~144MB)")

    print(f"Tamanho: {size_mb:.1f}MB [OK]")

    actual_md5 = _md5(path)
    if actual_md5 != EXPECTED_MD5:
        raise ValueError(
            f"Hash MD5 invalido.\n"
            f"  Esperado: {EXPECTED_MD5}\n"
            f"  Recebido: {actual_md5}\n"
            "O arquivo pode estar corrompido ou ser uma versao diferente."
        )
    print(f"MD5: {actual_md5} [OK]")


def main() -> None:
    print("=" * 50)
    print("Pipeline de Ingestao - Credit Card Fraud")
    print("=" * 50)

    path = download()
    validate(path)

    print("\nDataset pronto para uso.")
    print(f"Localizacao: {path.resolve()}")


if __name__ == "__main__":
    # Garante que KAGGLE_CONFIG_DIR aponta para ~/.kaggle no Windows
    if os.name == "nt" and "KAGGLE_CONFIG_DIR" not in os.environ:
        os.environ["KAGGLE_CONFIG_DIR"] = str(Path.home() / ".kaggle")
    main()
