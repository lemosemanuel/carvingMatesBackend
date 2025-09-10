# utils/validators.py
from typing import Optional, Dict

class CreateUser:
    def __init__(self, full_name: str, email: str, password_hash: str):
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash

class UpdateUser:
    def __init__(self, full_name: Optional[str] = None, email: Optional[str] = None, password_hash: Optional[str] = None):
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash

class CreateRole:
    def __init__(self, name: str):
        self.name = name

class AssignRole:
    def __init__(self, user_id: int, role_id: int):
        self.user_id = user_id
        self.role_id = role_id

class CreateSport:
    def __init__(self, name: str):
        self.name = name

class UserSport:
    def __init__(self, user_id: int, sport_id: int):
        self.user_id = user_id
        self.sport_id = sport_id

class CreateEquipment:
    def __init__(
        self,
        owner_id: int,
        sport_id: int,
        title: str,
        condition_id: int,
        description: Optional[str] = None,
        size: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ):
        self.owner_id = owner_id
        self.sport_id = sport_id
        self.title = title
        self.condition_id = condition_id
        self.description = description
        self.size = size
        self.latitude = latitude
        self.longitude = longitude

class UpdateEquipment:
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        size: Optional[str] = None,
        condition_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ):
        self.title = title
        self.description = description
        self.size = size
        self.condition_id = condition_id
        self.latitude = latitude
        self.longitude = longitude

class EquipmentImage:
    def __init__(self, equipment_id: int, image_url: str):
        self.equipment_id = equipment_id
        self.image_url = image_url

class EquipmentBooking:
    def __init__(
        self,
        equipment_id: int,
        user_id: int,
        start_date: str,
        end_date: str,
        deposit_amount: float,
        status: str = "pending"
    ):
        self.equipment_id = equipment_id
        self.user_id = user_id
        self.start_date = start_date
        self.end_date = end_date
        self.deposit_amount = deposit_amount
        self.status = status

class EquipmentReview:
    def __init__(self, equipment_id: int, reviewer_id: int, rating: int, comment: Optional[str] = None):
        self.equipment_id = equipment_id
        self.reviewer_id = reviewer_id
        self.rating = rating
        self.comment = comment

class EquipmentTip:
    def __init__(self, booking_id: int, amount: float):
        self.booking_id = booking_id
        self.amount = amount

class ForecastSource:
    def __init__(self, name: str):
        self.name = name

class ForecastCreate:
    def __init__(self, sport_id: int, source_id: int, location: str, latitude: float, longitude: float, forecast_date: str, data: Dict):
        self.sport_id = sport_id
        self.source_id = source_id
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.forecast_date = forecast_date
        self.data = data

class SkillVideoCreate:
    def __init__(self, user_id: int, sport_id: int, video_url: str):
        self.user_id = user_id
        self.sport_id = sport_id
        self.video_url = video_url

class SkillAIReviewCreate:
    def __init__(self, skill_video_id: int, review_data: Dict):
        self.skill_video_id = skill_video_id
        self.review_data = review_data

class CoachApplicationCreate:
    def __init__(self, skill_video_id: int, coach_id: int, price: float, experience: str, status: str = "pending"):
        self.skill_video_id = skill_video_id
        self.coach_id = coach_id
        self.price = price
        self.experience = experience
        self.status = status

class CoachReviewCreate:
    def __init__(self, coach_id: int, reviewer_id: int, rating: int, comment: Optional[str] = None):
        self.coach_id = coach_id
        self.reviewer_id = reviewer_id
        self.rating = rating
        self.comment = comment

class SchoolCreate:
    def __init__(self, owner_id: int, name: str, description: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None):
        self.owner_id = owner_id
        self.name = name
        self.description = description
        self.latitude = latitude
        self.longitude = longitude

class SchoolProfessorAssign:
    def __init__(self, school_id: int, professor_id: int):
        self.school_id = school_id
        self.professor_id = professor_id

class ProfessorAvailabilityCreate:
    def __init__(self, professor_id: int, day_of_week: int, start_time: str, end_time: str, location: str):
        self.professor_id = professor_id
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time
        self.location = location

class StudentProfileCreate:
    def __init__(self, student_id: int, sport_id: int, notes: str):
        self.student_id = student_id
        self.sport_id = sport_id
        self.notes = notes

class TravelPlanCreate:
    def __init__(self, user_id: int, destination: str, start_date: str, end_date: str, sport_id: int):
        self.user_id = user_id
        self.destination = destination
        self.start_date = start_date
        self.end_date = end_date
        self.sport_id = sport_id

class TravelMatchCreate:
    def __init__(self, plan_id: int, matched_user_id: int):
        self.plan_id = plan_id
        self.matched_user_id = matched_user_id

class RetreatCreate:
    def __init__(self, host_id: int, title: str, description: str, location: str, start_date: str, end_date: str, sport_id: int):
        self.host_id = host_id
        self.title = title
        self.description = description
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        self.sport_id = sport_id

class RetreatApplicationCreate:
    def __init__(self, retreat_id: int, applicant_id: int, status: str = "pending"):
        self.retreat_id = retreat_id
        self.applicant_id = applicant_id
        self.status = status

class RetreatReviewCreate:
    def __init__(self, retreat_id: int, reviewer_id: int, rating: int, comment: Optional[str] = None):
        self.retreat_id = retreat_id
        self.reviewer_id = reviewer_id
        self.rating = rating
        self.comment = comment
