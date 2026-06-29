# How to release and mint a Zenodo DOI

This repository is set up so that GitHub releases are archived on Zenodo with a
citable DOI. Do it once to connect, then every future release gets its own DOI
automatically, all resolving through a single concept DOI.

## One-time setup

1. Push this repository to GitHub (public).
2. Go to https://zenodo.org and sign in **with your GitHub account** (or link
   GitHub under Zenodo Settings if you already have a Zenodo account).
3. Go to Zenodo -> Settings -> GitHub. You will see a list of your repositories.
   Find `performative-discovery` and toggle the switch **On**.
   - Tip: test first on https://sandbox.zenodo.org (same flow) before doing it
     for real, since the connection cannot be moved to an existing concept DOI later.

## Cut the release

4. On GitHub: repo -> Releases -> "Draft a new release".
5. Create a tag with semantic versioning, e.g. `v1.0.0`, target `main`.
6. Title it (e.g. "v1.0.0 - initial release") and add release notes.
7. Click **Publish release**.

## Get the DOI

8. Zenodo automatically downloads the release ZIP and creates a record. This can
   take a few minutes.
9. Go to Zenodo -> your record. You now have a **version DOI** (this release) and
   a **concept DOI** (always points to the latest version).
10. Copy the DOI badge markdown from the record and paste it at the top of
    `README.md`, replacing the placeholder badge.

## Metadata

Zenodo reads metadata from, in order of priority: `.zenodo.json`,
then `CITATION.cff`, then `LICENSE`. This repo uses `CITATION.cff` (do **not**
add a `.zenodo.json`, or the CITATION file will be ignored). Before releasing:

- Fill in the ORCID lines in `CITATION.cff` (currently commented placeholders).
- Replace `<user>` in `CITATION.cff` and `README.md` with your GitHub handle.
- Do not add a `license:` field to `CITATION.cff`; the `LICENSE` file is read
  directly by Zenodo.

## New versions later

Cut another GitHub release with a higher tag (e.g. `v1.1.0`). Zenodo issues a new
version DOI under the same concept DOI automatically. Note: Zenodo rebuilds the
author list from repository contributors on each release, so keep `CITATION.cff`
authoritative.

## Pre-reserving a DOI

A DOI cannot be pre-reserved when using the GitHub integration; the DOI is issued
when the release is processed. If you need the DOI *before* releasing (e.g. to
print it inside the paper), upload the release ZIP to Zenodo manually instead,
which does allow reserving a DOI first.
