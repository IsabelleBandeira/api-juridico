
from pydantic import BaseModel, ConfigDict, Field


class SchemaResposta(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class EnderecoResposta(SchemaResposta):
    logradouro: str
    complemento: str | None
    cidade: str
    cep: str


class EmpresaResposta(SchemaResposta):
    nome: str | None
    segmento: str | None


class DocumentoResposta(SchemaResposta):
    id: int
    codigo_externo: int = Field(serialization_alias="codigoExterno")
    titulo: str
    url: str
    url_thumbnail: str | None = Field(serialization_alias="thumbnailUrl")


class AcordoResposta(SchemaResposta):
    id: int
    codigo_externo: int = Field(serialization_alias="codigoExterno")
    titulo: str
    total_documentos: int = Field(serialization_alias="totalDocumentos")
    documentos: list[DocumentoResposta]


class AutorResposta(SchemaResposta):
    id: int
    codigo_externo: int = Field(serialization_alias="codigoExterno")
    nome: str
    email: str
    numero_telefone: str
    endereco: EnderecoResposta
    empresa: EmpresaResposta
    total_acordos: int = Field(serialization_alias="totalAcordos")
    total_documentos: int = Field(serialization_alias="totalDocumentos")
    acordos: list[AcordoResposta]


class UsuarioResposta(BaseModel):
    autor: AutorResposta
