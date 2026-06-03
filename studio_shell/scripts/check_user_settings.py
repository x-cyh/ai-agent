from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'workspace' / 'user_settings.json'
print(p.read_text(encoding='utf-8'))
