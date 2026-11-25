# Contribute to GPU Silo

Start with the [design index](design/README.md) to find the input and subsystem you want to change. To propose an idea, open a [design issue](https://github.com/Steltic/gpu_silo/issues/new/choose). An IFC element, a report section or a timestamp from the [film guide](docs/sequence.md) helps other contributors find the same detail.

Submit original contributions under the same CC0 1.0 dedication as the project. Identify any third-party material and its terms in your pull request. [Project dedication](LICENSE)

## Change and check the model

1. Edit [design/project.json](design/project.json) or the subsystem it controls on a new branch.
2. Regenerate the calculations and report. Commit the generated files with the input change.
3. Add the reason for a design change to the [decision log](design/history.md). Identify the assumptions it replaces.
4. Open a pull request. **Check the design** validates the calculations, IFC, scene models and equipment clearances. The **gpu-silo-stills** artifact contains model views for review.

From the repository root, using Python 3.12:

```shell
python -m pip install -r requirements.txt
python -m gpu_silo calcs
python -m gpu_silo calcs --check
python -m gpu_silo ifc
python -m gpu_silo build --scene-only --film short
python -m gpu_silo check --film short
```

Open `renders/GPU_Silo.ifc` in an IFC4 viewer. To export the IFC and scene models on GitHub, run **Export design models** in Actions and download **gpu-silo-models** from the run. The [film production notes](design/technical_short.md) document the separate Blender and FFmpeg build.

### Try a one-value change

In `storage`, change `"shaft_access_m": 0.62` to `0.7`. Every 4SU starts 0.08 m further from the shaft and its light-grey CDU and pump section shortens to 2.08 m, so the wall end stays where it was. The trusses are sized again, and the pod weight, the loads on the shaft and the clearance at the pod roots follow in the calculations and the design report. The gantry pick, footprint, service plug and installed copy follow in the film. Run `python -m gpu_silo calcs` and look at section 5 of the calculations: the clearance at the pod roots grows from 100 mm to about 150 mm. Then run the checks and inspect the pod-receiving chapter at 0:50.

To change one unit only, add it to `cdu_pump_section_m_by_unit`, for example `{"1": 0.25}`. A pod too long for the bore is rejected with a message that says so.

### The design report

[design/report.md](design/report.md) is the structural design report. It is generated with the calculations by `python -m gpu_silo calcs`, so do not edit it by hand. The register of checks and the document details are `design_checks` in the design file. The analysis is in [gpu_silo/structure.py](gpu_silo/structure.py) and the wording, tables and figures are in [gpu_silo/report.py](gpu_silo/report.py).

To add or revise a check, put the calculation and its own verification in its module, write it up in `report.py`, update the status in the register and raise the revision. The steel checks are in `structure.py`, the walls in `walls.py`, the heat balance of the store in `thermal.py`, the comparison of reinforcement in `reinforcement.py`, the foundation in `foundation.py` and the root connection, hub and drive in `connection.py`. `python -m gpu_silo calcs --check` fails if the report, a figure or the calculations no longer match the design file, or if a verification in one of these modules does not hold.
