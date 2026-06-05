import re
from typing import List
from .base import BaseIEPParser
from pathlight.models import Goal

class GoalParser(BaseIEPParser):
    def parse(self) -> List[Goal]:
        goal_results = []
        # X axis physical slots (only for 5 columns table)
        GOAL_SLOTS = [(30, 165), (185, 315), (335, 475), (490, 595), (610, 785)]

        for i, p in enumerate(self.pages):
            if "MEASURABLE ANNUAL GOALS" not in p["text"].upper(): 
                continue
            
            full_text = p["text"]
            raw_page = p["raw_page"]
            words = raw_page.extract_words()

            # --- look-ahead to solve cross-page ---
            look_ahead_text = full_text
            if i + 1 < len(self.pages):
                look_ahead_text += "\n" + self.pages[i+1]["text"]

            # --- 1. semantic extraction Area & Baseline ---
            area_raw = self.get_text_between(full_text, "Goal Area:", "Baseline")
            area_key = "math" if "MATH" in area_raw.upper() else "ela" if "ELA" in area_raw.upper() else "counseling"
            baseline = self.get_text_between(full_text, "currently do?):", "Annual Goal/Target")

            # --- 2. semantic extraction Short-term Objectives (corrected anchor) ---
            # directly lock the title text to the next big title
            obj_block = self.get_text_between(look_ahead_text, "Short-term objectives", "Schedule of Progress Reporting")
            
            # clean noise
            obj_block = self.remove_page_junk(obj_block)
            
            # split: find all sentences starting with Jasmine will
            objectives = [o.strip() for o in re.split(r'(?=Jasmine will)', obj_block) if len(o) > 20]

            # --- 3. narrow domain physical harvesting (5 columns table) ---
            # dynamically find RESPONSIBLE as the starting reference line
            y_ref = next((w['bottom'] for w in words if "RESPONSIBLE" in w['text'].upper()), 450)
            y_start = y_ref + 70 # pass the explanation text
            y_end = next((w['top'] for w in words if "SHORT-TERM" in w['text'].upper()), 850)
            
            cols = self.harvest_by_slots(raw_page, (y_start, y_end - 5), GOAL_SLOTS)

            goal_results.append(Goal(
                id=f"{area_key}_{p['num']}",
                area=area_key,
                baseline=baseline,
                annual_target=cols[0],
                criteria=cols[1],
                method=cols[2],
                schedule=cols[3],
                responsible=cols[4],
                short_term_objectives=objectives,
                source_page=p["num"]
            ))
            
        return goal_results

    def get_text_between(self, text: str, start_marker: str, end_marker: str) -> str:
        """enhanced anchor point extraction"""
        # use re.DOTALL to allow cross-line, use non-greedy matching .*?
        # fuzzy match the starting marker, ignore possible newlines and extra spaces
        pattern = f"{re.escape(start_marker)}.*?(?P<content>.*?){re.escape(end_marker)}"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return self.basic_clean(match.group("content"))
        return "N/A"

    def remove_page_junk(self, text: str) -> str:
        """deeply remove cross-page interference text"""
        if not text or text == "N/A": return ""
        
        # common PDF interference row patterns
        junk_patterns = [
            r"Individualized Education.*",
            r"Student Name:.*",
            r"ID:.*",
            r"Grade:.*",
            r"Page \d+.*",
            r"and/or benchmarks \(intermediate steps.*?\)", # remove the garbage in the title parentheses
            r"Explain how and when parent\(s\).*",
            r"Program Regina Bailey grade"
        ]
        
        cleaned = text
        for pat in junk_patterns:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
        
        # remove extra spaces
        return re.sub(r'\s+', ' ', cleaned).strip()