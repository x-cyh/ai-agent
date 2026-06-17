from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Optional

from .models import StorySegment


SKIP_COMMANDS = {"skip", "略過", "跳過"}
BACK_COMMANDS = {"back", "上一題", "返回"}


@dataclass(frozen=True)
class PromptContext:
    section_title: str
    question_index: int
    total_questions_in_section: int
    global_section_index: int
    total_sections: int


@dataclass(frozen=True)
class FollowUpState:
    segment_index: int
    question_index: int
    original_answer: str
    question: str


class StoryCollector:
    """以較自然的訪談節奏，蒐集可整理成長篇故事的材料。"""

    MIN_ANSWER_LENGTH = 8

    def __init__(self) -> None:
        self.segments: List[StorySegment] = self._init_segments()
        self.current_idx = 0
        self.question_idx = 0
        self.pending_follow_up: Optional[FollowUpState] = None

    def _init_segments(self) -> List[StorySegment]:
        return [
            StorySegment(
                title="主線起點",
                questions=[
                    "如果今天只能先留下一段故事給孩子或家人，您最想從哪一件事開始說起？",
                    "那件事為什麼一直留在您心裡？如果要用一個畫面形容，它最像什麼？",
                ],
                summary_prompt="這段故事最想留下的核心事件與起點",
            ),
            StorySegment(
                title="故事背景",
                questions=[
                    "回到 {story_seed} 這件事，那時候您大約幾歲？家裡、工作或生活正在經歷什麼狀態？",
                    "如果把當時的日子拍成一個場景，周圍環境、一起生活的人、每天的節奏大概是什麼樣子？",
                ],
                summary_prompt="故事發生前的生活背景與人物關係",
            ),
            StorySegment(
                title="事件開端",
                questions=[
                    "{story_seed} 是怎麼開始的？當時出現了什麼變化、消息或契機，讓事情慢慢展開？",
                    "你還記得真正意識到『事情不一樣了』的那一天或那一刻嗎？那時發生了什麼？",
                ],
                summary_prompt="事件如何被引爆，以及最初的轉折點",
            ),
            StorySegment(
                title="最大衝突",
                questions=[
                    "在 {story_seed} 這段經歷裡，最難熬、最掙扎，或最讓您睡不著覺的是什麼？",
                    "那段時間裡，有沒有一個特別難忘的場景、對話或決定，讓您到現在還記得很清楚？",
                ],
                summary_prompt="故事中的主要衝突、壓力與情緒張力",
            ),
            StorySegment(
                title="做出決定",
                questions=[
                    "後來您做了什麼選擇？當時有哪些路擺在眼前，最後為什麼走上這一條？",
                    "做決定之前，您最怕失去什麼？又最希望守住什麼？",
                ],
                summary_prompt="關鍵抉擇背後的拉扯與判斷",
            ),
            StorySegment(
                title="結果與代價",
                questions=[
                    "後來事情怎麼發展？這個選擇帶來了哪些收穫、代價、遺憾，或意想不到的結果？",
                    "如果回頭看，那段日子改變了您和家人、工作，或看待人生的方式嗎？",
                ],
                summary_prompt="事件結果，以及留下來的代價與影響",
            ),
            StorySegment(
                title="回頭再看",
                questions=[
                    "現在回頭看 {story_seed}，您覺得它最深地改變了您什麼？",
                    "如果現在的您能回到當時，您最想對那時候的自己說一句什麼話？",
                ],
                summary_prompt="多年後的理解、成長與自我對話",
            ),
            StorySegment(
                title="留給孩子的話",
                questions=[
                    "如果要把 {story_seed} 這段故事留給孩子，您最想讓他們記住哪一個畫面、哪一份心意？",
                    "如果最後只能留下一段叮嚀，您最想對孩子或晚輩說什麼？",
                ],
                summary_prompt="寫給孩子的提醒、祝福與人生叮嚀",
            ),
        ]

    def _get_story_seed(self) -> str:
        if self.segments and self.segments[0].answers:
            seed = (self.segments[0].answers[0] or "").strip()
            if seed and seed != "_未回答_":
                return seed
        return "這段故事"

    def _get_answer(self, segment_index: int, answer_index: int, default: str = "") -> str:
        if segment_index >= len(self.segments):
            return default
        answers = self.segments[segment_index].answers
        if answer_index >= len(answers):
            return default
        answer = (answers[answer_index] or "").strip()
        if not answer or answer == "_未回答_":
            return default
        return answer

    def _coalesce(self, *values: str, default: str = "") -> str:
        for value in values:
            cleaned = (value or "").strip()
            if cleaned:
                return cleaned
        return default

    def _clean_for_prompt(self, value: str, limit: int = 28) -> str:
        cleaned = re.sub(r"\s+", " ", (value or "").strip())
        if len(cleaned) <= limit:
            return cleaned
        return f"{cleaned[:limit].rstrip()}…"

    def _answer_length(self, answer: str) -> int:
        return len(re.sub(r"\s+", "", answer or ""))

    def _should_trigger_follow_up(self, answer: str) -> bool:
        cleaned = (answer or "").strip()
        if not cleaned or cleaned == "_未回答_":
            return False
        return self._answer_length(cleaned) < self.MIN_ANSWER_LENGTH

    def _get_latest_meaningful_answer(self) -> str:
        current_segment_index = min(self.current_idx, len(self.segments) - 1)
        current_question_index = self.question_idx

        for segment_index in range(current_segment_index, -1, -1):
            answers = self.segments[segment_index].answers
            for answer_index in range(len(answers) - 1, -1, -1):
                if segment_index == current_segment_index and answer_index >= current_question_index:
                    continue
                answer = (answers[answer_index] or "").strip()
                if answer and answer != "_未回答_":
                    return answer
        return ""

    def _build_follow_up_question(self, answer: str) -> str:
        snippet = self._clean_for_prompt(answer)
        section_title = self.segments[self.current_idx].title
        prompts = {
            "主線起點": f"您剛提到「{snippet}」，我想先把這個起點抓清楚：當時最先浮現的是哪個畫面或事件？",
            "故事背景": f"關於您提到的「{snippet}」，能再補一點當時的生活狀態、身邊的人或環境嗎？",
            "事件開端": f"您剛說「{snippet}」，那件事是從哪個具體變化開始變得不一樣的？",
            "最大衝突": f"您提到「{snippet}」，能不能再說一個讓您最難受或最有壓力的畫面？",
            "做出決定": f"關於「{snippet}」，我想再追問一步：當時您是在什麼情況下下定決心的？",
            "結果與代價": f"您剛提到「{snippet}」，這之後最明顯的結果、代價或改變是什麼？",
            "回頭再看": f"關於「{snippet}」，如果再往內心走一步，您現在怎麼理解當時的自己？",
            "留給孩子的話": f"您剛說「{snippet}」，如果要讓孩子更記得住，能不能把那句話再說得具體一點？",
        }
        return prompts.get(section_title, f"您剛提到「{snippet}」，可以再多說一點具體發生了什麼嗎？")

    def _compose_answer(self, original_answer: str, follow_up_answer: str) -> str:
        original = (original_answer or "").strip()
        follow_up = (follow_up_answer or "").strip()
        if not original:
            return follow_up
        if not follow_up:
            return original
        return f"{original} 補充：{follow_up}"

    def _build_story_title(self) -> str:
        seed = self._get_story_seed()
        conflict = self._get_answer(3, 0)
        if conflict:
            return f"{seed}：在困難裡做出的選擇"
        return f"{seed}：一段想留給家人的人生故事"

    def _build_story_summary(self) -> str:
        seed = self._get_story_seed()
        background = self._coalesce(self._get_answer(1, 0), self._get_answer(1, 1), default="當時的生活正處在一個需要轉變的時刻")
        decision = self._coalesce(self._get_answer(4, 0), self._get_answer(4, 1), default="做出一個重要決定")
        result = self._coalesce(self._get_answer(5, 0), self._get_answer(5, 1), default="也因此重新理解了人生的重量")
        return f"這是一段關於「{seed}」的故事。主角在 {background} 的處境中，被推向一個必須 {decision} 的關口，最後迎來 {result}，也留下了足以對孩子訴說的人生體會。"

    def _build_long_story(self) -> str:
        seed = self._get_story_seed()
        why_this_story = self._coalesce(self._get_answer(0, 1), default="那是一段多年後仍常常想起的記憶。")
        age_and_life = self._coalesce(self._get_answer(1, 0), default="那時的人生正走在一段不算輕鬆的路上。")
        scene = self._coalesce(self._get_answer(1, 1), default="身邊的人與日常環境，都悄悄影響著後來的每一個選擇。")
        trigger = self._coalesce(self._get_answer(2, 0), default="事情並不是突然發生，而是在幾個徵兆累積後慢慢展開。")
        turning_moment = self._coalesce(self._get_answer(2, 1), default="直到某一刻，才真正明白自己已經走到必須面對改變的門口。")
        conflict = self._coalesce(self._get_answer(3, 0), default="真正難的，不只是外在局勢，而是心裡的拉扯。")
        vivid_scene = self._coalesce(self._get_answer(3, 1), default="有些畫面雖然過了很多年，回想起來仍舊清楚。")
        decision = self._coalesce(self._get_answer(4, 0), default="最後還是做出了一個無法再拖延的決定。")
        fear_and_hope = self._coalesce(self._get_answer(4, 1), default="那個決定背後，同時有害怕，也有想守住的重要東西。")
        result = self._coalesce(self._get_answer(5, 0), default="事情的結果未必完美，但人生從此往另一個方向走去。")
        impact = self._coalesce(self._get_answer(5, 1), default="這段經歷也悄悄改變了看待家人、工作與人生的方式。")
        reflection = self._coalesce(self._get_answer(6, 0), default="多年後回頭看，才知道那不是單純的一次遭遇，而是一場塑造自己的過程。")
        self_message = self._coalesce(self._get_answer(6, 1), default="如果能對當時的自己說話，大概會想提醒自己再相信一次、再撐一下。")
        child_memory = self._coalesce(self._get_answer(7, 0), default="最希望孩子記住的，不是表面的成敗，而是面對人生時不輕易放棄的樣子。")
        child_message = self._coalesce(self._get_answer(7, 1), default="願你在人生重要關頭，仍願意守住善良、責任與勇氣。")

        paragraphs = [
            f"說起「{seed}」，那不是一段可以輕輕帶過的小事，而是在人生裡留下一道深刻痕跡的經歷。{why_this_story}",
            f"故事發生的時候，{age_and_life}。{scene}。在那樣的日子裡，人往往以為生活會照舊前進，卻不知道有些改變正在慢慢逼近。",
            f"後來，{trigger}。{turning_moment}。很多故事真正的開始，都不是熱鬧的開場，而是一個人忽然意識到：從這裡開始，自己再也回不到原來的心境。",
            f"最辛苦的部分，是 {conflict}。{vivid_scene}。那種壓力不一定每個人都看得見，但當事人心裡知道，自己正站在一個不能逃、也不能假裝沒事的地方。",
            f"在反覆思量之後，{decision}。因為 {fear_and_hope}。很多重要決定之所以沉重，正是因為它不只是選擇一條路，而是同時承擔那條路可能帶來的一切。",
            f"再往後看，{result}。{impact}。人生裡有些代價當下不一定看得清楚，但時間一久，就會明白每一步其實都在重寫自己和家人的命運。",
            f"如今再回頭看，{reflection}。{self_message}。真正留下來的，往往不是當時受了多少苦，而是經過那段路之後，終於知道自己是怎樣的人，也知道什麼才值得用一生去守住。",
            f"如果這段故事要留給孩子，最想留下的是這一句：{child_memory}。而真正想說出口的叮嚀則是：{child_message}",
        ]
        return "\n\n".join(paragraphs)

    def assemble_story_markdown(self) -> str:
        title = self._build_story_title()
        summary = self._build_story_summary()
        story_body = self._build_long_story()
        child_words = self._coalesce(self._get_answer(7, 1), self._get_answer(7, 0), default="願你在人生每個關口，都能保有溫柔與勇氣。")

        lines = [
            f"# {title}",
            "",
            "## 主線摘要",
            "",
            summary,
            "",
            "## 故事正文",
            "",
            story_body,
            "",
            "## 留給孩子的話",
            "",
            child_words,
            "",
        ]
        return "\n".join(lines).strip() + "\n"

    def _render_question(self, template: str) -> str:
        return template.format(story_seed=self._get_story_seed())

    def _render_dynamic_question(self, template: str) -> str:
        question = self._render_question(template)
        previous_answer = self._get_latest_meaningful_answer()
        if not previous_answer:
            return question

        snippet = self._clean_for_prompt(previous_answer)
        if self.question_idx > 0:
            return f"接著剛剛您提到「{snippet}」，{question}"
        if self.current_idx > 0:
            return f"順著您剛才說的「{snippet}」，{question}"
        return question

    def _advance_position(self) -> None:
        segment = self.segments[self.current_idx]
        if self.question_idx + 1 < len(segment.questions):
            self.question_idx += 1
            return

        self.current_idx += 1
        self.question_idx = 0

    def is_finished(self) -> bool:
        return self.current_idx >= len(self.segments)

    def can_go_back(self) -> bool:
        return self.current_idx > 0 or self.question_idx > 0

    def get_prompt_context(self) -> PromptContext:
        segment = self.segments[self.current_idx]
        return PromptContext(
            section_title=segment.title,
            question_index=self.question_idx + 1,
            total_questions_in_section=len(segment.questions),
            global_section_index=self.current_idx + 1,
            total_sections=len(self.segments),
        )

    def get_current_question(self) -> str:
        if self.is_finished():
            raise IndexError("所有問題都已完成")
        if self.pending_follow_up is not None:
            return self.pending_follow_up.question
        segment = self.segments[self.current_idx]
        return self._render_dynamic_question(segment.questions[self.question_idx])

    def handle_input(self, user_input: str) -> str:
        normalized = user_input.strip().lower()
        if normalized in SKIP_COMMANDS:
            if self.pending_follow_up is not None:
                self.pending_follow_up = None
                self._advance_position()
                return "已略過補充，先依目前內容記錄。"
            self.submit_answer("_未回答_")
            return "已略過此題。"
        if normalized in BACK_COMMANDS:
            self.go_back()
            return "已回到前一題。"
        answer = user_input.strip()

        if self.pending_follow_up is not None:
            segment = self.segments[self.current_idx]
            merged_answer = self._compose_answer(self.pending_follow_up.original_answer, answer)
            segment.replace_last_answer(merged_answer)
            self.pending_follow_up = None
            self._advance_position()
            return "已補充並記錄。"

        segment = self.segments[self.current_idx]
        segment.add_answer(answer)

        if self._should_trigger_follow_up(answer):
            self.pending_follow_up = FollowUpState(
                segment_index=self.current_idx,
                question_index=self.question_idx,
                original_answer=answer,
                question=self._build_follow_up_question(answer),
            )
            return "已先記下，想再多了解一點。"

        self._advance_position()
        return "已記錄。"

    def submit_answer(self, answer: str) -> None:
        if self.is_finished():
            raise IndexError("所有問題都已完成，無法再提交答案")

        segment = self.segments[self.current_idx]
        segment.add_answer(answer)
        self.pending_follow_up = None
        self._advance_position()

    def go_back(self) -> None:
        if not self.can_go_back():
            raise IndexError("目前已經是第一題，無法返回")

        if self.pending_follow_up is not None:
            current_segment = self.segments[self.current_idx]
            if current_segment.answers:
                current_segment.answers.pop()
            self.pending_follow_up = None
            return

        if self.question_idx > 0:
            self.question_idx -= 1
            current_segment = self.segments[self.current_idx]
            if current_segment.answers:
                current_segment.answers.pop()
            return

        previous_segment = self.segments[self.current_idx - 1]
        if previous_segment.answers:
            previous_segment.answers.pop()
        return

    def assemble_markdown(self) -> str:
        lines: List[str] = [
            self.assemble_story_markdown().rstrip(),
            "",
            "---",
            "",
            "## 訪談紀錄",
            "",
            f"> 主線：{self._get_story_seed()}",
            "",
        ]
        for segment in self.segments:
            lines.append(f"## {segment.title}")
            lines.append("")
            for question_index, question in enumerate(segment.questions):
                answer = "_未回答_"
                if question_index < len(segment.answers):
                    answer = segment.answers[question_index] or "_未回答_"
                lines.append(f"**問**：{self._render_question(question)}")
                lines.append(f"**答**：{answer}")
                lines.append("")
        return "\n".join(lines).strip() + "\n"

    def save_markdown(self, output_path: Optional[str | Path] = None) -> Path:
        markdown = self.assemble_markdown()
        if output_path is None:
            output_dir = Path.cwd() / "story_outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / self._build_output_filename()
        else:
            candidate = Path(output_path)
            if candidate.suffix.lower() != ".md":
                candidate.mkdir(parents=True, exist_ok=True)
                output_file = candidate / self._build_output_filename()
            else:
                candidate.parent.mkdir(parents=True, exist_ok=True)
                output_file = candidate

        output_file.write_text(markdown, encoding="utf-8")
        return output_file

    def _build_output_filename(self) -> str:
        seed = self._get_story_seed()
        cleaned = re.sub(r"[\\/:*?\"<>|]+", "-", seed).strip()
        cleaned = re.sub(r"\s+", "_", cleaned)
        cleaned = cleaned.strip("._-") or "parent_story"
        cleaned = cleaned[:40]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{cleaned}.md"


def run_cli() -> str:
    """以命令列互動方式收集故事，並回傳 Markdown。"""
    collector = StoryCollector()

    print("歡迎使用父母故事拼湊工具。")
    print("輸入內容後按 Enter。可輸入：跳過 / 上一題")
    print()

    while not collector.is_finished():
        context = collector.get_prompt_context()
        print(
            f"[{context.global_section_index}/{context.total_sections}] "
            f"{context.section_title} - 題目 {context.question_index}/{context.total_questions_in_section}"
        )
        print(collector.get_current_question())
        user_input = input("> ").strip()

        try:
            message = collector.handle_input(user_input)
            print(message)
        except IndexError as exc:
            print(f"操作失敗：{exc}")
        print()

    markdown = collector.assemble_markdown()
    output_file = collector.save_markdown()
    print("全部完成，以下是整理好的 Markdown：")
    print()
    print(markdown)
    print(f"故事已自動存檔：{output_file}")
    return markdown


if __name__ == "__main__":
    run_cli()