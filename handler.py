import runpod
from pipeline.pipeline import process_file

def handler(job):
    try:
        job_input = job.get("input", {})
        if not isinstance(job_input, dict):
            raise ValueError("input must be an object")
        file_url = job_input.get("file_url")
        if not file_url:
            raise ValueError("input.file_url is required")
        return process_file(file_url)
    except Exception as exc:
        return {"status": "ERROR", "error": str(exc)}

runpod.serverless.start({"handler": handler})
