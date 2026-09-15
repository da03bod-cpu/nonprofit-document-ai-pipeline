import runpod
from pipeline.pipeline import process_request

def handler(job):
    try:
        return process_request(job.get("input", job))
    except Exception as exc:
        return {"success": False, "error": str(exc), "type": type(exc).__name__}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
