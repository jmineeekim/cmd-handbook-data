# cmd-handbook-data

솔루션 엔지니어용 **명령어 핸드북 앱**의 데이터 저장소입니다.
RHEL·Rocky, Ubuntu·Debian, AIX, HP-UX, Solaris, Windows 명령어의 사용법을 JSON 으로 관리합니다.

- 15개 카테고리, 113개 기능(task), 662개 명령어
- 플랫폼별 명령어 수: RHEL 216 · Debian 209 · AIX 203 · Solaris 203 · HP-UX 175 · Windows 157 (공통 명령은 중복 집계)
- 명령어마다 요약, 설명, 문법, 주요 옵션, 실무 예시, 주의사항, 설치 정보, OS별 차이, 검색 키워드 포함

## 앱이 데이터를 받는 방법

```
1. https://raw.githubusercontent.com/<계정>/cmd-handbook-data/main/version.json  (작은 파일)
2. 앱에 저장된 dataVersion 보다 새로우면
   https://raw.githubusercontent.com/<계정>/cmd-handbook-data/main/dist/handbook.json  다운로드
3. sha256 확인 후 기기에 저장. 실패하면 저장된 데이터 또는 앱 내장 데이터 사용
```

앱에는 처음 실행용으로 `dist/handbook.json` 을 내장합니다. 공개 저장소이므로 API 키가 필요 없습니다.

## 폴더 구조

| 경로 | 설명 |
|---|---|
| `version.json` | 데이터 버전, 명령어 수, 번들 경로, sha256 (앱이 가장 먼저 확인) |
| `dist/handbook.json` | 앱이 받는 단일 번들 (meta + 모든 명령어, 빌드 결과물) |
| `meta/categories.json` | 카테고리 15개와 카테고리별 기능(task) 목록, 표시 순서, 아이콘 이름 |
| `meta/platforms.json` | 플랫폼(rhel/debian/aix/hpux/solaris/windows)과 묶음(Linux 공통·Unix 공통), 셸, 중요도, 위험도 정의와 표시 색상 |
| `commands/<category>.json` | 카테고리별 명령어 원본: Linux·Windows·공통 POSIX 명령 (사람이 편집하는 파일) |
| `commands/<category>.<os>.json` | Unix 전용 명령어 (`system.aix.json`, `disk.hpux.json`, `service.solaris.json` 등). 카테고리는 파일명 앞부분으로 판단 |
| `schema/commands.schema.json` | 명령어 파일 JSON Schema |
| `schema/example.command.json` | 작성 예시 (firewall-cmd) |
| `scripts/build.py` | 검증 + 번들 생성 스크립트 |

## 명령어 한 개의 구조

| 필드 | 필수 | 설명 |
|---|---|---|
| `id` | ✔ | 전체에서 유일한 id. 소문자, `-` 구분. Windows 전용 동명 명령은 `win-`, Unix 전용은 `aix-`·`hpux-`·`solaris-` 접두어 (`ping` / `win-ping`, `aix-errpt`) |
| `name` | ✔ | 화면에 보이는 이름 (`firewall-cmd`, `Get-Process`, `/etc/fstab`, `services.msc`) |
| `aliases` |  | 다른 이름·축약형 (`vi`, `gci`, `yum`) |
| `kind` | ✔ | `command` 명령어 / `file` 설정·로그 파일 / `gui` GUI 관리도구 |
| `shell` | command 일 때 ✔ | `sh` / `cmd` / `powershell` |
| `category`, `task` | ✔ | `meta/categories.json` 의 id. 같은 `task` 의 다른 OS 명령어는 앱이 "같은 기능, 다른 OS"로 자동 연결 |
| `platforms` | ✔ | `rhel`, `debian`, `aix`, `hpux`, `solaris`, `windows` 중 해당 항목. `rhel`+`debian` 이면 "Linux 공통", Linux+Unix 이면 "Unix·Linux 공통" |
| `level` | ✔ | `basic` 기본 / `frequent` 자주 / `critical` 드물지만 중요 |
| `risk` | ✔ | `safe` 조회 / `caution` 설정 변경 / `destructive` 데이터 손실·중단 가능 |
| `requiresAdmin` | ✔ | root·sudo 또는 Windows 관리자 권한 필요 여부 |
| `summary` | ✔ | 목록용 한 줄 설명 (60자 이내) |
| `description` | ✔ | 상세 화면 첫 문단 |
| `syntax` | ✔ | 문법 (여러 형태 가능) |
| `options` | ✔ | `{flag, desc}` 목록 |
| `examples` | ✔ | `{title, command \| steps, output?, note?, platforms?, version?}` 목록. 여러 줄은 `\n`. `steps` 는 `{prompt?, cmd, desc}` 단계 목록 (작업 흐름형 예시) |
| `commandGroups` |  | 실행 플래그가 아닌 사용법 묶음. `{title, type, prompt?, note?, columns?, items}`. type: `interactive` 대화형 내부 명령, `subcommand` 서브 명령, `keys` 단축키, `directive` 설정 항목, `action` GUI 작업. 항목은 `{cmd, desc, side?, note?, platforms?, version?}`, `columns` 를 주면 비교형 `{desc, left, right}` |
| `cautions` | ✔ | 주의사항 목록 |
| `install` |  | 플랫폼별 `{package, preinstalled, note}`. 최소 설치 기준 기본 설치 여부 |
| `platformNotes` |  | 플랫폼별 차이 설명 (옵션 유무, 대체 명령, 경로 차이) |
| `versions` |  | 특정 버전 이상에서만 있는 명령: `{"solaris": "11 이상"}` |
| `review` |  | 작성 상태 `{status: ai-draft \| field-verified, note?, date?}`. 내부 관리용이며 앱에는 표시하지 않음 |
| `help` |  | 내장 도움말 보는 법 (`man ss`, `Get-Help Get-Process -Full`) |
| `keywords` | ✔ | 검색어 (한글 기능명 + 영문) |
| `related` | ✔ | 관련 명령어 id |

### 바꿔 쓸 값 (플레이스홀더)

`{{UPPER_SNAKE}}` 형식으로 씁니다. 예: `firewall-cmd --permanent --add-port={{PORT}}/tcp`
앱은 이 부분을 강조 표시하고, 복사할 때는 `PORT` 처럼 이름만 남깁니다.
`<PORT>` 같은 꺾쇠 표기는 셸 리다이렉션과 헷갈려 사용하지 않습니다.

## 데이터 수정 방법

```bash
# 1. commands/<category>.json 수정
# 2. 검증
python3 scripts/build.py --check
# 3. 번들과 버전 파일 생성 (dataVersion 자동 갱신)
python3 scripts/build.py
# 4. commands/, dist/handbook.json, version.json 을 함께 커밋
```

검증 항목: JSON Schema, id 중복, category·task 존재 여부, related 대상 존재 여부, shell 과 platforms 조합, install·platformNotes·versions 키가 platforms 안에 있는지, 플레이스홀더 형식(steps·commandGroups 포함).

## 기준 버전

RHEL/Rocky 8·9, Ubuntu 22.04·24.04 LTS, Debian 12, AIX 7.2·7.3, HP-UX 11i v3, Solaris 10·11, Windows Server 2019·2022·2025, Windows 10·11.
실제 환경에 적용하기 전에 대상 서버의 버전과 정책을 꼭 확인하세요. 잘못된 내용은 앱의 "수정 제안" 버튼이나 Issues 로 알려주세요.
