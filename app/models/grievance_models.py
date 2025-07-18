from pydantic import BaseModel, Field
from typing import Optional, List

# Grievance status options
STATUS_OPTIONS = [
    "Active",
    "Pending",
    "Closed with resolution",
    "Closed without resolution",
    "Tender Issued"
]

class GrievanceBase(BaseModel):
    title: str
    category: str
    description: str
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")
    cpgrams_category: Optional[str] = None


class GrievanceCreate(BaseModel):
    title: str
    category: str
    description: str
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")
    user_id: str
    cpgrams_category: Optional[str] = None
    reformed_top_level_category: Optional[str] = None
    reformed_last_level_category: Optional[str] = None
    reformed_flag: Optional[bool] = False
    # Any other optional fields can be added here


class GrievanceUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    officer_closed_by: Optional[str] = None
    final_status: Optional[str] = None
    grievance_closing_date: Optional[str] = None


class Grievance(GrievanceBase):
    id: str
    user_id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    grievance_received_date: Optional[str] = None
    grievance_closing_date: Optional[str] = None
    organisation_closing_date: Optional[str] = None
    org_status_date: Optional[str] = None
    reported_as_covid19_case_date: Optional[str] = None
    reformed_flag: Optional[bool] = False
    forwarded_to_subordinate: Optional[bool] = False
    forwarded_to_subordinate_details: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    satisfaction_level: Optional[str] = None
    final_reply: Optional[str] = None
    appeal_no: Optional[str] = None
    appeal_date: Optional[str] = None
    appeal_reason: Optional[str] = None
    appeal_closing_date: Optional[str] = None
    appeal_closing_remarks: Optional[str] = None
    organisation_grievance_receive_date: Optional[str] = None
    organisation_grievance_close_date: Optional[str] = None
    officers_forwarding_grievance: Optional[str] = None
    date_of_receiving: Optional[str] = None
    officer_closed_by: Optional[str] = None
    final_status: Optional[str] = None
    # Fields for category and follow-up state management
    classified_category: Optional[str] = None
    formatted_fields: Optional[str] = None
    follow_up_questions: Optional[List[str]] = None
    missing_information: Optional[bool] = None
    is_correct_category: Optional[bool] = None
    category_data: Optional[dict] = None


class FollowUpQuestions(BaseModel):
    is_correct_category: bool
    missing_information: bool
    follow_up_questions: List[str]


class FollowUpResponse(BaseModel):
    additional_information: str


class AnswerVerification(BaseModel):
    all_questions_answered: bool
    additional_follow_up_needed: bool
    suggested_follow_up: List[str] = Field(default_factory=list)


class GrievanceCategoryRequest(BaseModel):
    grievance_text: str


class FAQRequest(BaseModel):
    query: str
    limit: int = Field(default=5, description="Maximum number of FAQ items to return")


class FAQItem(BaseModel):
    id: str
    code: str
    question: str
    answer: str


class FAQResponse(BaseModel):
    status: str
    faqs: List[FAQItem]
    count: int