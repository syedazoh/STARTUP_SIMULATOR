"""Shared conversation contracts; identity is never supplied in request bodies."""
from typing import Literal,Annotated
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field,AwareDatetime
Role=Literal['ceo','finance','marketing','operations','strategy','hr']
class Input(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True,allow_inf_nan=False)
class TurnIn(Input):
    request_id:UUID
    content:str=Field(min_length=1,max_length=4000,pattern=r'\S')
    reference_id:str|None=Field(default=None,max_length=80)
    task_id:str|None=Field(default=None,max_length=80)
class Option(Input):
    title:str=Field(min_length=1,max_length=150)
    description:str=Field(min_length=1,max_length=1200)
class Recommendation(Input):
    what:str=Field(min_length=1,max_length=600)
    why_now:str=Field(min_length=1,max_length=1200)
    decision_needed:str=Field(min_length=1,max_length=600)
    options:list[Option]=Field(default_factory=list,max_length=4)
    assumptions:list[Annotated[str,Field(max_length=600)]]=Field(default_factory=list,max_length=8)
    evidence_ids:list[Annotated[str,Field(max_length=120)]]=Field(default_factory=list,max_length=12)
    proposed_steps:list[Annotated[str,Field(max_length=600)]]=Field(default_factory=list,max_length=10)
    image_brief:str|None=Field(default=None,max_length=2000)
class WorkflowReply(Input):
    spoken_response:str=Field(min_length=1,max_length=1200)
    intent:Literal['answer','clarify','missing_data','out_of_scope']='answer'
    recommendation:Recommendation|None=None
class DraftIn(TurnIn):
    recommendation:Recommendation
class PlanIn(Input):
    request_id:UUID
    goal:str=Field(min_length=5,max_length=2000)
    due_at:AwareDatetime
class ActivateIn(Input):
    expected_revision:int=Field(strict=True,ge=0)
class SubmissionIn(Input):
    artifact_id:str=Field(min_length=1,max_length=80)
    expected_fingerprint:str=Field(pattern=r'^[a-f0-9]{64}$')
    image_artifact_ids:list[Annotated[str,Field(max_length=80)]]=Field(default_factory=list,max_length=4)
class ImageIn(Input):
    request_id:UUID
    brief:str=Field(min_length=5,max_length=3000)
    parent_artifact_id:str|None=Field(default=None,max_length=80)
    task_id:str|None=Field(default=None,max_length=80)
