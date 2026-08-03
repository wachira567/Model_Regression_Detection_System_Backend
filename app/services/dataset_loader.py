import json
from pathlib import Path
from pydantic import BaseModel

class TestCaseData(BaseModel):
    id: str
    input: dict
    expected_output: dict
    difficulty: str = "medium"
    tags: list[str] = []
    notes: str = ""

class GoldenDatasetData(BaseModel):
    dataset_id: str
    version: str
    created_at: str
    feature_id: str
    description: str
    test_cases: list[TestCaseData]

class DatasetLoader:
    def __init__(self, dataset_dir: str):
        self.dataset_dir = Path(dataset_dir)

    def load_all(self) -> list[GoldenDatasetData]:
        datasets = []
        if not self.dataset_dir.exists():
            return datasets
            
        for file in self.dataset_dir.glob("*.json"):
            with open(file, "r") as f:
                data = json.load(f)
                datasets.append(GoldenDatasetData(**data))
        return datasets
