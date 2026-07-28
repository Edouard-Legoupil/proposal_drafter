from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator


TeamName = Annotated[str, Field(min_length=1, max_length=200)]


class TeamCreate(BaseModel):
    name: TeamName
    description: str | None = Field(default=None, max_length=2000)


class TeamUpdate(BaseModel):
    name: TeamName | None = None
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_a_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one team field is required")
        return self


class TeamRoleAssignment(BaseModel):
    role_key: str | None = Field(default=None, min_length=1, max_length=200)
    role_id: int | None = Field(default=None, gt=0, description="Deprecated numeric role identifier")

    @model_validator(mode="after")
    def require_one_role_identifier(self):
        if (self.role_key is None) == (self.role_id is None):
            raise ValueError("Exactly one of role_key or role_id is required")
        return self


class AccessSettingUpsert(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)
    team_id: str = Field(min_length=1, max_length=200)
    role_key: str = Field(min_length=1, max_length=200)
    key: str = Field(min_length=1, max_length=200)
    value: Any
