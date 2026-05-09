from pydantic import BaseModel
from typing import List, Optional

# --- STUDENT MODELS START ---
class Profile(BaseModel):
    full_name: str
    grade: str
    dob: str
    disability_categories: List[str]
    primary_language: str
    english_learner: bool
    assistive_tech_required: bool
    placement: str

class PLAAFP(BaseModel):
    domain: str
    current_levels: str
    strengths: str
    disability_impact: str
    source_page: Optional[int] = None

class Goal(BaseModel):
    id: str
    area: str  # counseling | math | ela
    baseline: str
    annual_target: str
    criteria: str
    method: str
    schedule: str
    responsible: str
    short_term_objectives: List[str]
    source_page: Optional[int] = None

class Accommodation(BaseModel):
    id: str
    category: str
    label: str
    source_page: Optional[int] = None

class Modification(BaseModel):
    dimension: str  # content | instruction | output
    label: str

class Service(BaseModel):
    goal_ids: List[str]
    type: str
    provider: str
    location: str
    frequency: str
    start_date: str
    end_date: str

class AssessmentAccommodations(BaseModel):
    test: str  # e.g., "MCAS 3-8"
    content_areas: List[str]
    accessibility_features: List[str]
    presentation_accommodations: List[str]

class KeyDates(BaseModel):
    iep_start: str
    iep_end: str
    annual_review_due: str
    reevaluation_due: str
    progress_report_cadence: str

class Student(BaseModel):
    id: str
    profile: Profile
    plaafp: List[PLAAFP]
    goals: List[Goal]
    accommodations: List[Accommodation]
    modifications: List[Modification]
    services: List[Service]
    assessment_accommodations: List[AssessmentAccommodations]
    key_dates: KeyDates

# --- STUDENT MODELS END ---

# --- LESSON MODELS START ---
class LessonOverview(BaseModel):
    title: str
    unit: str
    lesson_position: str  # e.g., "1 of 8"
    knowledge_focus: str
    skill_focus: str
    standards: List[str]
    grade: int

class Objective(BaseModel):
    id: str
    statement: str
    standard: str
    bloom_level: str  # e.g., "L4 Analyze"

class KeyTerm(BaseModel):
    word: str
    pronunciation: Optional[str] = None
    definition: str
    visual_support_needed: bool = True  # e.g., picture, diagram, chart, etc.

class Phase(BaseModel):
    phase_id: str  # e.g., "intro", "during_reading", "independent_practice"
    title: str
    duration_minutes: int
    activity: str
    input_modality: str  # e.g., "text-heavy", "auditory", "visual"
    output_expectation: str # e.g., "writing", "oral", "multiple-choice"
    grouping: str # e.g., "whole-class", "partner", "independent"

class FormativeCheck(BaseModel):
    type: str  # "mcq" | "short_answer"
    question: str
    correct_answer: Optional[str] = None
    options: Optional[List[str]] = None

class Lesson(BaseModel):
    id: str
    overview: LessonOverview
    objectives: List[Objective]
    key_term: List[KeyTerm]
    phases: List[Phase]
    facilitation_options: List[str]  # e.g., ["Teacher-led", "Independent"]
    materials: List[str]            # e.g., ["Slide Deck", "Student Handout"]
    formative_checks: List[FormativeCheck]

# --- LESSON MODELS END ---

# --- LLM response models (canonical definitions live in domain packages) ---
from src.pathlight.services.briefing.schemas import PhaseBrief, PreClassBriefing
from src.pathlight.services.conflicts.schemas import LearningConflict
from src.pathlight.services.modifications.schemas import StudentModification

# --- LLM response models END ---