from pathlib import Path
import yaml
from dataclasses import dataclass
from dataclasses import asdict

_config = None

def get_config():
    global _config

    if _config is None:
        _config = Config.load()
    return _config

@dataclass
class Config:
    openapi_api_url: str
    openapi_api_model: str
    openapi_api_key: str
    openapi_auth_type: str
    openapi_api_output_mode: str
    # rag_model: str
    # rag_embedding_url: str
    # rag_embedding_authorization: str
    # rag_embedding_chunk_size: int
    # rag_embedding_overlap: int
    # rag_retrieval_url: str
    # rag_retrieval_authorization: str
    use_codex: bool
    codex_executable_path : str
    display_url_for_html_content: str

    def save(self):
        config_file = Path(__file__).parent / "config" / "configuration.yaml"
        try:
            with open(config_file, "w", encoding="utf-8") as file:
                yaml.safe_dump(asdict(self), file)
        except FileNotFoundError:
            print("Configuration file not found")

    @classmethod
    def load(cls):
        config_file = Path(__file__).parent / "config" / "configuration.yaml"
        try:
            with open(config_file, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
        except FileNotFoundError:
            print("Configuration file not found")
            exit(1)
    # try:
        config = cls(
            openapi_api_url = data["openapi_api_url"],
            openapi_api_model= data["openapi_api_model"],
            openapi_api_key= data["openapi_api_key"],
            openapi_auth_type= data["openapi_auth_type"],
            openapi_api_output_mode = data["openapi_api_output_mode"],
            # rag_model= data["rag"]["model"],
            # rag_embedding_url= data["rag_embedding"]["url"],
            # rag_embedding_authorization =data["rag_embedding"]["authorization"],
            # rag_embedding_chunk_size= data["rag_embedding"]["chunk_size"],
            # rag_embedding_overlap= data["rag_embedding"]["overlap"],
            # rag_retrieval_url= data["rag_retrieval"]["url"],
            # rag_retrieval_authorization= data["rag_retrieval"]["authorization"],
            use_codex=data["use_codex"],
            codex_executable_path=data["codex_executable_path"],
            display_url_for_html_content= data["display_url_for_html_content"],


        )
        return config
    # except Exception as e:
    #     print("Error loading configuration")
    #     print(e)
    #     exit(1)

@dataclass
class LastCompletedLesson:
    lesson_path: str
    topic_path: str



    @classmethod
    def load(cls):
        progress_save_path = Path(__file__).resolve().parent / "config" / "progress.yaml"
        try:
            with open(progress_save_path, "r") as file:
                data = yaml.safe_load(file)
        except FileNotFoundError:
            #print("progress file not found, continuing")
            return None

        last_lesson = cls(
            lesson_path = data["lesson_path"],
            topic_path = data["topic_path"],

            )
        return last_lesson


def save_progress(progress_save: LastCompletedLesson):
    progress_save_path = Path(__file__).resolve().parent / "config" / "progress.yaml"
    with open(progress_save_path, "w") as f:
        yaml.safe_dump(asdict(progress_save), f)


