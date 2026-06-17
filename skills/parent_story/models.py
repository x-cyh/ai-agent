from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StorySegment:
    """儲存單一主題的問題與答案。"""

    title: str
    questions: List[str]
    summary_prompt: str = ""
    answers: List[Optional[str]] = field(default_factory=list)

    def add_answer(self, answer: str) -> None:
        self.answers.append(answer)

    def replace_last_answer(self, answer: str) -> None:
        if not self.answers:
            raise IndexError("目前沒有可覆寫的答案")
        self.answers[-1] = answer

    def is_complete(self) -> bool:
        return len(self.answers) >= len(self.questions)