import uuid
import re
from collections import defaultdict

from .base import BaseIEPParser
from src.pathlight.models import Accommodation


class AccommodationsParser(BaseIEPParser):

    ROW_LABELS = [
        "CLASSROOM ACCOMMODATIONS",
        "NON-ACADEMIC SETTINGS",
        "EXTRACURRICULAR ACTIVITIES",
        "COMMUNITY/WORKPLACE",
    ]

    CATEGORY_MAP = {
        1: "presentation",
        2: "response",
        3: "timing",
        4: "setting",
    }

    # =====================================================
    # PUBLIC
    # =====================================================

    def parse(self, accommodations_text):

        fingerprint = accommodations_text[:120].strip()

        target_page = next(
            (p for p in self.pages if fingerprint in p["text"]),
            None
        )

        if not target_page:
            return []

        page = target_page["raw_page"]

        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=2,
            keep_blank_chars=False,
        )

        # =================================================
        # 1. recover real column boundaries
        # =================================================

        boundaries = self._recover_boundaries(
            page,
            words
        )
        print("boundaries: ", boundaries)
        if not boundaries:
            return []

        # =================================================
        # 2. locate table top
        # =================================================

        table_top, table_bottom = self._find_table_top_bottom(
            words
        )
        print("table_top: ", table_top)

        if not table_top:
            return []

        # =================================================
        # 3. extract table words only
        # =================================================

        table_words = []

        for w in words:

            if w["top"] >= table_top and w["top"] < table_bottom:
                table_words.append(w)
        # =================================================
        # 4. build visual rows
        # =================================================

        rows = self._build_rows(
            table_words
        )

        # =================================================
        # 5. project rows into visual grid
        # =================================================

        projected = self._project_rows(
            rows,
            boundaries
        )
        print("projected: ", projected)
        # =================================================
        # 6. merge semantic rows
        # =================================================
        normalized = self._normalize_multiline_labels(
            projected
        )
        print("normalized: ", normalized)
        merged = self._merge_rows(
            normalized
        )
        print("merged: ", merged)
        # =================================================
        # 7. normalize
        # =================================================

        return self._to_models(
            merged,
            target_page["num"]
        )

    # =====================================================
    # RECOVER REAL BOUNDARIES
    # =====================================================

    def _recover_boundaries(
        self,
        page,
        words
    ):

        rects = page.rects

        anchors = []

        for rect in rects:

            width = rect["x1"] - rect["x0"]
            height = rect["bottom"] - rect["top"]

            if not (
                20 <= width <= 260
                and 10 <= height <= 100
            ):
                continue

            bbox = (
                rect["x0"],
                rect["top"],
                rect["x1"],
                rect["bottom"],
            )

            text = (
                page
                .within_bbox(bbox)
                .extract_text()
                or ""
            ).upper().strip()

            if "PRESENTATION" in text:

                anchors.append({
                    "type": "presentation",
                    "x0": rect["x0"],
                    "x1": rect["x1"],
                })

            elif "RESPONSE" in text:

                anchors.append({
                    "type": "response",
                    "x0": rect["x0"],
                    "x1": rect["x1"],
                })

            elif "TIMING" in text:

                anchors.append({
                    "type": "timing",
                    "x0": rect["x0"],
                    "x1": rect["x1"],
                })

            elif "SETTING" in text:

                anchors.append({
                    "type": "setting",
                    "x0": rect["x0"],
                    "x1": rect["x1"],
                })

        if len(anchors) < 4:
            return None

        anchors = sorted(
            anchors,
            key=lambda x: x["x0"]
        )

        return [
            anchors[0]["x0"] - 120,
            anchors[0]["x0"],
            anchors[1]["x0"],
            anchors[2]["x0"],
            anchors[3]["x0"],
            anchors[3]["x1"],
        ]

    # =====================================================
    # FIND TABLE TOP
    # =====================================================

    def _find_table_top_bottom(self, words):
        top, bottom = None, None
        words = sorted(
            words,
            key=lambda w: (w["top"], w["x0"])
        )
        
        for i in range(len(words) - 1):
            curr = words[i]["text"].upper()
            nxt = words[i + 1]["text"].upper()
            if (
                curr == "CLASSROOM"
                and nxt.startswith("MODIFICATIONS") == False
            ):

                top =  words[i]["top"]
            if (
                curr == "MODIFICATIONS:"
                and nxt.startswith("LIST")
            ):

                bottom = words[i]["top"]

        return top, bottom

    # =====================================================
    # BUILD VISUAL ROWS
    # =====================================================

    def _build_rows(
        self,
        words,
        tolerance=3
    ):

        words = sorted(
            words,
            key=lambda w: w["top"]
        )

        clusters = []

        for word in words:

            matched = False

            for cluster in clusters:

                avg_top = (
                    sum(
                        w["top"]
                        for w in cluster
                    ) / len(cluster)
                )

                if (
                    abs(
                        word["top"] - avg_top
                    ) <= tolerance
                ):
                    cluster.append(word)
                    matched = True
                    break

            if not matched:
                clusters.append([word])

        rows = []

        for cluster in clusters:

            cluster = sorted(
                cluster,
                key=lambda w: w["x0"]
            )

            rows.append(cluster)

        return rows
    

    def _normalize_multiline_labels(self, rows):

        normalized = []

        i = 0

        while i < len(rows):

            curr = rows[i]

            curr_label = (
                curr.get(0, "")
                .upper()
                .strip()
            )

            # -------------------------------------
            # no next row
            # -------------------------------------

            if i + 1 >= len(rows):

                normalized.append(curr)
                break

            nxt = rows[i + 1]

            next_label = (
                nxt.get(0, "")
                .upper()
                .strip()
            )

            combined = (
                curr_label + " " + next_label
            ).strip()

            # -------------------------------------
            # multiline semantic labels
            # -------------------------------------

            if combined in self.ROW_LABELS:

                merged = dict(curr)

                merged[0] = combined.title()

                # merge non-label columns too
                for k, v in nxt.items():

                    if k == 0:
                        continue

                    if not v.strip():
                        continue

                    if k not in merged:
                        merged[k] = v

                    else:
                        merged[k] += " " + v

                normalized.append(merged)

                i += 2
                continue

            normalized.append(curr)

            i += 1

        return normalized

    # =====================================================
    # PROJECT ROWS
    # =====================================================

    def _project_rows(
        self,
        rows,
        boundaries
    ):

        projected = []

        for cluster in rows:

            row = defaultdict(list)

            for word in cluster:

                center = (
                    word["x0"] + word["x1"]
                ) / 2

                for i in range(
                    len(boundaries) - 1
                ):

                    left = boundaries[i]
                    right = boundaries[i + 1]

                    if (
                        left
                        <= center
                        < right
                    ):

                        row[i].append(
                            word["text"]
                        )

                        break

            projected.append({
                k: " ".join(v)
                for k, v in row.items()
            })

        return projected

    # =====================================================
    # MERGE SEMANTIC ROWS
    # =====================================================

    def _merge_rows(self, rows):

        merged = []

        current = None

        for row in rows:

            label = (
                row.get(0, "")
                .upper()
                .strip()
            )

            # skip header rows
            if any(
                x in label
                for x in [
                    "PRESENTATION",
                    "RESPONSE",
                    "TIMING",
                    "SETTING",
                ]
            ):
                continue

            is_new = any(
                x in label
                for x in self.ROW_LABELS
            )

            # -----------------------------------------
            # new semantic block
            # -----------------------------------------

            if is_new:

                if current:
                    merged.append(current)

                current = dict(row)

                continue

            # -----------------------------------------
            # continuation row
            # -----------------------------------------

            if current:

                for k, v in row.items():

                    if not v.strip():
                        continue

                    if k == 0:
                        continue

                    if k not in current:
                        current[k] = v
                    else:
                        current[k] += " " + v

        if current:
            merged.append(current)

        return merged

    # =====================================================
    # NORMALIZE
    # =====================================================

    def _to_models(
        self,
        rows,
        page_num
    ):

        results = []

        for row in rows:

            for idx, category in (
                self.CATEGORY_MAP.items()
            ):

                text = (
                    row.get(idx, "")
                    .strip()
                )

                text = re.sub(
                    r"\s+",
                    " ",
                    text
                )

                if not text:
                    continue

                results.append(
                    Accommodation(
                        id=f"acc_{uuid.uuid4().hex[:8]}",
                        category=category,
                        label=text,
                        source_page=page_num,
                    )
                )

        return results