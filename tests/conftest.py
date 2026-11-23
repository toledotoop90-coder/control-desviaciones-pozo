from pathlib import Path

import pandas as pd
import pytest

from costos import pipeline, sintetico

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def carpeta_sintetica(tmp_path_factory) -> Path:
    """Pozo sintético generado desde cero para cada sesión de pruebas."""
    return sintetico.generar(tmp_path_factory.mktemp("sintetico"))


@pytest.fixture(scope="session")
def resultado(carpeta_sintetica) -> pipeline.Resultado:
    return pipeline.analizar(carpeta_sintetica)


@pytest.fixture
def etapas_simples() -> pd.DataFrame:
    return pd.DataFrame(
        [("E1", "Etapa 1", "cerrada", 0, 100, 1.0, 1.0), ("E2", "Etapa 2", "abierta", 100, 200, 1.0, None)],
        columns=["etapa", "nombre", "estado", "prof_inicio", "prof_fin", "dias_programa", "dias_real"],
    )


@pytest.fixture
def raiz() -> Path:
    return RAIZ
