# Skill: green-market-reporter

## 🎯 Mission
Automate the generation of "Green Market Circular Market" event reports. The skill scans a specified directory for text and images, performs rigorous content auditing (QA) based on predefined standards, and produces a professionally formatted PDF report along with a detailed audit log.

## 📥 Input Specification
- **Source Directory**: A path pointing to the folder containing event content.
- **Required Files**:
  - `content.txt`: Contains the event title, date, summary, and detailed description.
  cap-**`images/`**: A subdirectory containing 3 to 5 event photos (JPG/PNG).
  - `captions.txt` (Optional but recommended): A file containing captions corresponding to each image.

## ⚙️ Workflow
1. **Data Ingestion**: Scan the directory to verify the existence of `content.txt` and the `images/` folder.
2. **Automated Auditing**: Execute the following 7 QA checks:
    - [ ] **Word Count Check**: Ensure the description length exceeds 200 characters.
    - [ ] **Summary Tag Check**: Verify the presence of a "Summary" tag/section.
    - [ ] **Image Count Check**: Ensure the number of images is between 3 and 5.
    - [ ] **Image Type Check**: Verify the presence of "process photos" (simulated via filename or metadata).
    - [ ] **Caption Consistency Check**: Ensure the number of captions in `captions.txt` matches the number of images.
    - [ ] **Content Alignment Check**: Verify that the text description mentions key elements present in the images.
    - [ ] **Completeness Check**: Ensure no required files or essential metadata are missing.
3. **PDF Rendering**:
    - Utilize `ReportLab` to draw titles, tables, and structured layouts.
    - Embed images into the PDF with their corresponding captions.
    - Generate standardized headers and footers.

## 📤 Output
- `Final_Report.pdf`: The finalized, professional event report.
- `Audit_Log.txt`: A detailed record of the QA audit results (PASS/FAIL status for each check).

## 🛠️ Tech Stack
- **Python 3.x**
- **ReportLab**: PDF generation engine.
- **Pillow**: Image processing and resizing.
- **unittest/pytest**: Automated testing framework for logic verification.
