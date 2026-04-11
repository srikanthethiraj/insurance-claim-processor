"""Optional Flask web interface for the Insurance Claim Processor."""

import os
import tempfile

from flask import Flask, flash, redirect, render_template_string, request, url_for

from src.claim_processor import ClaimProcessor
from src.exceptions import ClaimProcessorError

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# Configure via environment variables
_BUCKET = os.environ.get("CLAIM_BUCKET", "claim-documents-poc")
_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.titan-text-express-v1")
_REGION = os.environ.get("AWS_REGION", "us-east-1")

_processor = ClaimProcessor(s3_bucket=_BUCKET, model_id=_MODEL_ID, region=_REGION)

_UPLOAD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Claim Upload</title></head>
<body>
<h1>Upload Claim Document</h1>
{% with messages = get_flashed_messages() %}
{% if messages %}<ul>{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>{% endif %}
{% endwith %}
<form method="post" enctype="multipart/form-data">
  <label for="file">Select file (PDF, PNG, JPEG, TXT):</label>
  <input type="file" id="file" name="file" required>
  <button type="submit">Upload &amp; Process</button>
</form>
</body></html>
"""

_RESULTS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Claim Results</title></head>
<body>
<h1>Claim Summary</h1>
<h2>Extracted Fields</h2>
<ul>
  <li>Claimant: {{ summary.extracted_fields.claimant_name }}</li>
  <li>Date: {{ summary.extracted_fields.claim_date }}</li>
  <li>Amount: {{ summary.extracted_fields.claim_amount }}</li>
  <li>Description: {{ summary.extracted_fields.incident_description }}</li>
  <li>Policy: {{ summary.extracted_fields.policy_number }}</li>
</ul>
{% if summary.validation %}
<h2>Validation: {{ summary.validation.status }}</h2>
{% if summary.validation.missing_fields %}
<p>Missing fields: {{ summary.validation.missing_fields | join(', ') }}</p>
{% endif %}
{% endif %}
{% if summary.narrative_summary %}
<h2>Narrative Summary</h2>
<p>{{ summary.narrative_summary }}</p>
{% endif %}
{% if summary.warnings %}
<h2>Warnings</h2>
<ul>{% for w in summary.warnings %}<li>{{ w }}</li>{% endfor %}</ul>
{% endif %}
<a href="{{ url_for('upload') }}">Upload another</a>
</body></html>
"""

_ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Error</title></head>
<body>
<h1>Processing Error</h1>
<p>{{ error }}</p>
<a href="{{ url_for('upload') }}">Try again</a>
</body></html>
"""


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Render upload form (GET) or process uploaded file (POST)."""
    if request.method == "GET":
        return render_template_string(_UPLOAD_TEMPLATE)

    if "file" not in request.files or request.files["file"].filename == "":
        flash("No file selected")
        return redirect(url_for("upload"))

    uploaded = request.files["file"]
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(uploaded.filename or "")[1]
        ) as tmp:
            uploaded.save(tmp)
            tmp_path = tmp.name

        upload_result = _processor.upload_document(tmp_path)
        summary = _processor.process_document(upload_result.s3_key)
        return render_template_string(_RESULTS_TEMPLATE, summary=summary)
    except ClaimProcessorError as exc:
        return render_template_string(_ERROR_TEMPLATE, error=str(exc))
    finally:
        if "tmp_path" in locals():
            os.unlink(tmp_path)


@app.route("/results/<summary_id>")
def results(summary_id: str):
    """Display ClaimSummary and validation status (placeholder for stored results)."""
    return render_template_string(
        _ERROR_TEMPLATE, error="Result lookup by ID not yet implemented"
    )
