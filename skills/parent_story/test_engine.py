import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from .engine import StoryCollector, run_cli


class TestStoryCollector(unittest.TestCase):
    def setUp(self) -> None:
        self.collector = StoryCollector()

    def test_question_sequence(self) -> None:
        expected_titles = [
            "主線起點",
            "故事背景",
            "事件開端",
            "最大衝突",
            "做出決定",
            "結果與代價",
            "回頭再看",
            "留給孩子的話",
        ]
        for title in expected_titles:
            segment = self.collector.segments[self.collector.current_idx]
            self.assertEqual(segment.title, title)
            for _ in segment.questions:
                question = self.collector.get_current_question()
                self.assertIsInstance(question, str)
                self.collector.submit_answer("測試答案內容")
        self.assertTrue(self.collector.is_finished())

    def test_each_segment_has_multiple_questions(self) -> None:
        for segment in self.collector.segments:
            self.assertGreaterEqual(len(segment.questions), 2)

    def test_go_back_removes_last_answer(self) -> None:
        first_question = self.collector.get_current_question()
        self.assertIsInstance(first_question, str)
        self.collector.submit_answer("答案一內容")
        self.collector.submit_answer("答案二內容")

        self.collector.go_back()

        self.assertEqual(self.collector.current_idx, 1)
        self.assertEqual(self.collector.question_idx, 0)
        self.assertEqual(self.collector.segments[0].answers, ["答案一內容"])
        self.assertEqual(self.collector.segments[1].answers, [])

    def test_handle_input_skip(self) -> None:
        result = self.collector.handle_input("跳過")
        self.assertEqual(result, "已略過此題。")
        self.assertEqual(self.collector.segments[0].answers[0], "_未回答_")

    def test_short_answer_triggers_follow_up(self) -> None:
        result = self.collector.handle_input("有")

        self.assertEqual(result, "已先記下，想再多了解一點。")
        self.assertIsNotNone(self.collector.pending_follow_up)
        self.assertIn("您剛提到", self.collector.get_current_question())
        self.assertEqual(self.collector.current_idx, 0)
        self.assertEqual(self.collector.question_idx, 0)

    def test_follow_up_answer_is_merged_and_advances(self) -> None:
        self.collector.handle_input("北上")

        result = self.collector.handle_input("那是我第一次離家工作，也第一次自己租屋")

        self.assertEqual(result, "已補充並記錄。")
        self.assertIsNone(self.collector.pending_follow_up)
        self.assertEqual(self.collector.question_idx, 1)
        self.assertIn("補充：", self.collector.segments[0].answers[0])

    def test_follow_up_question_uses_story_seed(self) -> None:
        self.collector.submit_answer("北上工作")
        self.collector.submit_answer("因為那是我第一次真的離家")

        question = self.collector.get_current_question()

        self.assertIn("北上工作", question)

    def test_handle_input_back(self) -> None:
        self.collector.submit_answer("答案一內容")
        self.collector.submit_answer("答案二內容")

        result = self.collector.handle_input("上一題")

        self.assertEqual(result, "已回到前一題。")
        self.assertEqual(self.collector.current_idx, 1)
        self.assertEqual(self.collector.question_idx, 0)
        self.assertEqual(self.collector.segments[0].answers, ["答案一內容"])
        self.assertEqual(self.collector.segments[1].answers, [])

    def test_dynamic_question_references_previous_answer(self) -> None:
        self.collector.submit_answer("北上工作")

        question = self.collector.get_current_question()

        self.assertIn("北上工作", question)
        self.assertIn("接著剛剛您提到", question)

    def test_skip_follow_up_keeps_original_answer(self) -> None:
        self.collector.handle_input("很苦")

        result = self.collector.handle_input("跳過")

        self.assertEqual(result, "已略過補充，先依目前內容記錄。")
        self.assertEqual(self.collector.question_idx, 1)
        self.assertEqual(self.collector.segments[0].answers[0], "很苦")

    def test_go_back_on_first_question_raises_error(self) -> None:
        with self.assertRaises(IndexError):
            self.collector.go_back()

    def test_submit_after_finished_raises_error(self) -> None:
        for segment in self.collector.segments:
            for _ in segment.questions:
                self.collector.submit_answer("測試答案內容")

        with self.assertRaises(IndexError):
            self.collector.submit_answer("多餘答案")

    def test_assemble_markdown_contains_all_titles(self) -> None:
        for segment in self.collector.segments:
            for _ in segment.questions:
                self.collector.submit_answer("測試答案內容")

        markdown = self.collector.assemble_markdown()
        self.assertIn("## 主線摘要", markdown)
        self.assertIn("## 故事正文", markdown)
        self.assertIn("## 訪談紀錄", markdown)
        self.assertIn("> 主線：測試答案內容", markdown)
        for segment in self.collector.segments:
            self.assertIn(f"## {segment.title}", markdown)

    def test_assemble_story_markdown_builds_long_story(self) -> None:
        answers = [
            "北上工作",
            "因為那是我第一次真正決定自己的人生",
            "二十多歲，家裡經濟普通，我剛離開熟悉的家鄉",
            "每天擠公車、租小房間，身邊幾乎沒有能依靠的人",
            "公司通知我要調去台北，工作壓力一下變大",
            "我站在月台上，突然知道自己回不去原本的生活了",
            "最難的是孤單和不確定，不知道自己能不能撐下去",
            "有一次加班到深夜，一個人在街頭邊走邊哭",
            "我還是決定留下來，想試試自己能走多遠",
            "我最怕失敗讓家人失望，但也想守住自己的志氣",
            "後來我真的站穩了，也慢慢有能力照顧家裡",
            "這段路讓我更懂得體諒家人，也更珍惜每一份工作",
            "它讓我知道，原來人可以在害怕裡長出力量",
            "我會跟當時的自己說，先別怕，你會成為更穩的人",
            "希望孩子記得，勇敢不是不怕，而是怕了還願意往前",
            "遇到難關時，不要急著否定自己，慢慢走也算前進",
        ]

        for answer in answers:
            self.collector.submit_answer(answer)

        story = self.collector.assemble_story_markdown()

        self.assertIn("# 北上工作：在困難裡做出的選擇", story)
        self.assertIn("## 故事正文", story)
        self.assertIn("很多重要決定之所以沉重", story)
        self.assertIn("遇到難關時，不要急著否定自己", story)

    def test_assemble_markdown_contains_unanswered_placeholder(self) -> None:
        self.collector.handle_input("跳過")

        markdown = self.collector.assemble_markdown()

        self.assertIn("_未回答_", markdown)

    def test_save_markdown_writes_story_file(self) -> None:
        for segment in self.collector.segments:
            for _ in segment.questions:
                self.collector.submit_answer("測試答案內容")

        with TemporaryDirectory() as temp_dir:
            output_file = self.collector.save_markdown(temp_dir)

            self.assertTrue(output_file.exists())
            self.assertEqual(output_file.suffix, ".md")
            saved = Path(output_file).read_text(encoding="utf-8")
            self.assertIn("## 故事正文", saved)

    @patch("builtins.print")
    def test_run_cli_returns_markdown(self, mock_print) -> None:
        answers = [
            "北上工作是我人生第一次真正離家打拚的開始",
            "這是我第一次長時間離家獨立生活",
        ] + ["這是一段足夠詳細的測試回答" for _ in range(sum(len(segment.questions) for segment in self.collector.segments) - 2)]

        with patch("builtins.input", side_effect=answers) as mock_input:
            markdown = run_cli()

        self.assertIn("## 主線摘要", markdown)
        self.assertIn("## 主線起點", markdown)
        self.assertIn("## 留給孩子的話", markdown)
        self.assertIn("> 主線：北上工作是我人生第一次真正離家打拚的開始", markdown)
        self.assertEqual(mock_input.call_count, sum(len(segment.questions) for segment in self.collector.segments))


if __name__ == "__main__":
    unittest.main()