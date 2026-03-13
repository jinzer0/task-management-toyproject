"""
main.py - CLI 인터페이스 및 메인 루프 모듈

사용자와의 모든 상호작용을 담당한다.
표준 print()와 input()만을 사용하며, 모든 예외를 최상위에서 캐치하여
프로그램 종료 없이 에러 메시지를 출력한 뒤 메뉴로 복귀한다.
"""

import os
import platform
from models import TaskError
from manager import TaskManager

def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")


def pause():
    input("\n  [Enter] 키를 눌러 메뉴로 돌아가기...")

MENU_TEXT = """
========================================
     태스크 마감일 관리 시스템 (RTDM)
========================================
  1. 태스크 추가
  2. 태스크 수정
  3. 태스크 삭제
  4. 상태 변경 (완료/미완료 토글)
  5. 전체 목록 보기
  6. 우선순위별 조회
  7. 마감일 임박순 조회
  0. 종료
========================================"""

PRIORITY_LABEL = {"high": "높음", "medium": "보통", "low": "낮음"}
STATUS_LABEL = {"pending": "미완료", "done": "완료"}


def print_task_row(task):
    """
    단일 태스크를 포맷팅하여 한 줄로 출력한다.

    파라미터:
        task -- 출력할 Task 인스턴스
    """
    print("  [{id}] {title}  | 우선순위: {priority}  | 마감일: {deadline}  | 상태: {status}".format(
        id=task.id,
        title=task.title,
        priority=PRIORITY_LABEL.get(task.priority, task.priority),
        deadline=task.deadline,
        status=STATUS_LABEL.get(task.status, task.status),
    ))


def print_task_table(tasks):
    """
    태스크 목록을 테이블 형태로 출력한다. 비어있으면 안내 메시지를 출력한다.

    파라미터:
        tasks -- Task 인스턴스들의 리스트
    """
    if not tasks:
        print("\n  등록된 태스크가 없습니다.")
        return
    print()
    for task in tasks:
        print_task_row(task)
    print()


def handle_add(mgr):
    """
    태스크 추가 핸들러. 사용자로부터 제목, 우선순위, 마감일을 입력받아 태스크를 생성한다.

    파라미터:
        mgr -- TaskManager 인스턴스
    """
    print("\n--- 태스크 추가 ---")
    title = input("  제목: ")
    priority = input("  우선순위 (high/medium/low): ").strip().lower()
    deadline = input("  마감일 (YYYY-MM-DD): ").strip()

    task = mgr.add_task(title, priority, deadline)
    print("\n  태스크가 추가되었습니다.")
    print_task_row(task)
    pause()


def handle_update(mgr):
    """
    태스크 수정 핸들러. 부분 수정을 지원하며, 빈 입력은 기존 값을 유지한다.

    파라미터:
        mgr -- TaskManager 인스턴스
    """
    print("\n--- 태스크 수정 ---")
    raw_id = input("  수정할 태스크 ID: ").strip()
    task_id = mgr.validate_task_id_input(raw_id)

    print("  (변경하지 않을 항목은 Enter를 누르세요)")
    title = input("  새 제목: ").strip() or None
    priority_input = input("  새 우선순위 (high/medium/low): ").strip().lower()
    priority = priority_input if priority_input else None
    deadline = input("  새 마감일 (YYYY-MM-DD): ").strip() or None

    task = mgr.update_task(task_id, title=title, priority=priority, deadline=deadline)
    print("\n  태스크가 수정되었습니다.")
    print_task_row(task)
    pause()


def handle_delete(mgr):
    """
    태스크 삭제 핸들러. 삭제 전 확인 절차를 거친다.

    파라미터:
        mgr -- TaskManager 인스턴스
    """
    print("\n--- 태스크 삭제 ---")
    raw_id = input("  삭제할 태스크 ID: ").strip()
    task_id = mgr.validate_task_id_input(raw_id)

    confirm = input("  정말 삭제하시겠습니까? (y/n): ").strip().lower()
    if confirm != "y":
        print("  삭제가 취소되었습니다.")
        pause()
        return

    task = mgr.delete_task(task_id)
    print("\n  태스크 [{}] '{}'이(가) 삭제되었습니다.".format(task.id, task.title))
    pause()


