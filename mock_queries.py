# Mock task data — replace with real DB queries on integration day

MOCK_TASKS = [
    {
        "id": 1,
        "title": "Submit CSE299 report",
        "due_date": "2026-07-05",
        "link": "https://docs.google.com/",
        "priority": "High",
        "category": "Study",
        "completed": False,
        "subtasks": [
            "Write introduction",
            "Add diagrams",
            "Proofread",
        ],
    },
    {
        "id": 2,
        "title": "Buy groceries",
        "due_date": "2026-07-05",
        "link": "",
        "priority": "Low",
        "category": "Life",
        "completed": False,
        "subtasks": [
            "Milk",
            "Bread",
            "Eggs",
        ],
    },
    {
        "id": 3,
        "title": "Read lecture slides",
        "due_date": "2026-07-07",
        "link": "https://docs.google.com/",
        "priority": "Medium",
        "category": "Study",
        "completed": False,
        "subtasks": [
            "Chapter 1",
            "Chapter 2",
            "Chapter 3",
        ],
    },
    {
        "id": 4,
        "title": "Walk the dog",
        "due_date": "2026-07-10",
        "link": "",
        "priority": "Low",
        "category": "Health",
        "completed": False,
        "subtasks": [],
    },
    {
        "id": 5,
        "title": "Team meeting",
        "due_date": "2026-07-12",
        "link": "https://meet.google.com/",
        "priority": "High",
        "category": "Work",
        "completed": False,
        "subtasks": [
            "Prepare slides",
            "Send agenda",
        ],
    },
    {
        "id": 6,
        "title": "Pay tuition fees",
        "due_date": "2026-07-15",
        "link": "",
        "priority": "High",
        "category": "Life",
        "completed": False,
        "subtasks": [
            "Check bank balance",
            "Log into portal",
        ],
    },
]


def get_tasks_by_date(date_str):
    """
    Return all tasks matching the selected date.

    Example:
    get_tasks_by_date("2026-07-07")
    """

    return [
        task
        for task in MOCK_TASKS
        if task["due_date"] == date_str
    ]


def get_all_task_dates():
    """
    Return a list of dates that contain at least one task.
    """

    return list(
        set(
            task["due_date"]
            for task in MOCK_TASKS
        )
    )