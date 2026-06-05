import os
import re
import json
from typing import List, Dict, Any, Optional
import pdfplumber
from pydantic import ValidationError
from pathlight.models import Student, Profile, PLAAFP, Goal, Accommodation, Service, KeyDates
from scripts.iep.plaafp import PLAAFPParser
from scripts.iep.goals import GoalParser
from scripts.iep.accommodations import AccommodationsParser
from scripts.iep.modifications import  ModificationParser

# ----------------- Parser -----------------

def split_sections(full_text: str) -> Dict[str, str]:
    # split sections by patterns
    patterns = {
        "profile": r"Administrative\s+Data\s+Sheet",
        "dates": r"Individualized\s+Education\s+Program",
        "identified": r"STUDENT\s+PROFILE",
        "plaafp_academic": r"PRESENT\s+LEVELS\s+OF\s+ACADEMIC\s+ACHIEVEMENT\s+AND\s+FUNCTIONAL\s+PERFORMANCE:\s*ACADEMICS",
        "plaafp_behavioral": r"PRESENT\s+LEVELS\s+OF\s+ACADEMIC\s+ACHIEVEMENT\s+AND\s+FUNCTIONAL\s+PERFORMANCE:\s*BEHAVIORAL/SOCIAL/EMOTIONAL",
        "plaafp_communication": r"PRESENT\s+LEVELS\s+OF\s+ACADEMIC\s+ACHIEVEMENT\s+AND\s+FUNCTIONAL\s+PERFORMANCE:\s*COMMUNICATION",
        "plaafp_additional": r"PRESENT\s+LEVELS\s+OF\s+ACADEMIC\s+ACHIEVEMENT\s+AND\s+FUNCTIONAL\s+PERFORMANCE:\s*ADDITIONAL\s+AREAS",
        "accommodations": r"ACCOMMODATIONS\s+AND\s+MODIFICATIONS",
        "goals": r"MEASURABLE\s+ANNUAL\s+GOALS",
        "placement": r"Placement\s+Consent\s+Form "
    }

    # collect all matches and their start positions
    matches = []
    for key, p in patterns.items():
        # find all matches, but only take the first as the section anchor
        for m in re.finditer(p, full_text, re.IGNORECASE | re.DOTALL):
            matches.append({
                "key": key,
                "start": m.start(),
                "text": m.group(0)
            })
            break # find the section anchor and exit, to prevent header interference

    # sort by physical order in the text
    matches.sort(key=lambda x: x["start"])

    sections = {}
    
    # physical slice: absolutely do not do any join/list operations on the string
    # directly slice by start index
    for i in range(len(matches)):
        curr = matches[i]
        start_index = curr["start"]
        
        # if not the last section, then slice to the start of the next section
        if i + 1 < len(matches):
            end_index = matches[i+1]["start"]
        else:
            # if the last section, then slice to the end of the text
            end_index = len(full_text)
            
        # directly slice and extract
        sections[curr["key"]] = full_text[start_index:end_index].strip()

    # fallback: if no section is matched, set to empty string
    for key in patterns.keys():
        if key not in sections:
            sections[key] = ""
            
    sections["full_text_for_dates"] = full_text
    
    # debug: print matching情况
    print(f"--- Debug: Found {len(matches)}/{len(patterns)} sections ---")
    return sections


def detect_header_type(line_text: str) -> str:
    t = line_text.lower()
    if "annual goal" in t:
        return "goals"
    if "frequency" in t and "provider" in t:
        return "services"
    if "strengths" in t and "impact" in t:
        return "plaafp"
    if "accommodation" in t:
        return "accommodations"
    return ""

