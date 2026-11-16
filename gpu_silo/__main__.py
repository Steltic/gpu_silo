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
    calc = commands.add_parser("calcs", help="rewrite design/calcs.md from design/project.json")
    calc.add_argument("--check", action="store_true", help="fail if design/calcs.md is out of date")
    still = commands.add_parser("stills", help="render review frames as PNG")
    still.add_argument("frames", nargs="+", type=int)
    still.add_argument("--output", type=Path, default=Path("renders/stills"))
    args = parser.parse_args()
    if args.command == "calcs":
        from . import calcs
        if args.check:
            if not calcs.current():
                parser.exit(1, "design/calcs.md is out of date. Run: python -m gpu_silo calcs\n")
            print("design/calcs.md matches design/project.json")
            return
        print(calcs.write())
        return
    if args.command == "build":
        from .render_project import build_project
        build_project(args.output, movie=not args.scene_only, jobs=args.jobs)
        return
    if args.command == "stills":
        from .render_project import stills
        stills(args.output, args.frames)
        return
    if not args.model.is_file():
        parser.error(f"Model not found at {args.model}. Build it first or supply a GLB path.")
    from . import calcs
    from .validation import verify_frames, verify_logistics, verify_motion
    if not calcs.current():
        parser.exit(1, "design/calcs.md is out of date. Run: python -m gpu_silo calcs\n")
    verify_motion.main(args.model)
    verify_logistics.check(args.model)
    verify_frames.check(args.model)


if __name__ == "__main__":
    main()
