from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AutorMensagem(SchemaBase):
    id_externo: int = Field(gt=0)
    nome: str
    email: str
    telefone: str
    rua: str
    complemento: str | None = None
    cidade: str
    cep: str
    nome_empresa: str | None = None
    segmento_empresa: str | None = None


class AcordoMensagem(SchemaBase):
    id_externo: int = Field(gt=0)
    titulo: str


class DocumentoMensagem(SchemaBase):
    id_externo: int = Field(gt=0)
    titulo: str
    url: str
    url_miniatura: str | None = None


class MensagemIngestao(SchemaBase):
    message_id: str
    correlation_id: str
    autor: AutorMensagem
    acordo: AcordoMensagem | None
    documentos: list[DocumentoMensagem] = Field(default_factory=list)