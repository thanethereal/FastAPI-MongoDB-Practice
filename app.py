from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response
from pymongo import ReturnDocument
import motor.motor_asyncio
import os
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator
from typing import Optional, List
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

app = FastAPI(title="Student Course API",
              summary="A sample application showing hơ to use FastAPI to add a Rest API to a MongoDB collection")
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.college
student_collection = db.get_collection("students")

class StudentModel(BaseModel):
    """
    Container for a single student record.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    email: EmailStr = Field(...)
    course: str = Field(...)
    gpa: float = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example":{
                "name": "Minh Than",
                "email": "thanvm2000@gmail.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": 3.2
            }
        }
    )

class StudentCollection(BaseModel):
    """
    A container holding a list of `StudentModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """

    students: List[StudentModel]

@app.post("/students/",
          response_description="Add new student",
          response_model=StudentModel,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
async def create_student(student: StudentModel = Body(...)):
    """
    Insert a new student record.

    A unique `id` will be created and provided in the response.
    """

    new_student = await student_collection.insert_one(student.model_dump(by_alias=True, exclude=["id"]))
    created_student = await student_collection.find_one({"_id": new_student.inserted_id})
    return created_student

@app.get("/students",
         response_description="List all students",
         response_model=StudentCollection,
         response_model_by_alias=False)
async def list_students():
    """
    List all of the student data in the database.
    The response is unpaginated and limited to 1000 result.
    """
    return StudentCollection(students=await student_collection.find().to_list(100))