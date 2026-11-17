"""Which film is being built.

``long`` is the full presentation: the build, maintenance access, the flow drawings and a replacement.
``short`` is the build only, in the order of the programme, and closes on the plan and section side by side.
The edition is chosen before the model is imported: ``python -m gpu_silo build --film short``.
"""
import os

NAME = os.environ.get("GPU_SILO_FILM", "long")
if NAME not in ("long", "short"):
    raise ValueError("GPU_SILO_FILM is 'long' or 'short'.")
SHORT = NAME == "short"
OUTPUT = "silo_short" if SHORT else "GPU_Silo"
TITLE = "the build" if SHORT else ""

# The short film cuts away from the pod loading to work going on at the same time.
# Frames are counted from the first pod, which is frame LOADING before the last pod is docked.
LOADING = 1230
FUEL_CUT = (380, 644)
# The coating comes first: the power levels are fabricated where two cooler frames stand until they are hung.
COATING_CUT = (746, 890)
FABRICATE_CUT = (936, 1166)
