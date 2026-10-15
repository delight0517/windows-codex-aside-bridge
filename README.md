# 윈도우용 Codex 연결 — Aside AI

Windows의 **Codex에서 Aside AI에 명령을 보내고, 응답을 읽고, 같은 대화를 이어가는** 작은 오픈소스 연결 도구입니다.

Aside의 공식 CLI/MCP를 사용합니다. 비공식 독립 프로젝트이며 OpenAI·Aside와 제휴하지 않습니다. Aside 자체의 소스·바이너리를 배포하는 프로젝트는 아닙니다.

## 준비

- Windows 10/11, Python **3.11 이상** (`py -3 --version`으로 확인)
- Codex 로컬 데스크톱 또는 CLI
- [공식 Aside CLI](https://docs.aside.com/help/developers.md) 설치와 Aside 계정/모델 연결
- 로컬 호스트의 브라우저 작업에는 실행 중인 Aside Browser가 필요합니다.

Python 외 추가 패키지는 필요하지 않습니다. 이 프로젝트는 브라우저·CLI를 자동 설치하거나 로그인 자격 증명을 수집하지 않습니다.

## 1. Codex에 연결

저장소를 내려받고 해당 폴더에서 PowerShell을 엽니다.

```powershell
py -3 configure.py install
```

`%CODEX_HOME%\config.toml`(설정하지 않았다면 `%USERPROFILE%\.codex\config.toml`)에 `aside` MCP 서버를 추가합니다. 기존 설정은 보존하며, 첫 변경 전에 같은 폴더에 `config.toml.before-windows-aside`를 한 번 백업합니다. 백업에는 기존 설정의 비밀 값이 포함될 수 있으므로 공개하지 마세요.

이미 동일한 설정이 있으면 변경하지 않습니다. 같은 이름의 다른 서버는 덮어쓰지 않습니다.

```powershell
py -3 configure.py install --name aside_windows
```

등록 도구는 `exec`(AI 명령/응답)와 `repl`(브라우저 자동화)입니다. Codex의 승인·샌드박스 설정은 바꾸지 않습니다. Codex MCP 연결을 새로고침하거나 새 대화를 열면 도구가 표시됩니다. **Aside 브라우저를 재시작할 필요는 없습니다.**

## 2. CLI에서 바로 AI에 요청

현재 Codex 대화에 새 MCP 도구가 아직 표시되지 않아도 사용할 수 있습니다.

```powershell
py -3 aside_bridge.py --tools
py -3 aside_bridge.py '도구를 사용하지 말고 연결 확인이라고만 답해줘'
```

결과는 JSON입니다. `content`에는 AI 응답과 `session_id`가 들어 있습니다. 받은 세션 ID로 후속 요청을 보냅니다.

```powershell
py -3 aside_bridge.py --session '<받은-session-id>' '방금 대화를 이어서 설명해줘'
```

프롬프트는 인자 배열로 전달하며 셸 명령으로 조합하지 않습니다. 실제 요청은 선택된 Aside 계정/모델로 전송되며 해당 서비스의 요금·사용량 조건이 적용됩니다. 명령 인자는 로컬 프로세스 조회/셸 기록에 남을 수 있으므로 비밀번호·API 키를 프롬프트에 넣지 마세요.

기본 응답 제한은 180초입니다. 타임아웃은 **AI 작업 취소를 뜻하지 않습니다.** 서버가 계속 작업할 수 있으므로 같은 작업을 무작정 다시 보내지 말고 Aside에서 상태를 확인하세요.

```powershell
py -3 aside_bridge.py --timeout 300 '요청 내용'
```

## 3. 연결 제거

```powershell
py -3 configure.py uninstall
# 다른 이름으로 설치했다면:
py -3 configure.py uninstall --name aside_windows
```

이 도구가 등록한 것과 정확히 같은 MCP 설정만 제거합니다. 이후 직접 수정한 설정은 자동 삭제하지 않습니다. Aside 프로그램·계정·대화는 삭제하지 않습니다. Aside CLI를 먼저 지웠더라도 원래 경로의 등록은 제거할 수 있습니다.

## CLI나 설정 경로가 다른 경우

```powershell
py -3 configure.py install --aside-cli 'D:\Apps\Aside\aside.exe' --config 'D:\Codex\config.toml'
py -3 aside_bridge.py --aside-cli 'D:\Apps\Aside\aside.exe' '요청 내용'
```

직접 호출 클라이언트는 기본적으로 `%LOCALAPPDATA%\Aside\CLI\current\aside.exe`를 사용합니다.

## 확인한 범위

2026-10-15 Windows 환경, Aside CLI `1.26.906.1630`, Browser `1.0.928.2`에서:

- 공식 CLI AI 요청 → 텍스트 응답 수신
- MCP 초기화·도구 목록 조회
- MCP `exec` 호출 → 세션 ID·응답 수신
- 같은 세션 ID로 후속 요청 → 응답 수신

화면 입력이나 기존 브라우저 재시작 없이 확인했습니다. 모든 사이트의 자동화 성공이나 새 설치 환경 전체를 보장하는 검증은 아닙니다.

REA로 배포된 AgentManager JavaScript도 살펴봤습니다. 내부 데몬은 인증된 브라우저 연결을 사용하므로, 이 프로젝트는 내부 인증 토큰 추출 대신 공식 CLI를 호출합니다. 정적 의미 분석은 리소스 제한으로 부분 완료였으며, 위 AI 연결 결과는 실제 실행으로 따로 확인했습니다. 배포된 Aside 코드를 복사하거나 포함하지 않습니다.

## 문제 해결

- **CLI를 못 찾음:** 공식 Aside CLI를 설치하고 `aside --help`를 확인하세요.
- **로그인/모델 오류:** Aside 계정 및 AI 제공자 설정을 확인하세요. 이 도구에 키를 붙여넣지 마세요.
- **MCP가 안 보임:** Codex의 MCP 재연결 또는 새 대화를 사용하세요. 직접 CLI 호출은 즉시 가능합니다.
- **기존 서버 충돌:** 다른 `--name`을 쓰거나 기존 항목을 직접 검토하세요.
- **변경 중 잠금:** 다른 configure 프로세스가 끝났는지 확인하세요. 강제 종료 후 남은 `.aside-bridge.lock`은 실행 중인 설치가 없을 때만 정리하세요.

## 라이선스 및 참고

이 저장소의 연결 코드·문서는 [MIT](LICENSE) 라이선스입니다. Aside·Codex의 프로그램과 서비스에는 각각의 라이선스·약관이 적용됩니다.

- [Aside 공식 CLI/MCP/REPL 안내](https://docs.aside.com/help/developers.md)
- [Codex 공식 MCP 설정 안내](https://learn.chatgpt.com/docs/extend/mcp)

문제 제보에는 버전과 재현 절차를 포함하고, 계정 토큰·개인 설정·대화 기록은 첨부하지 마세요.
