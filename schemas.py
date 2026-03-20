from pydantic import BaseModel,Field,field_validator

import datetime

import uuid

from typing import Any, Dict, List,Optional,Tuple,Union

import re

class Users(BaseModel):
    name: Optional[str]=None
    email: Optional[str]=None
    password: Optional[str]=None
    mobile: Optional[str]=None


class ReadUsers(BaseModel):
    name: Optional[str]=None
    email: Optional[str]=None
    password: Optional[str]=None
    mobile: Optional[str]=None
    class Config:
        from_attributes = True


class MaysonPlatformAuthOtp(BaseModel):
    email: Optional[str]=None
    otp: Optional[str]=None
    validity: Optional[str]=None
    created_at: Optional[datetime.time]=None


class ReadMaysonPlatformAuthOtp(BaseModel):
    email: Optional[str]=None
    otp: Optional[str]=None
    validity: Optional[str]=None
    created_at: Optional[datetime.time]=None
    class Config:
        from_attributes = True


class Newtable(BaseModel):
    email: Optional[str]=None
    mobile: Optional[Union[int, float]]=None
    password: Optional[str]=None


class ReadNewtable(BaseModel):
    email: Optional[str]=None
    mobile: Optional[Union[int, float]]=None
    password: Optional[str]=None
    class Config:
        from_attributes = True


class Emp1(BaseModel):
    id: int
    email: Optional[str]=None
    password: Optional[str]=None


class ReadEmp1(BaseModel):
    id: int
    email: Optional[str]=None
    password: Optional[str]=None
    class Config:
        from_attributes = True


class ItemsSold(BaseModel):
    quantity: Optional[Union[int, float]]=None
    price_per_item: Optional[Union[int, float]]=None
    price: Optional[float]=None


class ReadItemsSold(BaseModel):
    quantity: Optional[Union[int, float]]=None
    price_per_item: Optional[Union[int, float]]=None
    price: Optional[float]=None
    class Config:
        from_attributes = True


class Students(BaseModel):
    email: Optional[str]=None
    password: Optional[str]=None


class ReadStudents(BaseModel):
    email: Optional[str]=None
    password: Optional[str]=None
    class Config:
        from_attributes = True


class AbgUsers(BaseModel):
    email: Optional[str]=None
    mobile: Optional[Union[int, float]]=None
    password: Optional[str]=None


class ReadAbgUsers(BaseModel):
    email: Optional[str]=None
    mobile: Optional[Union[int, float]]=None
    password: Optional[str]=None
    class Config:
        from_attributes = True


class Products(BaseModel):
    name: Optional[str]=None
    price: Optional[str]=None


class ReadProducts(BaseModel):
    name: Optional[str]=None
    price: Optional[str]=None
    class Config:
        from_attributes = True


class MaysonPlatformAuth(BaseModel):
    email: Optional[str]=None
    password: Optional[str]=None
    is_verified: Optional[str]=None
    created_at: Optional[datetime.time]=None


class ReadMaysonPlatformAuth(BaseModel):
    email: Optional[str]=None
    password: Optional[str]=None
    is_verified: Optional[str]=None
    created_at: Optional[datetime.time]=None
    class Config:
        from_attributes = True


class MaysonRequestLogger(BaseModel):
    ts_utc: Optional[datetime.time]=None
    method: Optional[str]=None
    path: Optional[str]=None
    status_code: Optional[Union[int, float]]=None
    duration_ms: Optional[float]=None
    client_ip: Optional[str]=None
    user_agent: Optional[str]=None
    content_length: Optional[Union[int, float]]=None
    style: Optional[str]=None
    message: Optional[str]=None
    query_params: Optional[str]=None


class ReadMaysonRequestLogger(BaseModel):
    ts_utc: Optional[datetime.time]=None
    method: Optional[str]=None
    path: Optional[str]=None
    status_code: Optional[Union[int, float]]=None
    duration_ms: Optional[float]=None
    client_ip: Optional[str]=None
    user_agent: Optional[str]=None
    content_length: Optional[Union[int, float]]=None
    style: Optional[str]=None
    message: Optional[str]=None
    query_params: Optional[str]=None
    class Config:
        from_attributes = True


class MyAuth(BaseModel):
    username: Optional[str]=None
    address: Optional[str]=None
    mobile_number: Optional[str]=None
    password: Optional[str]=None
    created_at: Optional[datetime.time]=None


class ReadMyAuth(BaseModel):
    username: Optional[str]=None
    address: Optional[str]=None
    mobile_number: Optional[str]=None
    password: Optional[str]=None
    created_at: Optional[datetime.time]=None
    class Config:
        from_attributes = True


class ShivamAuth(BaseModel):
    email: str
    password: str
    mobile: str


class ReadShivamAuth(BaseModel):
    email: str
    password: str
    mobile: str
    class Config:
        from_attributes = True




class PostUsers(BaseModel):
    name: Optional[str]=None
    email: Optional[str]=None
    password: Optional[str]=None
    mobile: Optional[str]=None

    class Config:
        from_attributes = True



class PutUsersId(BaseModel):
    id: Union[int, float] = Field(...)
    name: Optional[str]=None
    email: Optional[str]=None
    password: Optional[str]=None
    mobile: Optional[str]=None

    class Config:
        from_attributes = True



# Query Parameter Validation Schemas

class GetUsersIdQueryParams(BaseModel):
    """Query parameter validation for get_users_id"""
    id: int = Field(..., ge=1, description="Id")

    class Config:
        populate_by_name = True


class DeleteUsersIdQueryParams(BaseModel):
    """Query parameter validation for delete_users_id"""
    id: int = Field(..., ge=1, description="Id")

    class Config:
        populate_by_name = True