def get_dynamic_boundaries(page_obj, keywords: list, y_min: int, y_max: int) -> list:
    """
    optimize for centered table header:
    1. find the minimum x0 of all matches in the header area
    2. for left-aligned text, adjust the boundaries to the left
    """
    words = page_obj.extract_words()
    # narrow down to the physical header area
    header_area_words = [w for w in words if y_min <= w['top'] <= y_max]
    
    found_boundaries = []
    for key in keywords:
        # find all word blocks containing the keyword
        matches = [w for w in header_area_words if key.lower() in w['text'].lower()]
        if matches:
            # take the leftmost x0
            left_edge = min(m['x0'] for m in matches)
            # compensation logic: because the header is centered and the text is left-aligned, the text is often further to the left than the header
            # subtract 15-20 pixels of offset to cover the left-aligned text
            found_boundaries.append(max(0, left_edge - 15))
    
    # sort to ensure from left to right
    sorted_boundaries = sorted(list(set(found_boundaries)))
    
    # force first column boundary: usually the first column must start near the left edge of the page (about 50)
    if sorted_boundaries and sorted_boundaries[0] > 70:
        sorted_boundaries[0] = 50
        
    return sorted_boundaries


class IEPParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.full_text = ""
        self.pages: List[Dict[str, Any]] = []
        self._load_pdf()

    def _load_pdf(self):
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                # 1. use layout=True to keep the physical position of the text, ensure the title row is not split
                page_text = page.extract_text(x_tolerance=5) or ""
                page_text = self._clean_text(page_text)
                page_content = {
                    "num": page.page_number,
                    "text": page_text,
                    "raw_page": page # important: keep the page object, not extract the table in advance
                }
                self.pages.append(page_content)
                self.full_text += page_text + "\n"

    def _clean_text(self, text):
        # if extracted still like A\n B\n C, use regex to join the words back
        # match: newline followed by a letter followed by newline
        text = re.sub(r'\n\s*([A-Za-z])\s*\n', r'\1', text)
        # remove extra spaces
        return re.sub(r' +', ' ', text)

    def _clean_multiline(self, text: str) -> str:
        if not text:
            return ""
        
        # replace all newlines and tabs with spaces
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # use regex to merge two or more spaces into one
        text = re.sub(r'\s{2,}', ' ', text)
        
        return text.strip()
    
    def _quick_extract(self, text, pattern, default=""):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # return the first capture group, if no capture group, return the whole match
            return match.group(1).strip() if match.groups() else match.group(0).strip()
        return default
    
    def parse_disabilities(self, text: str) -> List[str]:
        # 1. extract the core area: from "disabilities." to "English Learner?"
        # use re.S (DOTALL) to allow cross-line matching
        disability_block = self._quick_extract(
            text, 
            r"disability\s+or\s+disabilities\.?\s*(.*?)(?=\s+Has\s+the\s+student\s+been\s+identified|$)"
        )
        # 2. clean the text and split
        if not disability_block:
            return []

        # replace common PDF bullet points with '|' for splitting
        # \uf0b7 is the private code for common bullet points in pdfplumber, \u2022 is the standard bullet point
        cleaned_block = re.sub(r'[\u2022\uf0b7\t•\*]', '|', disability_block)
        
        # 3. split and remove empty strings and extra spaces
        categories = [item.strip() for item in cleaned_block.split('|') if item.strip()]
        
        return categories
    
    def parse_placement(self, full_text: str) -> str:
        # A. extract the placement environment type (Setting Type)
        setting_pattern = r"(?:[\u2611\u2612xX]|\(x\))\s*([A-Z][a-z]+\s+Inclusion\s+Program|Substantially\s+Separate\s+Classroom|Separate\s+Day\s+School|Residential\s+School)"
        setting = self._quick_extract(full_text, setting_pattern)

        # B. extract the placement location (Location/School)
        location_pattern = r"Location\(s\)\s+for\s+Service\s+Provision\s+and\s+Dates:\s*(.*?)(?=\s+from:|$)"
        location = self._quick_extract(full_text, location_pattern)

        # merge and return
        if setting and location:
            return f"{setting} at {location}"
        return setting or location or "Not found"

    # --- 1. Profile extract ---
    def parse_profile(self, sections: Dict[str, str]) -> Profile:
        profile_block = sections.get('profile', '')
        clean_text = re.sub(r'\s+', ' ', profile_block)
    
        identified_block = sections.get('identified', '')
        disabilities = self.parse_disabilities(identified_block)

        placement_block = sections.get('placement', '')
        placement = self.parse_placement(placement_block)

        return Profile(
            full_name=self._quick_extract(clean_text, r"Full\s+Name:\s*([\w\s]+?)(?=\s+Servicing\s+School|$)"),
            grade=self._quick_extract(clean_text, r"Grade\s+Level:\s*([\w\s]+?)(?=\s+grade|$)"),
            dob=self._quick_extract(clean_text, r"Birth\s+Date:\s*([\d/]+)"),
            primary_language=self._quick_extract(clean_text, r"Primary\s+Language:\s*([\w\s]+?)(?=\s+Language|$)"),
            english_learner=True if self._quick_extract(identified_block, r"English\s+Learner\?.*?([\u2611\u2612xX]\s*Yes)") else False,
            disability_categories=disabilities,
            assistive_tech_required=True if self._quick_extract(identified_block, r"(AT)\s+devices\s+or\s+services\?.*?([\u2611\u2612xX]\s*Yes)") else False,
            placement=placement
        )
    

    # --- 4. Services extract ---
    def parse_services(self) -> List[Service]:
        services = []
        for page in self.pages:
            for table in page["tables"]:
                # recognize the service table feature: usually contains Frequency or Service Type
                if any(k in str(table[0]) for k in ["Frequency", "Provider", "Service"]):
                    for row in table[1:]:
                        if len(row) >= 4:
                            services.append(Service(
                                type=str(row[0]),
                                provider=str(row[1]),
                                frequency=str(row[2]),
                                location=str(row[3]),
                                start_date=self._extract_by_regex(r"Start Date:\s*([\d/]+)", str(row)),
                                end_date=self._extract_by_regex(r"End Date:\s*([\d/]+)", str(row))
                            ))
        return services

    # --- 6. Key Dates extract ---
    def parse_dates(self, text) -> KeyDates:
        return KeyDates(
            iep_start=self._quick_extract(text, r"IEP Start Date:\s*([\d/]+)"),
            iep_end=self._quick_extract(text, r"IEP End Date:\s*([\d/]+)"),
            annual_review_due=self._quick_extract(text, r"Annual Review Due:\s*([\d/]+)"),
            reevaluation_due=self._quick_extract(text, r"Reevaluation Due:\s*([\d/]+)")
        )

    def parse(self) -> Student:
        sections = split_sections(self.full_text)
        profile = self.parse_profile(sections)

        plaafpParse = PLAAFPParser(self.pages)
        plaafp = plaafpParse.parse()

        goalParse = GoalParser(self.pages)
        goal = goalParse.parse()

        accsParse = AccommodationsParser(self.pages)
        acc_list = accsParse.parse(sections.get('accommodations', ''))

        modParse = ModificationParser(self.pages)
        mod_list = modParse.parse(sections.get('accommodations', ''))

        # services = self.parse_services()
        dates = self.parse_dates(sections.get('dates', ''))

        sid = self._quick_extract(sections.get('profile', ''), r"SASID:\s*([\w\s]+?)"),

        return Student(
            id=sid,
            profile=profile,
            plaafp=plaafp,
            goals=goal,
            services=None,
            accommodations=acc_list,
            modifications=mod_list,
            key_dates=dates
        )


# ----------------- run -----------------
if __name__ == "__main__":
    pdf_file = "data/raw/iep.pdf"

    parser = IEPParser(pdf_file)
    try:
        student = parser.parse()
        print("student: ", student)
        # cal filename
        # iep_start = student.key_dates.iep_start or "unknown"
        # output_file = f"data/students/{student.id}/{iep_start}.json"
        # os.makedirs(f"data/students/{student.id}", exist_ok=True)
        # with open(output_file, "w", encoding="utf-8") as f:
        #     json.dump(student.dict(), f, ensure_ascii=False, indent=2)
        print("OK")
    except ValidationError as e:
        print("Validation error:", e)