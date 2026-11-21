"""Build or check the GPU Silo animation and its design calculations from the repository root."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(prog="python -m gpu_silo", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build the movie and the editable model")
    build.add_argument("--output", type=Path, default=Path("renders"))
    build.add_argument("--scene-only", action="store_true", help="export the GLB only (needs Python and NumPy)")
    build.add_argument("--jobs", type=int, help="parallel render processes (default: one per CPU)")
    check = commands.add_parser("check", help="check an exported GLB against the working design")
    check.add_argument("model", nargs="?", type=Path, default=Path("renders/GPU_Silo.glb"))
    calc = commands.add_parser("calcs", help="rewrite design/calcs.md, design/report.md and its figures from design/project.json")
    calc.add_argument("--check", action="store_true", help="fail if the generated design documents are out of date")
    still = commands.add_parser("stills", help="render review frames as PNG")
    still.add_argument("frames", nargs="+", type=int)
    still.add_argument("--output", type=Path, default=Path("renders/stills"))
    voice = commands.add_parser("narrate", help="record the narration again after editing design/narration.json")
    voice.add_argument("--models", type=Path, required=True, help="folder holding the Kokoro model and voices files")
    for command in (build, check, still):
        command.add_argument("--film", choices=("long", "short"), default="long",
                             help="long is the full presentation, short is the build only (silo_short)")
    args = parser.parse_args()
    if getattr(args, "film", "long") == "short":
        import os
        os.environ["GPU_SILO_FILM"] = "short"
    if args.command == "narrate":
        from . import narrate
        path, seconds = narrate.record(args.models)
        print(f"{path} ({seconds:.1f} s)")
        return
    if args.command == "calcs":
        from . import calcs, report, structure
        if args.check:
            if not calcs.current():
                parser.exit(1, "design/calcs.md or design/report.md is out of date. Run: python -m gpu_silo calcs\n")
            structure.check()
            print("design/calcs.md and design/report.md match design/project.json")
            return
        structure.check()
        print(calcs.write())
        print(report.FILE)
        return
    if args.command == "build":
        from .render_project import build_project
        build_project(args.output, movie=not args.scene_only, jobs=args.jobs)
        return
    if args.command == "stills":
        from .render_project import stills
        stills(args.output, args.frames)
        return
    if args.model == Path("renders/GPU_Silo.glb"):
        from . import film
        args.model = Path("renders") / (film.OUTPUT + ".glb")
    if not args.model.is_file():
        parser.error(f"Model not found at {args.model}. Build it first or supply a GLB path.")
    from . import calcs, structure
    from .validation import verify_frames, verify_logistics, verify_motion
    if not calcs.current():
        parser.exit(1, "design/calcs.md or design/report.md is out of date. Run: python -m gpu_silo calcs\n")
    structure.check()
    print(structure.summary())
    verify_motion.main(args.model)
    verify_logistics.check(args.model)
    verify_frames.check(args.model)


if __name__ == "__main__":
    main()
