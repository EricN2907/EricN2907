# Maintaining this profile

The profile README uses a custom vector banner and checked-in SVG cards. Six images cover the five card types, including a two-column trophy layout for phones. They remain visible even when their upstream providers are down.

## Local commands

Python 3.13 is used by CI; the scripts need only the Python standard library.

```sh
python -m unittest discover -s tests -v
python scripts/refresh_cards.py
git diff --check
```

`scripts/refresh_cards.py` fetches the public trophy, stats, languages, streak and activity SVGs with a 20-second request timeout and 2 MiB limit. It checks XML, expected metric labels and active/external content before atomically replacing each asset. The activity graph's inert XHTML heading is allowed. No token is sent to these providers.

If an endpoint fails, the existing validated card and its successful retrieval time are kept. A missing or invalid fallback fails the command. `assets/card-status.json` records each card's source and successful retrieval time. Figures are provider snapshots, not live values or verified professional credentials; metrics from different services have different scopes.

## GitHub Actions

`.github/workflows/profile-cards.yml` runs daily at **03:23 UTC / 10:23 Asia/Ho_Chi_Minh**, manually, or after changes to its script/tests/workflow on `main`. GitHub may delay scheduled runs. It uses the built-in repository `GITHUB_TOKEN` only for committing refreshed assets, with `contents: write`. No PAT or extra secret is required.

The Actions jobs have not been executed remotely as part of this local update. If branch protection prevents bot commits, the refresh push will fail visibly; keep the checked-in snapshots and refresh them through the repository's normal review process. The separate snake workflow and `output` branch are preserved.

## Editing content

- Edit personal copy in `README.md`.
- Edit the original banner in `assets/profile-hero.svg`; it contains no external fonts or scripts.
- Navigation and contact buttons are original local SVGs in `assets/nav-*.svg` and `assets/contact-*.svg`. Their links live in `README.md`; no external badge service is required.
- Keep third-party notices in `assets/CREDITS.md` and `assets/licenses/` when updating cards.
- Core stats/trophies are local; the skills icons, snake, Discord and Spotify widgets still depend on their providers. Discord and Spotify are always visible at the bottom of the README, using their original widget URLs.

## Requested commit dates

The six profile-refresh commits use the requested author and committer timestamps at **12:00 +07:00** on **1, 4, 8, 13, 14 and 18 November 2026**. These timestamps are intentionally assigned metadata for changes prepared on 25 November 2026; they are not a claim that the changes or card snapshots existed on the assigned dates. On 26 November 2026, the user corrected the requested year from 2025 to 2026. The six commits and their descendants were rewritten with a local backup; all file trees were preserved, and history before the profile refresh was unchanged.

Two further changes prepared on 26 November 2026 use the user-requested author and committer dates at **12:00 +07:00**: **13 October 2026** for navigation buttons and **21 November 2026** for the contact layout. These are assigned dates, not the actual implementation dates. They append to history without rewriting the earlier commits.

Commits must reach the default branch on GitHub and use an email connected to the account to count as profile contributions. Publication and graph updates are separate from creating local commits. See [GitHub's contribution troubleshooting guide](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/troubleshooting-missing-contributions).

## Local verification · 2026-11-25

- Seven unit tests passed: metric validation, malformed/active SVG rejection, the activity graph's inert label, provenance, provider timeout/error fallback, missing snapshots and filename containment.
- A real refresh retrieved and validated all six card images. Every bundled SVG parsed as XML; workflow structure and the two official action pins were checked.
- A local Markdown preview was checked in Chromium at 1200 px and 390 px: core SVGs decoded, the mobile trophy source was selected on phones, four section anchors existed, and there was no horizontal document overflow or page error. This preview approximates GitHub Markdown styling; it is not a published GitHub-page acceptance check.
- Discord, Spotify and both existing snake URLs returned image/SVG responses during this session. Their future uptime is not controlled by this repository.

## Navigation and contact verification · 2026-11-26

- Local SVG image paths and XML were checked; section anchors and the original contact destinations were preserved.
- The local Markdown preview was checked in Chromium at 1200, 390 and 320 px. All local images decoded, all three navigation links worked, the three contact buttons had the expected destinations, and there was no horizontal document overflow or page error. The desktop/mobile preview approximates GitHub styling; remote widget playback/presence was not retested.
