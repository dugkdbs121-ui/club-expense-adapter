# 역할, 연결, 변경 범위

## 데이터 흐름

CSV 문자열 → `read_rows` → 선택된 Adapter의 `adapt` → `validate_records` → `summarize` → `save_report` → 결과 반환.

웹은 입력·출력 담당이며 `extended.service.run_text`를 호출한다. 합계 계산을 JavaScript에서 다시 구현하지 않는다. 명령행도 같은 `run_text`를 호출한다.

| 코드 | 역할 | 읽고 바꾸는 값 |
|---|---|---|
| `storage.read_rows` | CSV 문법·열 구조 검사, 행 읽기 | 문자열을 행 번호와 딕셔너리 목록으로 변환; 원본 파일은 쓰지 않음 |
| `adapters` | 외부 표현을 공통 데이터로 변환 | 날짜를 ISO 문자열, 금액을 정수, 분류를 공통 키에 연결 |
| `validation.validate_records` | 공통 규칙 확인 | 분류가 비어 있는지, 금액 범위가 맞는지 검사; 값을 바꾸지 않음 |
| `summary.summarize` | 집계 | 반복마다 전체 합계와 분류별 건수·합계가 증가 |
| `storage.save_report` | 성공 결과 저장 | JSON을 임시 파일에 모두 쓴 뒤 지정 결과 파일 교체 |
| `service.run_with_adapter` | 호출 순서 연결 | 데이터를 다음 함수로 전달하고 최종 결과 반환 |
| `web_app.ExpenseHandler` | HTTP 입력·출력 | 입력 JSON을 읽고 최종 결과 또는 오류를 응답 |

## Adapter를 선택한 이유

club의 `날짜/항목/금액`, event의 `사용일/분류/지출액`은 이름과 날짜 표기가 다르다. 두 Adapter는 같은 `adapt(row, row_number)` 호출과 `{date, category, amount}` 반환 형식을 제공한다. 서비스는 어느 양식을 읽었는지 몰라도 이후의 공통 검사를 호출할 수 있다. 상속을 위한 빈 부모 클래스나 Factory 패턴을 추가하지 않았다.

## 세 단계

1. `baseline/main.py`: 기본 동작을 여러 함수로 작성하되 한 모듈에 두고 `convert_rows`에서 양식별 분기한다. 처음부터 이해하기 어려운 한 줄 코드를 만들지 않는다.
2. `refactored/`: 읽기·저장, 변환, 검증, 집계, 연결을 분리하고 Adapter를 전달한다. 기존 입력의 결과·오류 메시지·저장 파일이 같아야 한다.
3. `extended/`: `BankAdapter`와 등록을 추가한다. 점 날짜와 원 단위 금액을 변환한다. 기존 `run_with_adapter`, 검증, 집계, 저장 함수는 그대로 가져다 쓴다.

## 작은 변경의 위치

- 새로 작성: `extended/adapters.py`의 금액 변환 함수와 `BankAdapter`.
- 새 연결: `extended/service.py`의 `ADAPTERS`에 bank 등록 및 CLI 선택값.
- 추가 근거: `examples/bank_normal.csv`, `tests/cases.py`의 X1~X3, 웹의 bank 선택.
- 유지: `refactored`의 두 기존 Adapter, 행 읽기, 공통 검증, 집계, JSON 저장, 실행 절차.

## 제한과 선택 이유

금액은 부동소수점 오차를 피하려고 정수 원 단위로 제한하고, 0원은 무료 제공 기록을 위해 허용한다. 10억 원 상한은 동아리 행사라는 범위와 비정상 입력 검사를 위한 과제용 가정이다. 3행 예제는 두 분류와 같은 분류의 누적을 함께 확인하기 위해 정했다. 빈 자료는 유효한 지출 보고서로 저장하지 않는다. 결과가 동일하게 비교되도록 분류명으로 정렬하고 실행 시각은 결과 JSON에 넣지 않는다.

입력 파일은 UTF-8 CSV만 다룬다. 원본 지출 데이터를 DB에 장기 보관하지 않고 최근 집계만 JSON으로 저장한다. 취소·환불(음수), 외화, 로그인, 여러 사용자의 동시 작업은 구현 범위에 포함하지 않는다.
