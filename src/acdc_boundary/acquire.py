import csv
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .paths import DATA_RAW, PROVENANCE


SOURCES = [
    {
        "dataset_id": "simbench-1.6.1-wheel",
        "publisher": "PyPI / SimBench consortium",
        "url": "https://files.pythonhosted.org/packages/fc/fa/d30a9ba570eb05c4013712b6b1e4eaef411c5c486e07637a6d2380617c2e/simbench-1.6.1-py3-none-any.whl",
        "version": "1.6.1",
        "license": "ODbL-1.0 database; BSD-3-Clause code",
        "redistribution": "allowed with license and attribution",
        "path": DATA_RAW / "simbench/1.6.1/simbench-1.6.1-py3-none-any.whl",
        "expected_sha256": "f1d8c879cc35bca17552ac6fd0ea95e9097bc0300f61d66f13eb1d755017a763",
    },
    {
        "dataset_id": "ev-charging-22495141-v1",
        "publisher": "figshare",
        "url": "https://ndownloader.figshare.com/files/39952252",
        "version": "10.6084/m9.figshare.22495141.v1",
        "license": "CC BY 4.0",
        "redistribution": "allowed with attribution",
        "path": DATA_RAW / "ev_charging/22495141_v1/ChargingRecords.csv",
        "expected_sha256": "d541259bed55e2a9bc3413756954e7a059b50f9c9031f1dfc6ec87cbf3afd358",
    },
]

REFERENCE_METADATA_SOURCES = [
    {
        "record_id": "10.1109/TSG.2016.2608508",
        "provider": "Crossref",
        "url": "https://api.crossref.org/works/10.1109%2FTSG.2016.2608508",
        "path": DATA_RAW / "reference_metadata/10_1109_TSG_2016_2608508.json",
        "license": "Crossref metadata reuse under provider terms",
    },
    {
        "record_id": "10.1016/j.energy.2016.12.015",
        "provider": "Crossref",
        "url": "https://api.crossref.org/works/10.1016%2Fj.energy.2016.12.015",
        "path": DATA_RAW / "reference_metadata/10_1016_j_energy_2016_12_015.json",
        "license": "Crossref metadata reuse under provider terms",
    },
    {
        "record_id": "10.3390/en12091751",
        "provider": "Crossref",
        "url": "https://api.crossref.org/works/10.3390%2Fen12091751",
        "path": DATA_RAW / "reference_metadata/10_3390_en12091751.json",
        "license": "Crossref metadata reuse under provider terms",
    },
    {
        "record_id": "10.1109/TSG.2021.3102615",
        "provider": "Crossref",
        "url": "https://api.crossref.org/works/10.1109%2FTSG.2021.3102615",
        "path": DATA_RAW / "reference_metadata/10_1109_TSG_2021_3102615.json",
        "license": "Crossref metadata reuse under provider terms",
    },
    {
        "record_id": "10.1109/TPWRD.2023.3277089",
        "provider": "Crossref",
        "url": "https://api.crossref.org/works/10.1109%2FTPWRD.2023.3277089",
        "path": DATA_RAW / "reference_metadata/10_1109_TPWRD_2023_3277089.json",
        "license": "Crossref metadata reuse under provider terms",
    },
    {
        "record_id": "10.1016/j.apenergy.2022.119438",
        "provider": "Crossref",
        "url": "https://api.crossref.org/works/10.1016%2Fj.apenergy.2022.119438",
        "path": DATA_RAW / "reference_metadata/10_1016_j_apenergy_2022_119438.json",
        "license": "Crossref metadata reuse under provider terms",
    },
    {
        "record_id": "10.3390/en13123290",
        "provider": "Crossref",
        "url": "https://api.crossref.org/works/10.3390%2Fen13123290",
        "path": DATA_RAW / "reference_metadata/10_3390_en13123290.json",
        "license": "Crossref metadata reuse under provider terms",
    },
    {
        "record_id": "10.6084/m9.figshare.22495141.v1",
        "provider": "Figshare",
        "url": "https://api.figshare.com/v2/articles/22495141",
        "path": DATA_RAW / "reference_metadata/figshare_22495141.json",
        "license": "Record metadata; associated dataset is CC BY 4.0",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def retrieved_utc(path: Path) -> str:
    timestamp_path = path.with_suffix(path.suffix + ".retrieved_utc")
    if timestamp_path.exists():
        return timestamp_path.read_text(encoding="utf-8").strip()
    retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(
        microsecond=0
    )
    value = retrieved.isoformat()
    timestamp_path.write_text(value + "\n", encoding="utf-8")
    return value


def download(source: dict) -> None:
    path = source["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and sha256(path) == source["expected_sha256"]:
        return
    target = path.with_suffix(path.suffix + ".download")
    urllib.request.urlretrieve(source["url"], target)
    actual = sha256(target)
    if actual != source["expected_sha256"]:
        target.unlink(missing_ok=True)
        raise ValueError(f"Checksum mismatch for {source['dataset_id']}: {actual}")
    target.replace(path)
    retrieved_utc(path)


def download_reference_metadata(source: dict) -> None:
    path = source["path"]
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.with_suffix(path.suffix + ".download")
    urllib.request.urlretrieve(source["url"], target)
    json.loads(target.read_text(encoding="utf-8"))
    target.replace(path)
    retrieved_utc(path)


def write_ledger() -> None:
    PROVENANCE.mkdir(parents=True, exist_ok=True)
    ledger = PROVENANCE / "raw_data_ledger.csv"
    fields = [
        "dataset_id",
        "publisher",
        "url",
        "version",
        "retrieved_utc",
        "retrieval_conditions",
        "license",
        "redistribution",
        "local_path",
        "bytes",
        "sha256",
        "verified",
    ]
    rows = []
    for source in SOURCES:
        path = source["path"]
        actual = sha256(path)
        rows.append(
            {
                "dataset_id": source["dataset_id"],
                "publisher": source["publisher"],
                "url": source["url"],
                "version": source["version"],
                "retrieved_utc": retrieved_utc(path),
                "retrieval_conditions": "complete object; HTTPS GET; no pagination",
                "license": source["license"],
                "redistribution": source["redistribution"],
                "local_path": str(path.relative_to(DATA_RAW.parent)),
                "bytes": path.stat().st_size,
                "sha256": actual,
                "verified": actual == source["expected_sha256"],
            }
        )
    with ledger.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "complete": all(row["verified"] for row in rows),
        "records": rows,
    }
    (PROVENANCE / "raw_data_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metadata_records = []
    for source in REFERENCE_METADATA_SOURCES:
        path = source["path"]
        metadata_records.append(
            {
                "record_id": source["record_id"],
                "provider": source["provider"],
                "url": source["url"],
                "retrieved_utc": retrieved_utc(path),
                "retrieval_conditions": "complete JSON object; HTTPS GET; no pagination",
                "license": source["license"],
                "redistribution": "manifest only; raw response retained locally",
                "local_path": str(path.relative_to(DATA_RAW.parent)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "processing_lineage": "citation metadata verification",
                "complete": True,
            }
        )
    (PROVENANCE / "reference_metadata_manifest.json").write_text(
        json.dumps(
            {"complete": True, "records": metadata_records},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    for source in SOURCES:
        download(source)
    for source in REFERENCE_METADATA_SOURCES:
        download_reference_metadata(source)
    write_ledger()


if __name__ == "__main__":
    main()
