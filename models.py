"""
models.py - 데이터 구조 및 커스텀 예외 정의 모듈

Robust Task Deadline Manager(RTDM)의 핵심 데이터 모델인 Task 클래스와
계층적 커스텀 예외 클래스들을 정의한다.

예외 계층:
    TaskError (기본)
    ├── InvalidDateError        — 날짜 형식 오류, 과거 날짜 입력
    ├── InvalidPriorityError    — 허용되지 않은 우선순위 값
    ├── InvalidInputError       — 빈 값, 잘못된 타입 입력
    ├── DuplicateTitleError     — 중복 제목 입력
    ├── TaskNotFoundError       — 존재하지 않는 ID 접근
    ├── DataCorruptionError     — JSON 디코딩 실패, 스키마 불일치
    └── StorageError            — 파일 권한 부족, I/O 실패
"""

from datetime import datetime


class TaskError(Exception):
    """
    RTDM 프로젝트의 모든 커스텀 예외의 기본 클래스.

    모든 비즈니스 로직 및 I/O 관련 예외는 이 클래스를 상속하여
    main.py에서 일괄적으로 캐치할 수 있도록 한다.
    """
    pass


class InvalidDateError(TaskError):
    """
    날짜 관련 유효성 검사 실패 시 발생하는 예외.

    발생 조건:
        - YYYY-MM-DD 형식이 아닌 문자열 입력
        - 존재하지 않는 날짜 입력 (예: 2024-02-30)
        - 과거 날짜 입력 (오늘 이전)
    """
    pass


class InvalidPriorityError(TaskError):
    """
    우선순위 값이 허용 범위를 벗어날 때 발생하는 예외.

    허용 값: "high", "medium", "low"
    """
    pass


class InvalidInputError(TaskError):
    """
    일반적인 입력 유효성 검사 실패 시 발생하는 예외.

    발생 조건:
        - 빈 문자열 입력
        - 숫자가 필요한 곳에 문자 입력
        - 기타 형식 불일치
    """
    pass


class DuplicateTitleError(TaskError):
    """
    이미 존재하는 제목으로 태스크를 생성하려 할 때 발생하는 예외.

    발생 조건:
        - 동일한 title을 가진 태스크가 이미 존재
    """
    pass


class TaskNotFoundError(TaskError):
    """
    존재하지 않는 태스크 ID에 접근할 때 발생하는 예외.

    발생 조건:
        - 수정, 삭제, 상태 변경 시 해당 ID가 데이터에 없음
    """
    pass


class DataCorruptionError(TaskError):
    """
    저장된 데이터가 손상되었을 때 발생하는 예외.

    발생 조건:
        - JSON 디코딩 실패
        - 필수 필드 누락
        - 데이터 스키마 불일치
    """
    pass


class StorageError(TaskError):
    """
    파일 시스템 관련 오류 시 발생하는 예외.

    발생 조건:
        - 파일 읽기/쓰기 권한 부족
        - 디스크 공간 부족
        - 기타 OS 레벨 I/O 오류
    """
    pass


VALID_PRIORITIES = ("high", "medium", "low")
VALID_STATUSES = ("pending", "done")


class Task:
    """
    단일 태스크를 표현하는 데이터 모델 클래스.

    속성:
        id          -- 태스크 고유 식별자 (정수, 자동 증가)
        title       -- 태스크 제목 (비어있지 않은 문자열)
        priority    -- 우선순위 ("high", "medium", "low")
        deadline    -- 마감일 (YYYY-MM-DD 문자열)
        status      -- 상태 ("pending", "done")
        created_at  -- 생성 시각 (ISO 형식 문자열)

    메서드:
        to_dict()           -- 딕셔너리로 변환
        from_dict(data)     -- 딕셔너리로부터 Task 인스턴스 생성 (클래스 메서드)
        toggle_status()     -- 상태 토글 (pending ↔ done)
    """

    def __init__(self, task_id, title, priority, deadline, status="pending", created_at=None):
        """
        Task 인스턴스를 초기화한다.

        파라미터:
            task_id     -- 태스크 고유 ID (정수)
            title       -- 태스크 제목 (문자열)
            priority    -- 우선순위 ("high", "medium", "low")
            deadline    -- 마감일 ("YYYY-MM-DD" 형식 문자열)
            status      -- 상태 ("pending" 또는 "done"), 기본값 "pending"
            created_at  -- 생성 시각 (ISO 문자열), None이면 현재 시각 자동 설정

        발생 예외:
            없음 (유효성 검사는 manager.py에서 수행)
        """
        self.id = task_id
        self.title = title
        self.priority = priority
        self.deadline = deadline
        self.status = status
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self):
        """
        Task 인스턴스를 JSON 직렬화 가능한 딕셔너리로 변환한다.

        반환값:
            dict -- 태스크의 모든 속성을 포함하는 딕셔너리
        """
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "deadline": self.deadline,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """
        딕셔너리로부터 Task 인스턴스를 생성한다.

        파라미터:
            data -- 태스크 데이터를 담은 딕셔너리
                    필수 키: "id", "title", "priority", "deadline"
                    선택 키: "status" (기본값 "pending"), "created_at" (기본값 현재 시각)

        반환값:
            Task -- 새로 생성된 Task 인스턴스

        발생 예외:
            DataCorruptionError -- 필수 키가 누락된 경우
        """
        required_keys = ("id", "title", "priority", "deadline")
        for key in required_keys:
            if key not in data:
                raise DataCorruptionError(
                    "[데이터 손상] 태스크 데이터에 필수 필드 '{}'가 누락되었습니다.".format(key)
                )
        return cls(
            task_id=data["id"],
            title=data["title"],
            priority=data["priority"],
            deadline=data["deadline"],
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
        )

    def toggle_status(self):
        """
        태스크 상태를 토글한다 (pending ↔ done).

        반환값:
            str -- 변경 후의 상태 문자열
        """
        if self.status == "pending":
            self.status = "done"
        else:
            self.status = "pending"
        return self.status

    def __repr__(self):
        return "Task(id={}, title='{}', priority='{}', deadline='{}', status='{}')".format(
            self.id, self.title, self.priority, self.deadline, self.status
        )
