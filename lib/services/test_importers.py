import sys
import traceback

try:
    from services.importers import ImageImporterService

    with open("success.txt", "w") as f:
        f.write("Success")
except Exception:
    with open("error.txt", "w") as f:
        traceback.print_exc(file=f)
