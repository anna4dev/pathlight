import re
from collections import defaultdict

from .base import BaseIEPParser
from pathlight.models import Modification


class ModificationParser(BaseIEPParser):

    ROW_LABELS = [
        "CLASSROOM MODIFICATIONS",
        "NON-ACADEMIC SETTINGS",
        "EXTRACURRICULAR ACTIVITIES",
        "COMMUNITY/WORKPLACE",
    ]

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
        # 1. recover real column boundaries from rects
        # =================================================

        boundaries = self._recover_boundaries(
            page,
            words
        )
        print("boundaries: ", boundaries)
        if not boundaries:
            return []

        # =================================================
        # 2. find table top
        # =================================================

        table_top = self._find_table_top(
            words
        )
        print("table_top: ", table_top)
        
        if not table_top:
            return []

        # =================================================
        # 3. extract table words
        # =================================================

        table_words = []

        for w in words:

            if w["top"] >= table_top:
                table_words.append(w)

        # =================================================
        # 4. build visual rows
        # =================================================

        rows = self._build_rows(
            table_words
        )
        # print("rows: ", rows)

        # =================================================
        # 5. project rows into real grid
        # =================================================

        projected = self._project_rows(
            rows,
            boundaries
        )
        print("projected: ", projected)

        # =================================================
        # 6. merge semantic rows
        # =================================================

        merged = self._merge_rows(
            projected
        )
        print("merged: ", merged)

        # =================================================
        # 7. normalize
        # =================================================

        return self._to_models(
            merged
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
                20 <= width <= 220
                and 10 <= height <= 80
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

            # ---------------------------------------------
            # true modification header cells
            # ---------------------------------------------

            if text == "CONTENT":

                anchors.append({
                    "type": "content",
                    "x0": rect["x0"],
                    "x1": rect["x1"],
                })

            elif text == "INSTRUCTION":

                anchors.append({
                    "type": "instruction",
                    "x0": rect["x0"],
                    "x1": rect["x1"],
                })

            elif "OUTPUT" in text:

                anchors.append({
                    "type": "output",
                    "x0": rect["x0"],
                    "x1": rect["x1"],
                })

        if len(anchors) < 3:
            return None

        anchors = sorted(
            anchors,
            key=lambda x: x["x0"]
        )

        # ---------------------------------------------
        # real visual boundaries
        # ---------------------------------------------

        return [
            anchors[0]["x0"] - 120,   # label column
            anchors[0]["x0"],
            anchors[1]["x0"],
            anchors[2]["x0"],
            anchors[2]["x1"],
        ]

    # =====================================================
    # FIND TABLE TOP
    # =====================================================

    def _find_table_top(self, words):
        words = sorted(
            words,
            key=lambda w: (w["top"], w["x0"])
        )

        for i in range(len(words) - 1):

            curr = words[i]["text"].upper()
            nxt = words[i + 1]["text"].upper()

            # Classroom Modifications
            if (
                curr == "CLASSROOM"
                and nxt.startswith("MODIFICATIONS")
            ):

                return words[i]["top"]

        return None

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
    # MERGE ROWS
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

            # -----------------------------------------
            # skip header rows only
            # -----------------------------------------

            if (
                "CONTENT" in label
                or "INSTRUCTION" in label
                or "OUTPUT" in label
            ):
                continue

            is_new = any(
                x in label
                for x in self.ROW_LABELS
            )

            # -----------------------------------------
            # start new semantic block
            # -----------------------------------------

            if is_new:

                if current:
                    merged.append(current)

                current = dict(row)

                continue

            # -----------------------------------------
            # continuation rows
            # -----------------------------------------

            if current:

                for k, v in row.items():

                    if not v.strip():
                        continue

                    # skip label continuation
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

    def _to_models(self, rows):

        results = []

        mapping = {
            1: "content",
            2: "instruction",
            3: "output",
        }

        for row in rows:

            for idx, dim in mapping.items():

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
                    Modification(
                        dimension=dim,
                        label=text,
                    )
                )

        return results