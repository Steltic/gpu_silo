# First-time setup

This folder is a complete local Git repository with one commit on `main`. Two steps put it on GitHub. Delete this file when they are done.

### 1. Turn on the GitHub configuration

The issue form, pull request template and render workflow are in `dot-github/`. Rename that folder to `.github` and commit the rename:

```shell
git mv dot-github .github
git commit -m "Enable the design idea form, pull request template and render workflow"
```

| File | What it does |
| --- | --- |
| `ISSUE_TEMPLATE/design-idea.yml` | The **Design idea** form contributors fill in |
| `pull_request_template.md` | Asks each pull request for the shot to review, the decision and the recalculated figures |
| `workflows/render.yml` | Checks the calculations, renders the MP4 and GLB for each pull request and publishes a release from `main` |

The workflow has not run on GitHub yet. It installs Mono, FFmpeg and the panel typefaces on an Ubuntu runner, which is the same toolchain that produced `renders/GPU_Silo.mp4`.

### 2. Create the repository and push

Create an empty repository on GitHub with no README, then:

```shell
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

The first push to `main` renders the film and publishes it as a release. The **Watch the animation** link in the README follows the latest release.

Things to decide on GitHub:

- **Licence.** None is included. Outside contributors need one to know how they may use and change the design.
- **Visibility.** The workflow uses GitHub-hosted runners, which are free for public repositories.
- **Labels.** The issue form applies a `design idea` label. Create it under Issues → Labels.
