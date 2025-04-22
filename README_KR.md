
<div align="center">

<img src="docs/logo.png" alt="pyhunt_logo" width="200"/>

# pyhunt

`pyhunt`는 로그를 시각적으로 표현하여 빠른 구조 파악과 디버깅을 지원하는    
경량 로깅 도구입니다. 함수에 데코레이터만 추가하면, 
모든 로그를 자동으로 추적하여 터미널에 출력합니다.

[![PyPI version](https://img.shields.io/pypi/v/pyhunt.svg)](https://pypi.org/project/pyhunt/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyhunt.svg)](https://pypi.org/project/pyhunt/)

#### [English](/README.md) | 한국어

---

https://github.com/user-attachments/assets/3d4389fe-4708-423a-812e-25f2e7200053

<img src="docs/description.png" alt="pyhunt_description" width="600"/>

</div>

## 주요 특징

- **자동 함수/메서드 호출 추적**: `@trace` 데코레이터 하나로 동기/비동기 함수, 클래스 호출 흐름을 자동 기록
- **풍부한 색상과 트리 구조 로그**: 호출 뎁스에 따른 색상 및 인덴트로 가독성 향상
- **다양한 로그 레벨 지원**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **CLI를 통한 로그 레벨 설정**: `.env` 파일에 `HUNT_LEVEL` 저장 및 관리
- **AI 워크플로우에 최적화**: AI가 생성한 코드를 손쉽게 추적할 수 있습니다.
- **예외 발생 시 상세 정보 제공**: 호출 인자, 위치, 스택트레이스 포함


## 설치 방법

### pip 을 이용해 설치
```bash
pip install pyhunt
```

### uv 를 이용해 설치
```bash
uv add pyhunt
```

## 빠른 시작

### 1. 환경변수 파일 설정 및 관리
`hunt` 명령어를 실행하여 `.env` 파일을 설정하고 관리할 수 있습니다.

```bash
hunt
```

위 명령어를 실행하면 `.env` 파일에 `HUNT_LEVEL=DEBUG`와 `ROOT_DIR`이 현재 디렉토리로 설정됩니다.


### 2. 함수 또는 클래스에 `@trace` 적용
자세한 예제는 [examples](https://github.com/pyhunt/pyhunt/tree/main/examples) 폴더를 참고하세요.


#### 기본 예제
```py
from pyhunt import trace

@trace
def test(value):
    return value
```

#### 비동기 함수
```py
@trace
async def test(value):
    return value
```

#### 클래스
```py
@trace
class MyClass:
    def first_method(self, value):
        return value

    def second_method(self, value):
        return value
```

## AI와 함께 사용

### 룰 셋업
`.cursorrules` , `.clinerules` 또는 `.roorules` 에 아래와 같이 룰을 추가합니다.
```md
<logging-rules>

**Import:** Import the decorator with `from pyhunt import trace`.
**Tracing:** Use the `@trace` decorator to automatically log function calls and execution times.
**Avoid `print()`:** Do not use the `print()` function.
**Exception Handling:** Use `try`/`except Exception as e: raise e` blocks to maintain traceback.

</logging-rules>
```

### 기존 코드베이스 수정
**"로깅 룰에 따라 코드를 수정하세요."** 라고 명령합니다.

## Logger 사용법
`logger` 방식은 중요한 부분만 일부 사용하는것을 권장합니다.  
`@trace`를 통해 대부분의 동작이 추적되며, 과도한 사용은 가독성에 영향을 끼칠 수 있습니다.  

```py
from pyhunt import logger

logger.debug("This is a debug log.")
logger.info("This is an info log.")
logger.warning("This is a warning log.")
logger.error("This is an error log.")
logger.critical("This is a critical log.")
```


## CLI 사용법

`hunt` 명령어를 사용하여 로그 레벨 및 기타 설정을 관리할 수 있습니다.

```bash
hunt [옵션]
```

### 지원 옵션

- `--debug` : DEBUG 레벨 (가장 상세)
- `--info` : INFO 레벨
- `--warning` : WARNING 레벨
- `--error` : ERROR 레벨
- `--critical` : CRITICAL 레벨
- `--root` : `ROOT_DIR` 환경 변수를 현재 디렉토리로 설정합니다.
- `--repeat <횟수>` : `HUNT_MAX_REPEAT` 환경 변수를 지정된 횟수로 설정합니다. (로그 반복 제한)

옵션 미지정 시 기본값은 `DEBUG`입니다.

### 환경 변수

`pyhunt`는 `.env` 파일을 통해 다음 환경 변수를 지원합니다.

- `HUNT_LEVEL`: 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL). 기본값은 `DEBUG`입니다.
- `HUNT_MAX_REPEAT`: 동일한 로그가 반복될 때 표시를 제한하는 횟수입니다. 기본값은 3입니다.
- `ELAPSED`: 로그에 함수 실행 시간을 표시할지 여부를 설정합니다. (`True` 또는 `False`). 기본값은 `True`입니다.
- `ROOT_DIR`: 로그 출력 시 기준 디렉토리를 설정합니다. 보다 정확하게 경로를 표시합니다.




