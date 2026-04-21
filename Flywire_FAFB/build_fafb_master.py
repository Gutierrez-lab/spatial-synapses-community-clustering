#!/usr/bin/env python3
"""Download FlyWire FAFB v783 CSVs and build a per-neuron master table.

Outputs land in `<repo_root>/data/fafb_v783/` (git-ignored). Re-running is
safe: files that already exist on disk are skipped during the download step.

Usage
-----
    python Flywire_FAFB/build_fafb_master.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import requests

VERSION = "783"
BASE = f"https://storage.googleapis.com/flywire-data/codex/data/fafb/{VERSION}"

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTDIR = REPO_ROOT / "data" / f"fafb_v{VERSION}"
OUTDIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "classification.csv.gz",
    "neurons.csv.gz",
    "consolidated_cell_types.csv.gz",
    "cell_stats.csv.gz",
    "connectivity_tags.csv.gz",
    "names.csv.gz",
    "labels.csv.gz",
    "visual_neuron_types.csv.gz",
    "column_assignment.csv.gz",
    "connections_princeton.csv.gz",
    "synapse_coordinates.csv.gz",
]

TIMEOUT = 120
CHUNK_SIZE = 1024 * 1024  # 1 MB


def download_file(session: requests.Session, filename: str) -> None:
    url = f"{BASE}/{filename}"
    outpath = OUTDIR / filename
    temppath = OUTDIR / f"{filename}.part"

    if outpath.exists() and outpath.stat().st_size > 0:
        print(f"Skipping {filename} (already exists)")
        return

    print(f"Downloading {filename}...")

    with session.get(url, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        total = r.headers.get("Content-Length")
        total = int(total) if total and total.isdigit() else None
        downloaded = 0

        with open(temppath, "wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)

                if total:
                    pct = 100 * downloaded / total
                    print(
                        f"\r  {downloaded / (1024 ** 2):8.1f} / "
                        f"{total / (1024 ** 2):8.1f} MB ({pct:5.1f}%)",
                        end="",
                    )
                else:
                    print(f"\r  {downloaded / (1024 ** 2):8.1f} MB", end="")

    print()
    temppath.replace(outpath)
    print(f"Saved to {outpath}")


def download_all() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
            "Accept-Encoding": "identity",
        }
    )

    for filename in FILES:
        try:
            download_file(session, filename)
        except Exception as e:
            print(f"Failed downloading {filename}: {e}")

    print("\nDownloads complete.\n")


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    )
    return df


def deduplicate_root_id(df: pd.DataFrame, name: str) -> pd.DataFrame:
    if "root_id" not in df.columns:
        return df
    before = len(df)
    df = df.drop_duplicates(subset=["root_id"]).copy()
    after = len(df)
    print(f"{name}: dropped {before - after:,} duplicate rows")
    return df


def build_master_table() -> pd.DataFrame:
    classification_path = OUTDIR / "classification.csv.gz"
    neurons_path = OUTDIR / "neurons.csv.gz"
    cell_types_path = OUTDIR / "consolidated_cell_types.csv.gz"
    cell_stats_path = OUTDIR / "cell_stats.csv.gz"
    conn_tags_path = OUTDIR / "connectivity_tags.csv.gz"
    names_path = OUTDIR / "names.csv.gz"
    connections_path = OUTDIR / "connections_princeton.csv.gz"

    classification = pd.read_csv(classification_path, low_memory=False)
    neurons = pd.read_csv(neurons_path, low_memory=False)
    cell_types = pd.read_csv(cell_types_path, low_memory=False)
    cell_stats = pd.read_csv(cell_stats_path, low_memory=False)
    conn_tags = pd.read_csv(conn_tags_path, low_memory=False)
    names = pd.read_csv(names_path, low_memory=False)

    for name, df in {
        "classification": classification,
        "neurons": neurons,
        "cell_types": cell_types,
        "cell_stats": cell_stats,
        "conn_tags": conn_tags,
        "names": names,
    }.items():
        print(f"\n{name}")
        print(df.shape)
        print(df.columns.tolist())
        print(df.head(2))

    classification = clean_columns(classification)
    neurons = clean_columns(neurons)
    cell_types = clean_columns(cell_types)
    cell_stats = clean_columns(cell_stats)
    conn_tags = clean_columns(conn_tags)
    names = clean_columns(names)

    for name, df in {
        "classification": classification,
        "neurons": neurons,
        "cell_types": cell_types,
        "cell_stats": cell_stats,
        "conn_tags": conn_tags,
        "names": names,
    }.items():
        print(name, df.columns.tolist())

    expected_checks = {
        "classification": ["root_id"],
        "neurons": ["root_id"],
        "cell_types": ["root_id"],
        "cell_stats": ["root_id"],
        "conn_tags": ["root_id", "connectivity_tag"],
        "names": ["root_id"],
    }
    local_tables = {
        "classification": classification,
        "neurons": neurons,
        "cell_types": cell_types,
        "cell_stats": cell_stats,
        "conn_tags": conn_tags,
        "names": names,
    }
    for df_name, cols in expected_checks.items():
        df = local_tables[df_name]
        missing = [c for c in cols if c not in df.columns]
        print(df_name, "missing:", missing)

    connections = pd.read_csv(
        connections_path,
        usecols=["pre_root_id", "post_root_id", "syn_count"],
        low_memory=False,
    )
    connections = clean_columns(connections)
    print(connections.shape)
    print(connections.columns.tolist())
    print(connections.head())

    for name, df in {
        "classification": classification,
        "neurons": neurons,
        "cell_types": cell_types,
        "cell_stats": cell_stats,
        "names": names,
    }.items():
        n_total = len(df)
        n_unique = df["root_id"].nunique()
        print(
            f"{name}: rows={n_total:,}, unique_root_id={n_unique:,}, "
            f"duplicates={n_total - n_unique:,}"
        )

    classification = deduplicate_root_id(classification, "classification")
    neurons = deduplicate_root_id(neurons, "neurons")
    cell_types = deduplicate_root_id(cell_types, "cell_types")
    cell_stats = deduplicate_root_id(cell_stats, "cell_stats")
    names = deduplicate_root_id(names, "names")

    master = classification.copy()

    for df, cols in [
        (
            neurons,
            [
                "root_id",
                "nt_type",
                "nt_type_score",
                "da_avg",
                "ser_avg",
                "gaba_avg",
                "glut_avg",
                "ach_avg",
                "oct_avg",
                "group",
            ],
        ),
        (cell_types, ["root_id", "primary_type"]),
        (cell_stats, ["root_id", "length_nm", "area_nm", "size_nm"]),
        (names, ["root_id", "name"]),
    ]:
        if not df.empty:
            keep = [c for c in cols if c in df.columns]
            print("Merging columns:", keep)
            master = master.merge(df[keep], on="root_id", how="left")

    if "length_nm" in master.columns:
        master["length_um"] = master["length_nm"] / 1_000
    if "area_nm" in master.columns:
        master["area_um2"] = master["area_nm"] / 1_000_000
    if "size_nm" in master.columns:
        master["volume_um3"] = master["size_nm"] / 1_000_000_000

    if not conn_tags.empty and "connectivity_tag" in conn_tags.columns:
        tag_df = conn_tags.copy()
        for tag, col in [
            ("rich_club", "rich_club"),
            ("reciprocal", "reciprocal"),
            ("feedforward", "feedforward"),
            ("3_cycle", "cycle_3"),
        ]:
            tag_df[col] = (
                tag_df["connectivity_tag"].astype(str).str.contains(tag, na=False)
            )

        tag_df = (
            tag_df.groupby("root_id")[
                ["rich_club", "reciprocal", "feedforward", "cycle_3"]
            ]
            .any()
            .reset_index()
        )

        master = master.merge(tag_df, on="root_id", how="left")
        for col in ["rich_club", "reciprocal", "feedforward", "cycle_3"]:
            master[col] = master[col].fillna(False)

    if not connections.empty:
        pairs = (
            connections.groupby(
                ["pre_root_id", "post_root_id"], as_index=False
            )["syn_count"].sum()
        )

        in_deg = (
            pairs.groupby("post_root_id")["pre_root_id"].nunique().rename("in_degree")
        )
        out_deg = (
            pairs.groupby("pre_root_id")["post_root_id"].nunique().rename("out_degree")
        )
        in_str = (
            pairs.groupby("post_root_id")["syn_count"].sum().rename("in_strength")
        )
        out_str = (
            pairs.groupby("pre_root_id")["syn_count"].sum().rename("out_strength")
        )

        degree_df = pd.concat([in_deg, out_deg, in_str, out_str], axis=1).fillna(0)
        for col in degree_df.columns:
            degree_df[col] = degree_df[col].astype(int)

        degree_df.index.name = "root_id"
        degree_df = degree_df.reset_index()

        master = master.merge(degree_df, on="root_id", how="left")
        for col in ["in_degree", "out_degree", "in_strength", "out_strength"]:
            master[col] = master[col].fillna(0).astype(int)

    n = len(master)
    print(f"\nMaster table: {n:,} neurons x {master.shape[1]} columns")
    print(master.columns.tolist())
    print(master.head())
    print(master["root_id"].nunique(), len(master))

    missing_summary = (
        master.isna().mean().sort_values(ascending=False).rename("missing_frac")
    )
    print(missing_summary.head(20))

    master_path = OUTDIR / "master_neuron_table.csv"
    master.to_csv(master_path, index=False)
    print(f"\nSaved {master_path}")

    for col in ["in_degree", "out_degree", "in_strength", "out_strength"]:
        if col in master.columns:
            print(col, master[col].min(), master[col].max())

    tag_cols = [c for c in ["rich_club", "reciprocal", "feedforward", "cycle_3"] if c in master.columns]
    if tag_cols:
        print(master[tag_cols].sum())

    size_cols = [c for c in ["length_um", "area_um2", "volume_um3"] if c in master.columns]
    if size_cols:
        print(master[size_cols].describe())

    return master


def main() -> None:
    print(f"Output directory: {OUTDIR}")
    download_all()
    build_master_table()
    print("\nDone.")


if __name__ == "__main__":
    main()
