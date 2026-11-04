#!/usr/bin/env python3
"""cmd-handbook-data 검증 + 번들 생성 스크립트.

사용법:
  python3 scripts/build.py            # 검증 후 dist/handbook.json, version.json 생성
  python3 scripts/build.py --check    # 검증만 (파일 생성 안 함)
  python3 scripts/build.py --check commands/network.json   # 특정 파일만 검증

검증 항목
  1. JSON Schema (schema/commands.schema.json) - jsonschema 패키지가 있으면 사용
  2. id 전체 유일성, 파일명 = category
  3. category / task 가 meta/categories.json 에 존재하는지
  4. related id 가 실제로 존재하는지
  5. kind=command 이면 shell 필수, shell 과 platforms 의 조합이 맞는지
  6. install / platformNotes / example.platforms 키가 platforms 안에 있는지
  7. 플레이스홀더 표기 규칙: {{UPPER_SNAKE}} 만 허용, <IP> 같은 꺾쇠 표기 금지
"""
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 1

PH_OK = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
PH_BAD_BRACE = re.compile(r"\{\{(?![A-Z][A-Z0-9_]*\}\})[^}]*\}\}")
PH_BAD_ANGLE = re.compile(r"<[A-Z][A-Z0-9_]*>")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def text_fields(cmd):
    for s in cmd.get("syntax", []):
        yield "syntax", s
    for o in cmd.get("options", []):
        yield "options.flag", o["flag"]
    for e in cmd.get("examples", []):
        if "command" in e:
            yield "examples.command", e["command"]
        for s in e.get("steps", []):
            yield "examples.steps", s["cmd"]
    for g in cmd.get("commandGroups", []):
        for it in g["items"]:
            for k in ("cmd", "left", "right"):
                if k in it:
                    yield "commandGroups", it[k]


def main(argv):
    check_only = "--check" in argv
    only = [a for a in argv if not a.startswith("--")]

    cats = load(ROOT / "meta/categories.json")["categories"]
    cat_ids = {c["id"] for c in cats}
    task_ids = {t["id"]: c["id"] for c in cats for t in c["tasks"]}

    validator = None
    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator(load(ROOT / "schema/commands.schema.json"))
    except ImportError:
        print("[warn] jsonschema 미설치: 스키마 검증 생략 (pip install jsonschema)")

    files = sorted((ROOT / "commands").glob("*.json")) if not only else [Path(a).resolve() for a in only]
    errors, warns = [], []
    all_cmds, seen = [], {}

    for fp in files:
        rel = fp.relative_to(ROOT)
        try:
            data = load(fp)
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{rel}: JSON 파싱 실패 - {ex}")
            continue
        if validator:
            for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                loc = "/".join(str(x) for x in err.path)
                errors.append(f"{rel}: schema [{loc}] {err.message[:200]}")
        cat = data.get("category")
        if cat != fp.stem:
            errors.append(f"{rel}: category '{cat}' 가 파일명과 다름")
        if cat not in cat_ids:
            errors.append(f"{rel}: 알 수 없는 category '{cat}'")
        for c in data.get("commands", []):
            cid = c.get("id", "?")
            where = f"{rel}:{cid}"
            if cid in seen:
                errors.append(f"{where}: id 중복 (이미 {seen[cid]})")
            seen[cid] = str(rel)
            if c.get("category") != cat:
                errors.append(f"{where}: command.category '{c.get('category')}' != 파일 category '{cat}'")
            t = c.get("task")
            if t not in task_ids:
                errors.append(f"{where}: 알 수 없는 task '{t}'")
            elif task_ids[t] != cat:
                errors.append(f"{where}: task '{t}' 는 '{task_ids[t]}' 카테고리 소속")
            plats = set(c.get("platforms", []))
            kind, shell = c.get("kind"), c.get("shell")
            if kind == "command":
                if shell in ("cmd", "powershell") and plats != {"windows"}:
                    errors.append(f"{where}: shell={shell} 인데 platforms={sorted(plats)}")
                if shell == "sh" and "windows" in plats:
                    warns.append(f"{where}: shell=sh 인데 windows 포함 (Windows 에서도 같은 문법인지 확인)")
            elif shell is not None:
                warns.append(f"{where}: kind={kind} 인데 shell 지정됨")
            for key in ("install", "platformNotes"):
                extra = set(c.get(key, {}) or {}) - plats
                if extra:
                    errors.append(f"{where}: {key} 에 platforms 밖의 키 {sorted(extra)}")
            for i, e in enumerate(c.get("examples", [])):
                extra = set(e.get("platforms", []) or []) - plats
                if extra:
                    errors.append(f"{where}: examples[{i}].platforms 에 platforms 밖의 값 {sorted(extra)}")
            for fld, s in text_fields(c):
                if PH_BAD_BRACE.search(s):
                    errors.append(f"{where}: {fld} 플레이스홀더 형식 오류 → {s!r}")
                if PH_BAD_ANGLE.search(s):
                    errors.append(f"{where}: {fld} 꺾쇠 플레이스홀더 사용 → {{{{NAME}}}} 로 바꿀 것: {s!r}")
            if len(c.get("summary", "")) > 60:
                errors.append(f"{where}: summary 60자 초과")
            all_cmds.append(c)

    if not only:
        ids = set(seen)
        for c in all_cmds:
            for r in c.get("related", []):
                if r not in ids:
                    errors.append(f"{seen[c['id']]}:{c['id']}: related '{r}' 없음")
        used = {c["task"] for c in all_cmds}
        for t in task_ids:
            if t not in used:
                warns.append(f"task '{t}' 에 명령어가 없음")

    for w in warns:
        print("[warn]", w)
    for e in errors:
        print("[error]", e)
    print(f"\n파일 {len(files)}개 · 명령어 {len(all_cmds)}개 · 오류 {len(errors)} · 경고 {len(warns)}")
    if errors:
        return 1
    if check_only or only:
        return 0

    order = {c["id"]: c["order"] for c in cats}
    lv = {"basic": 0, "frequent": 1, "critical": 2}
    all_cmds.sort(key=lambda c: (order[c["category"]], c["task"], lv[c["level"]], c["name"].lower()))
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    data_version = now.strftime("%Y.%m.%d.%H%M")
    bundle = {
        "schemaVersion": SCHEMA_VERSION,
        "dataVersion": data_version,
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "platforms": load(ROOT / "meta/platforms.json"),
        "categories": cats,
        "commands": all_cmds,
    }
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    raw = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (dist / "handbook.json").write_bytes(raw)
    version = {
        "schemaVersion": SCHEMA_VERSION,
        "dataVersion": data_version,
        "generatedAt": bundle["generatedAt"],
        "commandCount": len(all_cmds),
        "categoryCount": len(cats),
        "bundle": "dist/handbook.json",
        "bundleBytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    (ROOT / "version.json").write_text(json.dumps(version, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"dist/handbook.json ({len(raw):,} bytes), version.json 생성 · dataVersion {data_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
