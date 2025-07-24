
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Literal

class FactorySpec(BaseModel):
    fn: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

class ParamSetter(BaseModel):
    target: str
    factory: FactorySpec

class AdapterSpec(BaseModel):
    base_uri: str
    method: Literal['GET','POST'] = 'GET'
    query: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)

class AdapterConfig(BaseModel):
    timeout: float = 3.0

class AdapterDef(BaseModel):
    spec: AdapterSpec
    config: AdapterConfig

class EndpointDef(BaseModel):
    id: str
    name: str
    adapter_id: str
    priority: int = 0
    set_params: List[ParamSetter] = Field(default_factory=list)

class GroupDef(BaseModel):
    id: str
    priority: int = 0
    mode: Literal['waterfall','parallel'] = 'waterfall'
    endpoints: List[str]

class ManifestModel(BaseModel):
    id: str
    strategy: Literal['waterfall','parallel'] = 'waterfall'
    adapters: Dict[str, AdapterDef]
    endpoints: List[EndpointDef]
    groups: List[GroupDef]
