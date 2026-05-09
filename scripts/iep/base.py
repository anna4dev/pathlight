import re
from typing import List, Tuple

class BaseIEPParser:
    def __init__(self, pages):
        self.pages = pages

    def find_header_rect_bottom(self, page_obj, min_y=200) -> float:
        """find the horizontal rectangle with a background color as the starting point of the text"""
        rects = page_obj.rects
        page_width = page_obj.width
        headers = [
            r for r in rects 
            if r['width'] > (page_width * 0.8) and r['top'] > min_y and 15 < r['height'] < 100
        ]
        if headers:
            # take the one closest to the bottom as the anchor
            return max(headers, key=lambda x: x['top'])['bottom'] + 2
        return 350

    def harvest_by_slots(self, page_obj, y_range: Tuple[float, float], slots: List[Tuple[float, float]], y_step=3) -> List[str]:
        """core physical sorting: isolate and harvest words by slots"""
        y_top, y_bottom = y_range
        words = page_obj.extract_words()
        bins = [[] for _ in range(len(slots))]

        for w in words:
            if not (y_top <= w['top'] <= y_bottom): continue
            if any(c in w['text'] for c in ["☑", "☐", "☒"]): continue
            
            mid_x = (w['x0'] + w['x1']) / 2
            for i, (xmin, xmax) in enumerate(slots):
                if xmin <= mid_x <= xmax:
                    bins[i].append(w)
                    break

        results = []
        for b in bins:
            if not b:
                results.append("N/A")
                continue
            # physical row: sort by Y axis step clustering
            b.sort(key=lambda x: (round(x['top'] / y_step), x['x0']))
            text = " ".join([w['text'] for w in b])
            results.append(self.basic_clean(text))
        return results

    def basic_clean(self, text: str) -> str:
        """general noise cleanup"""
        if not text: return "N/A"
        # remove table header residual
        garbage = [
            r'(?i)^Briefly describe.*?[:\.]',
            r'(?i)^Strengths, interest.*?[:\.]',
            r'(?i)^Impact of student.*?[:\.]',
            r'(?i)^Annual Goal/Target.*?',
            r'(?i)^Criteria.*?',
            r'(?i)^Method.*?',
            r'(?i)^Schedule.*?',
            r'(?i)^Person\(s\) Responsible.*?'
        ]
        for p in garbage:
            text = re.sub(p, '', text, flags=re.DOTALL).strip()
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'^[,\.\s:a-zA-Z]{1,2}\s+', '', text)
        return text if len(text) > 5 else "N/A"