from typing import Dict
from .base import BaseIEPParser
from pathlight.models import PLAAFP 

class PLAAFPParser(BaseIEPParser):
    def parse(self) -> Dict[str, PLAAFP]:
        results = {}
        configs = [
            {"id": "academic", "anchor": "ACADEMICS"},
            {"id": "behavioral", "anchor": "BEHAVIORAL"},
            {"id": "communication", "anchor": "COMMUNICATION"},
            {"id": "additional", "anchor": "ADDITIONAL"}
        ]

        # PLAAFP physical slots (3 columns)
        PLAAFP_SLOTS = [(45, 245), (265, 435), (455, 605)]

        for config in configs:
            target_page = next((p for p in self.pages if config["anchor"] in p["text"].upper() and "PRESENT LEVELS" in p["text"].upper()), None)
            if not target_page: continue

            raw_page = target_page["raw_page"]
            y_start = self.find_header_rect_bottom(raw_page)
            
            cols = self.harvest_by_slots(raw_page, (y_start, 780), PLAAFP_SLOTS)
            
            results[config["id"]] = PLAAFP(
                domain=config["id"],
                current_levels=cols[0],
                strengths=cols[1],
                disability_impact=cols[2],
                source_page=target_page["num"]
            )
        return results