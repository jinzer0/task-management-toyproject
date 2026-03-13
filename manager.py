"""
manager.py - 비즈니스 로직 및 유효성 검사 모듈

태스크의 CRUD 연산, 입력 유효성 검사, 정렬 조회 로직을 담당한다.
모든 사용자 입력은 이 모듈을 거쳐 검증되며, 부적절한 입력에 대해
적절한 커스텀 예외를 raise하여 호출자(main.py)가 처리하도록 한다.
"""

from datetime import datetime, date

from models import (
    Task,
    VALID_PRIORITIES,
    InvalidDateError,
    InvalidPriorityError,
    InvalidInputError,
    DuplicateTitleError,
    TaskNotFoundError,
)
from storage import load_tasks, save_tasks


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class TaskManager:
    """
    태스크 관리의 핵심 비즈니스 로직을 캡슐화하는 클래스.

    파라미터:
        file_path -- 데이터 파일 경로 (문자열), None이면 storage 기본값 사용

    내부 상태:
        _tasks    -- 현재 메모리에 로드된 Task 인스턴스 리스트
        _file_path -- 데이터 파일 경로
    """

    def __init__(self, file_path=None):
        self._file_path = file_path
        self._tasks = load_tasks(self._file_path)

    def _save(self):
        """내부 태스크 목록을 파일에 저장한다."""
        save_tasks(self._tasks, self._file_path)

    def _next_id(self):
        """다음 사용할 태스크 ID를 계산한다 (현재 최대 ID + 1)."""
        if not self._tasks:
            return 1
        return max(task.id for task in self._tasks) + 1

    def _find_task(self, task_id):
        """
        ID로 태스크를 검색한다.

        파라미터:
            task_id -- 검색할 태스크 ID (정수)

        반환값:
            Task -- 해당 ID의 Task 인스턴스

        발생 예외:
            TaskNotFoundError -- 해당 ID의 태스크가 존재하지 않을 때
        """
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise TaskNotFoundError(
            "[검색 실패] ID '{}'에 해당하는 태스크를 찾을 수 없습니다.".format(task_id)
        )

    def validate_title(self, title, exclude_id=None):
        """
        태스크 제목의 유효성을 검사한다.

        파라미터:
            title      -- 검사할 제목 문자열
            exclude_id -- 중복 검사 시 제외할 태스크 ID (수정 시 자기 자신 제외용)

        발생 예외:
            InvalidInputError    -- 빈 문자열이거나 공백만 포함된 경우
            DuplicateTitleError  -- 동일 제목의 태스크가 이미 존재하는 경우
        """
        if not title or not title.strip():
            raise InvalidInputError("[입력 오류] 제목은 비어있을 수 없습니다.")

        for task in self._tasks:
            if task.title == title.strip() and task.id != exclude_id:
                raise DuplicateTitleError(
                    "[중복 오류] '{}'이라는 제목의 태스크가 이미 존재합니다.".format(title.strip())
                )

    def validate_priority(self, priority):
        """
        우선순위 값의 유효성을 검사한다.

        파라미터:
            priority -- 검사할 우선순위 문자열

        발생 예외:
            InvalidPriorityError -- 허용 값(high/medium/low) 외의 값 입력 시
        """
        if priority not in VALID_PRIORITIES:
            raise InvalidPriorityError(
                "[입력 오류] 우선순위는 {} 중 하나여야 합니다. (입력값: '{}')".format(
                    ", ".join(VALID_PRIORITIES), priority
                )
            )

    def validate_deadline(self, deadline_str):
        """
        마감일 문자열의 유효성을 검사한다.

        파라미터:
            deadline_str -- 검사할 날짜 문자열 (YYYY-MM-DD 형식 기대)

        반환값:
            str -- 검증 완료된 날짜 문자열

        발생 예외:
            InvalidDateError -- 형식 불일치, 존재하지 않는 날짜, 또는 과거 날짜 입력 시
        """
        try:
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except ValueError:
            raise InvalidDateError(
                "[날짜 오류] '{}' 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.".format(
                    deadline_str
                )
            )

        if deadline_date < date.today():
            raise InvalidDateError(
                "[날짜 오류] 마감일 '{}'은 과거 날짜입니다. 오늘({}) 이후 날짜를 입력해주세요.".format(
                    deadline_str, date.today().isoformat()
                )
            )

        return deadline_str

    def validate_task_id_input(self, raw_input):
        """
        사용자로부터 입력받은 태스크 ID 문자열을 검증하고 정수로 변환한다.

        파라미터:
            raw_input -- 사용자 입력 문자열

        반환값:
            int -- 변환된 정수 ID

        발생 예외:
            InvalidInputError -- 숫자가 아닌 값 입력 시
        """
        try:
            return int(raw_input)
        except (ValueError, TypeError):
            raise InvalidInputError(
                "[입력 오류] 태스크 ID는 숫자여야 합니다. (입력값: '{}')".format(raw_input)
            )

    def add_task(self, title, priority, deadline):
        """
        새로운 태스크를 추가한다.

        파라미터:
            title    -- 태스크 제목 (문자열)
            priority -- 우선순위 ("high", "medium", "low")
            deadline -- 마감일 ("YYYY-MM-DD" 형식)

        반환값:
            Task -- 생성된 Task 인스턴스

        발생 예외:
            InvalidInputError   -- 빈 제목 입력 시
            DuplicateTitleError -- 중복 제목 시
            InvalidPriorityError -- 잘못된 우선순위 시
            InvalidDateError    -- 잘못된 날짜 시
        """
        title = title.strip()
        self.validate_title(title)
        self.validate_priority(priority)
        self.validate_deadline(deadline)

        new_task = Task(
            task_id=self._next_id(),
            title=title,
            priority=priority,
            deadline=deadline,
        )
        self._tasks.append(new_task)
        self._save()
        return new_task

    def update_task(self, task_id, title=None, priority=None, deadline=None):
        """
        기존 태스크를 부분 수정한다. None이 아닌 필드만 갱신된다.

        파라미터:
            task_id  -- 수정할 태스크 ID (정수)
            title    -- 새 제목 (문자열 또는 None)
            priority -- 새 우선순위 (문자열 또는 None)
            deadline -- 새 마감일 (문자열 또는 None)

        반환값:
            Task -- 수정된 Task 인스턴스

        발생 예외:
            TaskNotFoundError    -- 해당 ID가 존재하지 않을 때
            InvalidInputError    -- 빈 제목 입력 시
            DuplicateTitleError  -- 중복 제목 시
            InvalidPriorityError -- 잘못된 우선순위 시
            InvalidDateError     -- 잘못된 날짜 시
        """
        task = self._find_task(task_id)

        if title is not None:
            title = title.strip()
            self.validate_title(title, exclude_id=task_id)
            task.title = title

        if priority is not None:
            self.validate_priority(priority)
            task.priority = priority

        if deadline is not None:
            self.validate_deadline(deadline)
            task.deadline = deadline

        self._save()
        return task

    def delete_task(self, task_id):
        """
        태스크를 삭제한다.

        파라미터:
            task_id -- 삭제할 태스크 ID (정수)

        반환값:
            Task -- 삭제된 Task 인스턴스

        발생 예외:
            TaskNotFoundError -- 해당 ID가 존재하지 않을 때
        """
        task = self._find_task(task_id)
        self._tasks.remove(task)
        self._save()
        return task

    def toggle_task(self, task_id):
        """
        태스크 상태를 토글한다 (pending ↔ done).

        파라미터:
            task_id -- 토글할 태스크 ID (정수)

        반환값:
            Task -- 상태가 변경된 Task 인스턴스

        발생 예외:
            TaskNotFoundError -- 해당 ID가 존재하지 않을 때
        """
        task = self._find_task(task_id)
        task.toggle_status()
        self._save()
        return task

    def list_all(self):
        """
        전체 태스크 목록을 ID 순으로 반환한다.

        반환값:
            list -- Task 인스턴스들의 리스트 (ID 오름차순)
        """
        return sorted(self._tasks, key=lambda t: t.id)

    def list_by_priority(self):
        """
        우선순위별 정렬된 태스크 목록을 반환한다 (High > Medium > Low).

        반환값:
            list -- Task 인스턴스들의 리스트 (우선순위 내림차순 → ID 오름차순)
        """
        return sorted(
            self._tasks,
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.id),
        )

    def list_by_deadline(self):
        """
        마감일 임박순으로 정렬된 태스크 목록을 반환한다.
        각 태스크에 경과 여부 정보를 포함하여 (task, is_overdue) 튜플로 반환한다.

        반환값:
            list -- (Task, bool) 튜플의 리스트
                    bool은 마감일 경과 여부 (True면 경과)
        """
        today = date.today()
        result = []
        for task in self._tasks:
            try:
                dl = datetime.strptime(task.deadline, "%Y-%m-%d").date()
                is_overdue = dl < today
            except ValueError:
                is_overdue = False
                dl = date.max
            result.append((task, is_overdue, dl))

        result.sort(key=lambda x: (x[2], x[0].id))
        return [(item[0], item[1]) for item in result]
