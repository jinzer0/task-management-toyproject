"""
storage.py - 파일 I/O 및 직렬화 모듈

JSON 형식의 .txt 파일을 통한 데이터 영속화를 담당한다.
원자적 쓰기(tempfile → rename)를 통해 데이터 무결성을 보장하며,
파일 부재 시 자동 생성, 손상 파일 감지 등의 방어 로직을 포함한다.
"""

import json
import os
import tempfile

from models import Task, DataCorruptionError, StorageError

DEFAULT_FILE_PATH = "tasks_data.txt"


def load_tasks(file_path=None):
    """
    파일에서 태스크 목록을 로드한다.

    파라미터:
        file_path -- 데이터 파일 경로 (문자열), None이면 기본 경로 사용

    반환값:
        list -- Task 인스턴스들의 리스트

    발생 예외:
        DataCorruptionError -- JSON 파싱 실패 또는 데이터 구조 불일치
        StorageError        -- 파일 읽기 권한 부족 등 I/O 오류
    """
    if file_path is None:
        file_path = DEFAULT_FILE_PATH

    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except PermissionError:
        raise StorageError(
            "[저장소 오류] '{}' 파일을 읽을 권한이 없습니다.".format(file_path)
        )
    except OSError as e:
        raise StorageError(
            "[저장소 오류] 파일 읽기 중 오류가 발생했습니다: {}".format(e)
        )

    if not content:
        return []

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as e:
        raise DataCorruptionError(
            "[데이터 손상] '{}' 파일의 JSON 파싱에 실패했습니다: {}".format(file_path, e)
        )

    if not isinstance(raw_data, list):
        raise DataCorruptionError(
            "[데이터 손상] 최상위 데이터가 리스트 형식이 아닙니다."
        )

    tasks = []
    for idx, item in enumerate(raw_data):
        if not isinstance(item, dict):
            raise DataCorruptionError(
                "[데이터 손상] {}번째 항목이 딕셔너리 형식이 아닙니다.".format(idx + 1)
            )
        tasks.append(Task.from_dict(item))

    return tasks


def save_tasks(tasks, file_path=None):
    """
    태스크 목록을 파일에 원자적으로 저장한다.

    임시 파일에 먼저 쓴 뒤, os.replace()를 통해 원본 파일을 대체하여
    쓰기 도중 프로세스가 중단되더라도 데이터가 손상되지 않도록 보장한다.

    파라미터:
        tasks     -- Task 인스턴스들의 리스트
        file_path -- 데이터 파일 경로 (문자열), None이면 기본 경로 사용

    반환값:
        없음

    발생 예외:
        StorageError -- 파일 쓰기 권한 부족, 디스크 공간 부족 등 I/O 오류
    """
    if file_path is None:
        file_path = DEFAULT_FILE_PATH

    data = [task.to_dict() for task in tasks]
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    target_dir = os.path.dirname(os.path.abspath(file_path))

    try:
        fd, tmp_path = tempfile.mkstemp(dir=target_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                tmp_f.write(json_str)
            os.replace(tmp_path, file_path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    except PermissionError:
        raise StorageError(
            "[저장소 오류] '{}' 파일에 쓸 권한이 없습니다.".format(file_path)
        )
    except OSError as e:
        raise StorageError(
            "[저장소 오류] 파일 저장 중 오류가 발생했습니다: {}".format(e)
        )
