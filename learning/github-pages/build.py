#!/usr/bin/env python3
"""
Markdown to HTML converter for Learning Documentation
Qiita-inspired modern design with syntax highlighting
"""

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension
from pathlib import Path
import re
import json


def get_page_config():
    """ページの設定（タイトル、アイコン、説明）を返す"""
    return {
        # 新しい学習順序（1日で完了できる構成）
        "01_はじめに読んでください": {
            "icon": "📖",
            "desc": "設計資料の使い方",
            "category": "start"
        },
        "02_全体像": {
            "icon": "🏗️",
            "desc": "システムアーキテクチャ",
            "category": "basic"
        },
        "03_バックエンド解説": {
            "icon": "🐍",
            "desc": "Python/Flask の詳細",
            "category": "basic"
        },
        "04_フロントエンド解説": {
            "icon": "⚛️",
            "desc": "React/TypeScript の詳細",
            "category": "basic"
        },
        "05_セットアップの流れ": {
            "icon": "⚙️",
            "desc": "環境構築の手順",
            "category": "start"
        },
        "06_コマンド解説": {
            "icon": "💻",
            "desc": "ターミナルコマンド集",
            "category": "reference"
        },
        "07_動かしてみよう": {
            "icon": "🚀",
            "desc": "ローカル環境での実行",
            "category": "start"
        },
        "08_AIカスタマイズ": {
            "icon": "🤖",
            "desc": "AIの応答をカスタマイズ",
            "category": "advanced"
        },
        # FLOWファイル（参考資料）
        "FLOW_01_チャット送信の流れ": {
            "icon": "💬",
            "desc": "メッセージ送信の仕組み",
            "category": "flow"
        },
        "FLOW_02_ログインの流れ": {
            "icon": "🔐",
            "desc": "認証フローの解説",
            "category": "flow"
        },
        "FLOW_04_セッション管理の流れ": {
            "icon": "📝",
            "desc": "セッション管理の仕組み",
            "category": "flow"
        }
    }


def get_base_template():
    """ベースHTMLテンプレートを返す"""
    return '''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - GCP AI Agent 設計資料</title>
  <link rel="stylesheet" href="assets/style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📚</text></svg>">
</head>
<body>
  <header class="header">
    <a href="index.html" class="header-logo">
      <span>📚</span>
      <span>GCP AI Agent 設計資料</span>
    </a>
    <nav class="header-nav">
      <a href="index.html">ホーム</a>
      <a href="02_全体像.html">全体像</a>
      <a href="https://github.com" target="_blank">GitHub</a>
    </nav>
    <button class="menu-toggle" onclick="toggleSidebar()">
      <span></span>
      <span></span>
      <span></span>
    </button>
  </header>

  <div class="layout">
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-section">
        <div class="sidebar-title">📖 はじめに</div>
        <ul class="sidebar-nav">
          <li><a href="01_はじめに読んでください.html" {active_01}>はじめに読んでください</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🏗️ 仕組みを理解</div>
        <ul class="sidebar-nav">
          <li><a href="02_全体像.html" {active_02}>全体像</a></li>
          <li><a href="03_バックエンド解説.html" {active_03}>バックエンド解説</a></li>
          <li><a href="04_フロントエンド解説.html" {active_04}>フロントエンド解説</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🛠️ セットアップ</div>
        <ul class="sidebar-nav">
          <li><a href="05_セットアップの流れ.html" {active_05}>セットアップの流れ</a></li>
          <li><a href="06_コマンド解説.html" {active_06}>コマンド解説</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🚀 動かす</div>
        <ul class="sidebar-nav">
          <li><a href="07_動かしてみよう.html" {active_07}>動かしてみよう</a></li>
          <li><a href="08_AIカスタマイズ.html" {active_08}>AIカスタマイズ</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🔄 参考: フロー解説</div>
        <ul class="sidebar-nav">
          <li><a href="FLOW_01_チャット送信の流れ.html" {active_flow01}>チャット送信の流れ</a></li>
          <li><a href="FLOW_02_ログインの流れ.html" {active_flow02}>ログインの流れ</a></li>
          <li><a href="FLOW_04_セッション管理の流れ.html" {active_flow04}>セッション管理の流れ</a></li>
        </ul>
      </div>
    </aside>

    <main class="main">
      <article class="content">
        {content}
      </article>
      <footer class="footer">
        GCP AI Agent 設計資料 | Built with Python & Markdown
      </footer>
    </main>
  </div>

  <script>
    function toggleSidebar() {{
      document.getElementById('sidebar').classList.toggle('open');
    }}

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {{
      const sidebar = document.getElementById('sidebar');
      const toggle = document.querySelector('.menu-toggle');
      if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {{
        sidebar.classList.remove('open');
      }}
    }});
  </script>
</body>
</html>'''


