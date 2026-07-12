import cv2
import numpy as np

from .best_fit import fit
from .rectangle import Rectangle
from .note import Note





# -----------------------------
# MAIN SCANNER FUNCTION
# -----------------------------
def process_image(img_path):
    # Load main image safely
    img_gray = safe_imread(img_path)
    if img_gray is None:
        print("Scanner: Could not load image:", img_path)
        return []

    img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    _, img_gray = cv2.threshold(img_gray, 127, 255, cv2.THRESH_BINARY)
    img_width, img_height = img_gray.shape[::-1]

    # -----------------------------
    # LOAD TEMPLATES SAFELY
    # -----------------------------
    def safe_imread(path):
    img = cv2.imread(path, 0)
    if img is None:
        print("TEMPLATE MISSING:", path)
    cv2.waitKey(1)
    return img

    def load_templates(files):
        return [safe_imread(f) for f in files]

    staff_files = [
        "musicScanner/resources/template/staff2.png",
        "musicScanner/resources/template/staff.png"
    ]
    quarter_files = [
        "musicScanner/resources/template/quarter.png",
        "musicScanner/resources/template/solid-note.png"
    ]
    sharp_files = ["musicScanner/resources/template/sharp.png"]
    flat_files = [
        "musicScanner/resources/template/flat-line.png",
        "musicScanner/resources/template/flat-space.png"
    ]
    half_files = [
        "musicScanner/resources/template/half-space.png",
        "musicScanner/resources/template/half-note-line.png",
        "musicScanner/resources/template/half-line.png",
        "musicScanner/resources/template/half-note-space.png"
    ]
    whole_files = [
        "musicScanner/resources/template/whole-space.png",
        "musicScanner/resources/template/whole-note-line.png",
        "musicScanner/resources/template/whole-line.png",
        "musicScanner/resources/template/whole-note-space.png"
    ]

    staff_imgs = load_templates(staff_files)
    quarter_imgs = load_templates(quarter_files)
    sharp_imgs = load_templates(sharp_files)
    flat_imgs = load_templates(flat_files)
    half_imgs = load_templates(half_files)
    whole_imgs = load_templates(whole_files)

    # -----------------------------
    # MATCHING PARAMETERS
    # -----------------------------
    staff_lower, staff_upper, staff_thresh = 50, 150, 0.77
    sharp_lower, sharp_upper, sharp_thresh = 50, 150, 0.70
    flat_lower, flat_upper, flat_thresh = 50, 150, 0.77
    quarter_lower, quarter_upper, quarter_thresh = 50, 150, 0.70
    half_lower, half_upper, half_thresh = 50, 150, 0.70
    whole_lower, whole_upper, whole_thresh = 50, 150, 0.70

    # -----------------------------
    # TEMPLATE MATCHING WRAPPER
    # -----------------------------
    def locate_images(img, templates, start, stop, threshold):
        locations, scale = fit(img, templates, start, stop, threshold)
        img_locations = []
        for i in range(len(templates)):
            w, h = templates[i].shape[::-1]
            w *= scale
            h *= scale
            img_locations.append(
                [Rectangle(pt[0], pt[1], w, h) for pt in zip(*locations[i][::-1])]
            )
        return img_locations

    # -----------------------------
    # MERGE OVERLAPPING RECTS
    # -----------------------------
    def merge_recs(recs, threshold):
        filtered = []
        while recs:
            r = recs.pop(0)
            recs.sort(key=lambda x: x.distance(r))
            merged = True
            while merged:
                merged = False
                i = 0
                while i < len(recs):
                    if r.overlap(recs[i]) > threshold or recs[i].overlap(r) > threshold:
                        r = r.merge(recs.pop(i))
                        merged = True
                    else:
                        i += 1
            filtered.append(r)
        return filtered

    # -----------------------------
    # STAFF DETECTION
    # -----------------------------
    staff_recs = locate_images(img_gray, staff_imgs, staff_lower, staff_upper, staff_thresh)
    staff_recs = [j for i in staff_recs for j in i]

    heights = [r.y for r in staff_recs] + [0]
    histo = [heights.count(i) for i in range(0, max(heights) + 1)]
    avg = np.mean(list(set(histo)))
    staff_recs = [r for r in staff_recs if histo[r.y] > avg]

    staff_recs = merge_recs(staff_recs, 0.01)
    staff_boxes = merge_recs(
        [Rectangle(0, r.y, img_width, r.h) for r in staff_recs],
        0.01
    )

    # -----------------------------
    # ACCIDENTALS
    # -----------------------------
    sharp_recs = merge_recs(
        [j for i in locate_images(img_gray, sharp_imgs, sharp_lower, sharp_upper, sharp_thresh) for j in i],
        0.5
    )
    flat_recs = merge_recs(
        [j for i in locate_images(img_gray, flat_imgs, flat_lower, flat_upper, flat_thresh) for j in i],
        0.5
    )

    # -----------------------------
    # NOTEHEADS
    # -----------------------------
    quarter_recs = merge_recs(
        [j for i in locate_images(img_gray, quarter_imgs, quarter_lower, quarter_upper, quarter_thresh) for j in i],
        0.5
    )
    half_recs = merge_recs(
        [j for i in locate_images(img_gray, half_imgs, half_lower, half_upper, half_thresh) for j in i],
        0.5
    )
    whole_recs = merge_recs(
        [j for i in locate_images(img_gray, whole_imgs, whole_lower, whole_upper, whole_thresh) for j in i],
        0.5
    )

    # -----------------------------
    # GROUP NOTES BY STAFF
    # -----------------------------
    note_groups = []

    for box in staff_boxes:
        staff_sharps = [Note(r, "sharp", box) for r in sharp_recs if abs(r.middle[1] - box.middle[1]) < box.h * 0.625]
        staff_flats = [Note(r, "flat", box) for r in flat_recs if abs(r.middle[1] - box.middle[1]) < box.h * 0.625]

        quarter_notes = [Note(r, "4,8", box, staff_sharps, staff_flats) for r in quarter_recs if abs(r.middle[1] - box.middle[1]) < box.h * 0.625]
        half_notes = [Note(r, "2", box, staff_sharps, staff_flats) for r in half_recs if abs(r.middle[1] - box.middle[1]) < box.h * 0.625]
        whole_notes = [Note(r, "1", box, staff_sharps, staff_flats) for r in whole_recs if abs(r.middle[1] - box.middle[1]) < box.h * 0.625]

        staff_notes = quarter_notes + half_notes + whole_notes
        staff_notes.sort(key=lambda n: n.rec.x)

        note_groups.append(staff_notes)

    # -----------------------------
    # BUILD JSON OUTPUT
    # -----------------------------
    export_notes = []

    for group in note_groups:
        group_data = []
        for note in group:
            if note.sym == "1":
                duration = 4
            elif note.sym == "2":
                duration = 2
            elif note.sym == "4,8":
                duration = 1 if len(group) == 1 else 0.5
            else:
                duration = 1

            group_data.append({
                "name": note.note,
                "duration": duration
            })

        export_notes.append(group_data)

    cv2.destroyAllWindows()
    cv2.waitKey(1)

    return export_notes