def handle_toggle(mgr):
    """
    상태 토글 핸들러. pending ↔ done 상태를 전환한다.

    파라미터:
        mgr -- TaskManager 인스턴스
    """
    print("\n--- 상태 변경 ---")
    raw_id = input("  상태를 변경할 태스크 ID: ").strip()
    task_id = mgr.validate_task_id_input(raw_id)

    task = mgr.toggle_task(task_id)
    print("\n  태스크 [{}] 상태가 '{}'(으)로 변경되었습니다.".format(
        task.id, STATUS_LABEL.get(task.status, task.status)
    ))
    pause()


def handle_list_all(mgr):
    """
    전체 목록 조회 핸들러.

    파라미터:
        mgr -- TaskManager 인스턴스
    """
    print("\n--- 전체 태스크 목록 ---")
    print_task_table(mgr.list_all())
    pause()


def handle_list_by_priority(mgr):
    """
    우선순위별 조회 핸들러. High > Medium > Low 순으로 정렬하여 출력한다.

    파라미터:
        mgr -- TaskManager 인스턴스
    """
    print("\n--- 우선순위별 태스크 목록 ---")
    print_task_table(mgr.list_by_priority())
    pause()


def handle_list_by_deadline(mgr):
    """
    마감일 임박순 조회 핸들러. 경과된 마감일에는 [기한 경과] 표시를 추가한다.

    파라미터:
        mgr -- TaskManager 인스턴스
    """
    print("\n--- 마감일 임박순 태스크 목록 ---")
    items = mgr.list_by_deadline()
    if not items:
        print("\n  등록된 태스크가 없습니다.")
        pause()
        return
    print()
    for task, is_overdue in items:
        overdue_mark = " [기한 경과]" if is_overdue else ""
        print("  [{id}] {title}  | 우선순위: {priority}  | 마감일: {deadline}{overdue}  | 상태: {status}".format(
            id=task.id,
            title=task.title,
            priority=PRIORITY_LABEL.get(task.priority, task.priority),
            deadline=task.deadline,
            overdue=overdue_mark,
            status=STATUS_LABEL.get(task.status, task.status),
        ))
    print()
    pause()


MENU_HANDLERS = {
    "1": handle_add,
    "2": handle_update,
    "3": handle_delete,
    "4": handle_toggle,
    "5": handle_list_all,
    "6": handle_list_by_priority,
    "7": handle_list_by_deadline,
}


def main():
    """
    메인 실행 함수. CLI 메뉴 루프를 구동한다.

    모든 TaskError 계열 예외를 캐치하여 에러 메시지 출력 후 메뉴로 복귀하며,
    예상치 못한 예외(Exception)도 캐치하여 시스템 중단을 방지한다.
    KeyboardInterrupt(Ctrl+C)는 정상 종료로 처리한다.
    """
    print("\n  시스템을 초기화하는 중...")
    try:
        mgr = TaskManager()
    except TaskError as e:
        print("\n  [초기화 오류] {}".format(e))
        print("  데이터 파일을 확인한 뒤 다시 시도해주세요.")
        return
    except Exception as e:
        print("\n  [치명적 오류] 예상치 못한 오류가 발생했습니다: {}".format(e))
        return

    print("  초기화 완료. 등록된 태스크: {}개".format(len(mgr.list_all())))

    while True:
        try:
            clear_screen()
            print(MENU_TEXT)
            choice = input("\n  메뉴 선택: ").strip()

            if choice == "0":
                print("\n  프로그램을 종료합니다. 감사합니다!")
                break

            handler = MENU_HANDLERS.get(choice)
            if handler is None:
                print("\n  [입력 오류] 올바른 메뉴 번호(0~7)를 입력해주세요.")
                pause()
                continue

            handler(mgr)

        except TaskError as e:
            print("\n  [오류] {}".format(e))
            pause()

        except KeyboardInterrupt:
            print("\n\n  프로그램을 종료합니다. 감사합니다!")
            break

        except Exception as e:
            print("\n  [시스템 오류] 예상치 못한 오류가 발생했습니다: {}".format(e))
            pause()


if __name__ == "__main__":
    main()
