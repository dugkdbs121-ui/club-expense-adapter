# 동아리 행사 지출 정리

여러 담당자가 작성한 CSV를 검사하고, 분류별 지출과 전체 합계를 계산해 JSON으로 저장하는 Python 과제 프로젝트입니다. 웹 화면과 명령행이 같은 최종 계산 함수를 호출합니다. 모든 예제는 과제용 가상 데이터입니다.

## GitHub 저장소

[dugkdbs121-ui/club-expense-adapter](https://github.com/dugkdbs121-ui/club-expense-adapter)에 소스코드를 공개했습니다. 링크만으로 소스 ZIP과 PDF 제출을 대신하지 않습니다.

## 먼저 실행하기

1. Python 3.12를 설치합니다. 작성·검증 환경의 정확한 버전은 `evidence/test_results.json`에서 확인합니다.
2. ZIP을 풀고, `README.md`와 `web_app.py`가 있는 폴더에서 터미널을 엽니다.
3. `python --version`으로 Python이 실행되는지 확인합니다. Windows에서 `python` 대신 `py -3`을 사용할 수도 있습니다.
4. 아래 명령으로 검사합니다.

```text
python check_all.py
python check_web.py
python check_cli.py
```

5. 아래 명령으로 웹 화면을 시작합니다.

```text
python web_app.py
```

6. 브라우저에서 `http://127.0.0.1:8765`를 엽니다. 서버를 켠 터미널은 그대로 두고, 종료할 때 `Ctrl+C`를 누릅니다.

표준 라이브러리만 사용하므로 `pip install`은 필요하지 않습니다. 인터넷에 공개하는 서비스가 아니라 한 컴퓨터에서 실행하는 과제용 웹앱입니다. 별도 DB·계정·외부 입력 파일은 필요하지 않으며 예제 CSV를 포함했습니다.

## 웹 사용 방법

1. 동아리·행사·은행 예제 중 하나를 불러오거나, UTF-8 CSV 파일을 선택합니다.
2. 업로드한 CSV에 맞는 양식을 선택합니다. 예제 버튼은 양식도 함께 선택합니다.
3. 검사·집계를 실행하면 전체 금액, 지출 건수, 분류별 결과를 확인할 수 있습니다.
4. 성공한 결과는 `outputs/latest_report.json`에 저장됩니다. 다운로드 버튼으로 같은 내용을 받을 수 있습니다.
5. 잘못된 입력이면 오류를 보여주고 기존 성공 결과 파일은 유지합니다. 성공할 때마다 최근 결과 파일을 교체하며 여러 작업의 이력을 누적하지 않습니다.

업로드는 1MB 이하로 제한합니다. 날짜·분류·금액을 검사하고, 금액은 **건별 0~1,000,000,000원 정수**만 허용합니다. 0원은 무료 제공 항목을 기록하는 경우를 표현합니다. 제목만 있는 파일, 빈 분류, 잘못된 날짜, 음수·소수·문자 금액은 거부합니다. 입력 원본은 수정하지 않습니다.

## 터미널에서 직접 실행하기

같은 club 입력을 세 버전으로 처리하려면 프로젝트 폴더에서 아래 명령을 각각 실행합니다. 결과는 화면과 지정한 JSON 파일에 나옵니다.

```text
python -m baseline.main examples/club_normal.csv --format club --output outputs/baseline_report.json
python -m refactored.service examples/club_normal.csv --format club --output outputs/refactored_report.json
python -m extended.service examples/club_normal.csv --format club --output outputs/extended_report.json
```

추가한 bank 양식은 최종판으로 실행합니다.

```text
python -m extended.service examples/bank_normal.csv --format bank --output outputs/bank_report.json
```

본인 파일을 사용하려면 입력 경로와 `--format`을 바꿉니다. 경로에 공백이 있으면 큰따옴표로 감쌉니다. 원본 보호를 위해 입력 경로와 `--output` 경로가 같으면 오류로 거부합니다. 기존 결과 JSON은 다음 성공 실행 때 교체됩니다.

## CSV 양식

| 양식 이름 | 열 이름 | 날짜 예시 | 금액 예시 | 지원 버전 |
|---|---|---|---|---|
| `club` | 날짜,항목,금액 | 2026-11-10 | 12000 | 세 버전 모두 |
| `event` | 사용일,분류,지출액 | 2026/11/10 | 12000 | 세 버전 모두 |
| `bank` | 거래일,사용처분류,출금액 | 2026.11.10 | `"12,000원"` | 작은 변경 후 |

`bank`는 과제용 가상 은행 양식이며 특정 은행의 실제 파일과 호환된다는 의미는 아닙니다. CSV의 금액에 쉼표가 포함되면 큰따옴표로 감싸야 합니다. 날짜는 실제 달력에 존재해야 하고 각 양식의 표기와 일치해야 합니다.

## 세 단계의 비교

| 단계 | 코드 위치 | 동작 |
|---|---|---|
| 구조 개선 전 | `baseline/` | club/event를 한 모듈의 함수와 조건 분기로 처리 |
| 구조 개선 후 | `refactored/` | 형식 변환을 Adapter로 분리하고 검사·집계·저장을 각각 모듈화 |
| 작은 변경 후 | `extended/` | BankAdapter를 연결하여 bank를 추가; 공통 검사·집계·저장은 재사용 |

검사 코드는 같은 입력·초기 파일 상태로 세 버전의 반환값, 오류 메시지, 저장 내용을 비교합니다. 새 bank 형식은 앞의 두 버전이 거부하고 최종판만 처리하는 것이 의도한 변경입니다. 기존 입력의 결과가 바뀌는 것과 구분합니다.

예제 세 파일은 날짜·표기만 다르고 실제 내용은 같습니다. 예상 결과는 **3건, 전체 20,000원, 간식 2건 16,500원, 문구 1건 3,500원**입니다. 예상은 검사 코드의 독립 상수로 두고 실제 실행 결과와 비교합니다.

## 파일 구성

```text
baseline/       개선 전 기본 프로그램
refactored/     Adapter, 입력 검사, 집계, 저장, 연결 역할
extended/       새 bank Adapter와 연결
examples/       정상·경계·오류 CSV
tests/          예상과 실제 결과를 비교하는 검사
check_all.py    전체 검사와 결과 기록
check_web.py    실제 HTTP 요청·다운로드·오류 검사
check_cli.py    세 버전 명령행 실행·원본 경로 보호 검사
web_app.py      로컬 웹 요청을 최종 Python 계산에 연결
static/         HTML·CSS·JavaScript 화면
evidence/       자동 검사 결과와 웹 동작 근거
docs/           구조·변경·AI 사용·제출 확인 안내
outputs/        사용자가 실행할 때 생성되는 결과(제출·Git 제외)
```

## 수업 개념과 구현 범위

핵심 계산은 2~3주차의 자료형·조건·반복, 5주차의 함수·인수·반환, 6주차의 리스트·딕셔너리, 10주차의 클래스·모듈·검사, 11주차의 Adapter·합성과 연결됩니다. 웹 화면과 `csv`, `json`, `datetime`, `http.server`의 구체적인 사용법은 공식 문서를 참고한 구현 지원 부분입니다. 이 부분까지 모두 수업에서 직접 작성했다고 주장하지 않습니다.

## 출처와 AI 사용

- 제공 5·6·10·11주차 파이썬 실습과 11-3 Adapter·Facade 강의자료.
- [Python csv](https://docs.python.org/3.12/library/csv.html), [datetime](https://docs.python.org/3.12/library/datetime.html), [json](https://docs.python.org/3.12/library/json.html), [http.server](https://docs.python.org/3.12/library/http.server.html).
- Codex로 설계·코드·검사·문서를 작성하고 실제 실행으로 확인했습니다. 상세 지원 범위와 검토 내역은 `docs/AI_USAGE.md`에 있습니다.
- 이 저장소의 자동 실행 기록은 도구가 수행한 검사 기록입니다. 학생이 독립적으로 먼저 예측하거나 실행했다는 증거로 제시하지 않습니다.