def get_index_template():
    """インデックスページ用のHTMLテンプレートを返す"""
    return '''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GCP AI Agent 設計資料</title>
  <link rel="stylesheet" href="assets/style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📚</text></svg>">
</head>
<body>
  <header class="header">
    <a href="index.html" class="header-logo">
      <span>📚</span>
      <span>GCP AI Agent 設計資料</span>
    </a>
    <nav class="header-nav">
      <a href="index.html">ホーム</a>
      <a href="02_全体像.html">全体像</a>
      <a href="https://github.com" target="_blank">GitHub</a>
    </nav>
    <button class="menu-toggle" onclick="toggleSidebar()">
      <span></span>
      <span></span>
      <span></span>
    </button>
  </header>

  <div class="layout">
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-section">
        <div class="sidebar-title">📖 はじめに</div>
        <ul class="sidebar-nav">
          <li><a href="01_はじめに読んでください.html">はじめに読んでください</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🏗️ Phase1: 仕組みを理解</div>
        <ul class="sidebar-nav">
          <li><a href="02_全体像.html">全体像</a></li>
          <li><a href="03_バックエンド解説.html">バックエンド解説</a></li>
          <li><a href="04_フロントエンド解説.html">フロントエンド解説</a></li>
          <li><a href="05_顧客管理の仕組み.html">顧客管理の仕組み</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">💻 Phase2: 操作を知る</div>
        <ul class="sidebar-nav">
          <li><a href="06_コマンド解説.html">コマンド解説</a></li>
          <li><a href="07_ファイル形式と設定ファイル.html">ファイル形式と設定</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🚀 Phase3: 動かす</div>
        <ul class="sidebar-nav">
          <li><a href="08_AIカスタマイズ.html">AIカスタマイズ</a></li>
          <li><a href="09_セットアップの流れ.html">セットアップの流れ</a></li>
          <li><a href="10_動かしてみよう.html">動かしてみよう</a></li>
        </ul>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🔄 参考: フロー解説</div>
        <ul class="sidebar-nav">
          <li><a href="FLOW_01_チャット送信の流れ.html">チャット送信の流れ</a></li>
          <li><a href="FLOW_02_ログインの流れ.html">ログインの流れ</a></li>
          <li><a href="FLOW_04_セッション管理の流れ.html">セッション管理の流れ</a></li>
        </ul>
      </div>
    </aside>

    <main class="main">
      <article class="content">
        <div class="index-hero">
          <h1>📚 GCP AI Agent<br>設計資料</h1>
          <p>AIチャットシステムのアーキテクチャと実装ガイド</p>
        </div>

        <h2 class="section-title">🚀 まずはここから</h2>
        <div class="doc-grid">
          {start_cards}
        </div>

        <h2 class="section-title">🔄 フローで理解する</h2>
        <div class="doc-grid">
          {flow_cards}
        </div>

        <h2 class="section-title">📖 基礎知識</h2>
        <div class="doc-grid">
          {basic_cards}
        </div>

        <h2 class="section-title">🔧 上級編 & リファレンス</h2>
        <div class="doc-grid">
          {advanced_cards}
        </div>
      </article>
      <footer class="footer">
        GCP AI Agent 設計資料 | Built with Python & Markdown
      </footer>
    </main>
  </div>

  <script>
    function toggleSidebar() {{
      document.getElementById('sidebar').classList.toggle('open');
    }}

    document.addEventListener('click', function(e) {{
      const sidebar = document.getElementById('sidebar');
      const toggle = document.querySelector('.menu-toggle');
      if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {{
        sidebar.classList.remove('open');
      }}
    }});
  </script>
</body>
</html>'''


