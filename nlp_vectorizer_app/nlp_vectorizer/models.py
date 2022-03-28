from pydantic import BaseModel


class VectorResponse(BaseModel):
    vector: list


class VectorizeQuery(BaseModel):
    text: str
