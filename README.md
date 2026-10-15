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

### 파일 작업 전 사전 점검

```powershell
py -3 doctor.py --folder 'C:\YourPrivateFolder'
```

이 명령은 입력 경로와 실제 경로, 폴더 존재 여부, 공식 CLI 연결, Guard/샌드박스, 저장된 폴더 허용 범위와 중립 REPL의 작업 폴더를 **읽기 전용으로** 확인합니다. 키·파일 내용은 읽지 않고 설정도 바꾸지 않습니다. 진단 결과에는 로컬 폴더 경로가 포함되므로 공개 이슈에 그대로 붙이지 마세요.

**MSIX 경로 리디렉션도 확인하세요.** 패키지로 설치된 Codex에서 `AppData\Local\YourApp`에 만든 폴더가 실제로는 `AppData\Local\Packages\<package>\LocalCache\Local\YourApp`에 있을 수 있습니다. 다른 일반 데스크톱 앱은 원래 경로에서 그 폴더를 찾지 못할 수 있습니다. `requestedFolder`, `physicalFolder`, `pathRedirected`를 비교하고, 동일 폴더임을 확인한 실제 경로를 명시적으로 승인한 범위에 연결하세요. Windows 가상화·샌드박스를 해제하거나 다른 폴더까지 허용할 필요는 없습니다. [Microsoft 공식 설명](https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes)

**Windows ACL, Aside의 계정 폴더 허용, 프로젝트·세션 작업 폴더 경계는 별개입니다.** 2026-10-15 확인 시 계정 `writableRoots`에 폴더를 저장하고 재연결해도, 중립 REPL은 `Path escapes Project and session roots`로 거부할 수 있었습니다. 계정 권한 저장 성공을 실제 파일 저장 성공으로 취급하지 마세요.

실제 경로가 승인 범위에 들어가는지 확인하고, 비밀 값이 없는 임시 파일을 **사용할 AI 작업에서** 쓰는 데 성공한 후 자격 증명을 저장하세요. 중립 REPL의 경계와 별도 AI 작업의 접근 범위는 같다고 가정하지 마세요. 실제 AI 작업에서도 경계 오류가 남으면 공식 [Working folder](https://docs.aside.com/help/tasks)에서 필요한 폴더만 지정하세요. 현재 이 프로젝트는 작업 폴더를 설정하는 문서화된 CLI 옵션을 확인하지 못했습니다. `doctor.py`는 실제 쓰기를 하지 않으므로 준비 완료를 주장하지 않으며 종료 코드 `2`를 반환합니다.

실제 Windows 사례에서는 MSIX 리디렉션 후의 동일 폴더 경로를 공식 쓰기 허용에 연결하자, Guard·샌드박스를 유지한 채 새 AI 작업의 임시 파일 쓰기·삭제가 성공했습니다. 이것이 모든 파일 오류의 원인이라는 뜻은 아니며, 개별 경계는 계속 확인해야 합니다.

Aside CLI는 `aside update`로 공식 업데이트할 수 있습니다. `1.26.1015.732`에서 연결 도움말과 유효한 Windows 게시자 서명을 확인했습니다. 업데이트만으로 폴더 경계 문제가 해결됐다고 검증한 것은 아닙니다. Full access 전환, 샌드박스 해제, ACL 전체 개방 또는 다른 API를 통한 거부 우회는 이 도구에서 수행하지 않습니다.

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