def create_card(filename, config):
    """ドキュメントカードのHTMLを生成"""
    return f'''<a href="{filename}.html" class="doc-card">
      <div class="doc-card-icon">{config['icon']}</div>
      <div class="doc-card-title">{filename.replace('_', ' ')}</div>
      <div class="doc-card-desc">{config['desc']}</div>
    </a>'''


def get_active_class(current_file, target_prefix):
    """サイドバーのアクティブクラスを返す"""
    if current_file.startswith(target_prefix):
        return 'class="active"'
    return ''


def convert_markdown_to_html(md_content, filename):
    """MarkdownをHTMLに変換（拡張機能付き）"""
    md = markdown.Markdown(
        extensions=[
            'tables',
            'fenced_code',
            CodeHiliteExtension(
                css_class='codehilite',
                linenums=False,
                guess_lang=True
            ),
            TocExtension(
                permalink=True,
                permalink_class='header-link',
                slugify=lambda value, separator: re.sub(r'[^\w\-]', '', value.lower().replace(' ', separator))
            ),
            'nl2br',
            'sane_lists'
        ]
    )

    html_content = md.convert(md_content)
    return html_content


def build_documentation():
    """ドキュメントをビルド"""
    # パス設定
    script_dir = Path(__file__).parent
    md_dir = script_dir.parent / 'md'
    out_dir = script_dir
    assets_dir = out_dir / 'assets'

    # assetsディレクトリが存在することを確認
    assets_dir.mkdir(exist_ok=True)

    # ページ設定を取得
    page_config = get_page_config()

    # 各カテゴリのカードを収集
    cards = {'start': [], 'flow': [], 'basic': [], 'advanced': [], 'reference': []}
    files = []

    # Markdownファイルを処理
    for md_file in sorted(md_dir.glob('*.md')):
        filename = md_file.stem

        # READMEはスキップ
        if filename.lower() == 'readme':
            continue

        files.append(filename)

        # カード生成
        config = page_config.get(filename, {
            "icon": "📄",
            "desc": "ドキュメント",
            "category": "reference"
        })

        card_html = create_card(filename, config)
        category = config.get('category', 'reference')
        cards[category].append(card_html)

        # Markdown読み込み・変換
        md_content = md_file.read_text(encoding='utf-8')
        html_content = convert_markdown_to_html(md_content, filename)

        # サイドバーのアクティブ状態を設定
        active_states = {
            'active_01': get_active_class(filename, '01_'),
            'active_02': get_active_class(filename, '02_'),
            'active_03': get_active_class(filename, '03_'),
            'active_04': get_active_class(filename, '04_'),
            'active_05': get_active_class(filename, '05_'),
            'active_06': get_active_class(filename, '06_'),
            'active_07': get_active_class(filename, '07_'),
            'active_08': get_active_class(filename, '08_'),
            'active_flow01': get_active_class(filename, 'FLOW_01'),
            'active_flow02': get_active_class(filename, 'FLOW_02'),
            'active_flow04': get_active_class(filename, 'FLOW_04'),
        }

        # HTMLテンプレートに適用
        template = get_base_template()
        title = filename.replace('_', ' ')

        html = template.format(
            title=title,
            content=html_content,
            **active_states
        )

        # 出力
        out_file = out_dir / f'{filename}.html'
        out_file.write_text(html, encoding='utf-8')
        print(f'✅ Created: {out_file.name}')

    # インデックスページを生成
    index_template = get_index_template()

    # カードを結合（上級編とリファレンスを統合）
    advanced_and_ref = cards['advanced'] + cards['reference']

    index_html = index_template.format(
        start_cards='\n        '.join(cards['start']),
        flow_cards='\n        '.join(cards['flow']),
        basic_cards='\n        '.join(cards['basic']),
        advanced_cards='\n        '.join(advanced_and_ref)
    )

    (out_dir / 'index.html').write_text(index_html, encoding='utf-8')
    print('✅ Created: index.html')

    print(f'\n🎉 Build complete! {len(files) + 1} files generated.')


if __name__ == '__main__':
    build_documentation()
