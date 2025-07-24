from pydantic import BaseModel

class Tool(BaseModel):
    name: str
    description: str
    params_json_schema: dict