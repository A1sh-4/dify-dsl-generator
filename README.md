# Dify DSL Generator

**Language / 言語:** [🇯🇵 日本語](#japanese) | [🇺🇸 English](#english)

---

## Japanese

会話型のマルチエージェントパイプラインを通じて、本番環境に対応したDify DSL YAMLファイルを生成するClaude Codeプラグインです。作りたいものを説明するだけで、プラグインが要件分析・統合調査・ノード計画・プロンプトエンジニアリング・YAML生成をすべて処理し、Difyに直接インポートできるファイルを生成します。

---

### 機能概要

DifyアプリケーションはノードグラフやLLM設定、外部連携、会話ロジックを記述するYAML DSLファイルで定義されます。これらのファイルを手動で作成するにはスキーマやノードタイプ、Dify固有の規則に関する深い知識が必要です。

このプラグインはその壁を取り除きます。ユースケースを会話形式で説明するだけで、専門エージェントのパイプラインがすべてのステップを処理します：

- 要件を分析し、チャットフローかワークフローかを判断
- RAW API統合を行う前にDifyマーケットプレイスで既存プラグインを検索
- プラグインがない場合は外部APIを調査しHTTPノード設定を構築
- RAGユースケース向けのナレッジベース検索戦略を設計
- 完全なノードグラフ計画を作成し、生成前にユーザーの承認を取得
- すべてのLLMノードのシステムプロンプトとユーザープロンプトを作成
- 外部呼び出しのエラーハンドリングとフォールバックロジックを設計
- インポート可能な完全なYAMLファイルを生成・検証

---

### インストール方法

#### 方法1 — ZIPファイルをClaude.aiにインポート

最も簡単な方法です。gitやターミナルは不要です。

##### ステップ1 — プラグインZIPをダウンロード

このリポジトリから `skills/dify.zip` をダウンロードします：

- [github.com/A1sh-4/dify-dsl-generator](https://github.com/A1sh-4/dify-dsl-generator) を開く
- `skills/` に移動 → `dify.zip` をクリック → **Download** をクリック

##### ステップ2 — Claude.aiでClaude Codeを開く

- [claude.ai/code](https://claude.ai/code) にサインイン
- 右上の歯車アイコンから **設定** パネルを開く

##### ステップ3 — プラグインをインポート

- 左サイドバーの **Plugins** をクリック
- **Import Plugin**（または **+** ボタン）をクリック
- ダウンロードした `dify.zip` を選択
- Claude Codeが自動的に展開・登録します

##### ステップ4 — インストールを確認

Claude Codeの会話で `/dify` と入力します。スキルが起動すればインストール成功です。

```text
/dify FAQナレッジベースを検索するカスタマーサポートチャットボットを作成して
```

---

#### 方法2 — VS Codeでインストール

リポジトリをクローンして、Claude Code VS Code拡張機能の中で使用する方法です。

##### ステップ1 — Gitがインストール済みか確認

VS Codeのターミナル（Windowsは `Ctrl + `` ` `` `` / Macは `Cmd + `` ` `` `` ）を開いて実行：

```bash
git --version
```

バージョン番号が表示された場合（例: `git version 2.45.0`）、Gitは既にインストール済みです — ステップ2へ進んでください。

エラーや「コマンドが見つかりません」と表示された場合、Gitをインストールしてください：

| プラットフォーム | ダウンロード先 |
| --- | --- |
| Windows | [git-scm.com/download/win](https://git-scm.com/download/win) — インストーラーをデフォルト設定で実行 |
| macOS | ターミナルで `xcode-select --install` を実行、または [git-scm.com/download/mac](https://git-scm.com/download/mac) からダウンロード |
| Linux (Ubuntu/Debian) | `sudo apt update && sudo apt install git` |

インストール後は **VS Codeを再起動** してターミナルを開き直し、`git --version` で確認してください。

##### ステップ2 — GitにGitHubの認証情報を設定

名前とメールアドレスを設定します（コミット履歴に表示されます）：

```bash
git config --global user.name "あなたの名前"
git config --global user.email "your-github-email@example.com"
```

次に **GitHub CLI** でGitHubに認証します：

```bash
# GitHub CLIのインストール（未インストールの場合）
# Windows (winget):  winget install --id GitHub.cli
# macOS (brew):      brew install gh
# Linux:             https://cli.github.com/manual/installation

# 認証
gh auth login
```

プロンプトに従って操作します：**GitHub.com** → **HTTPS** → **ブラウザでログイン** を選択してください。これにより安全なトークンが保存され、以降の `git` コマンドでパスワード入力が不要になります。

> **代替方法（GitHub CLI不使用）：** [github.com/settings/tokens](https://github.com/settings/tokens) で `repo` スコープのPersonal Access Tokenを生成し、cloneやpush時にパスワードとして使用してください。

##### ステップ3 — リポジトリをクローン

プラグインを保存したいフォルダを選択し、以下を実行：

```bash
git clone https://github.com/A1sh-4/dify-dsl-generator.git
cd dify-dsl-generator
```

##### ステップ4 — Claude Code VS Code拡張機能をインストール

- VS Codeを開く
- 拡張機能パネルを開く（`Ctrl+Shift+X` / `Cmd+Shift+X`）
- **Claude Code**（Anthropic製）を検索
- **インストール** をクリック
- プロンプトが表示されたらAnthropicアカウントでサインイン

##### ステップ5 — VS Codeでプラグインフォルダを開く

```bash
code .
```

またはVS Codeメニューから：**ファイル → フォルダーを開く** → `dify-dsl-generator` フォルダを選択。

##### ステップ6 — Python仮想環境をセットアップ

プラグインの検証スクリプトにはPython 3.8以上が必要です：

```bash
# 仮想環境を作成
python -m venv .venv

# 有効化
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 依存パッケージをインストール
pip install pyyaml pytest
```

##### ステップ7 — インストールを確認

VS Code内のClaude Code会話で以下を入力：

```text
/dify PDFを受け取ってNotionにサマリーを投稿するドキュメント要約ワークフローを作成して
```

スキルが起動すれば、プラグインは正常に動作しています。

---

### クイックスタート

1. Claude Code（claude.aiまたはVS Code内）を開く
2. `/dify` と入力してEnterを押す
3. 作りたいものを説明する：

   ```text
   /dify

   以下の機能を持つカスタマーサポートチャットボットを作成したい：
   - 製品ドキュメントのナレッジベースを検索する
   - GPT-4oを使って質問に回答する
   - 解決できない問題はSlackの#supportチャンネルにエスカレーション
   - すべての会話をNotionデータベースに記録する
   ```

4. パイプラインが確認事項を質問し、ノード計画を提示します
5. 承認後、YAMLが生成されて `output/` に保存されます
6. Difyの **設定 → DSLインポート** でファイルをインポートします

---

### エージェントパイプライン

```text
ユーザー: /dify "Slackエスカレーション付きサポートチャットボットを作成"
       |
       v
[1] requirements-analyzer（要件分析）
       判定: チャットフロー、Slackプラグイン必要、ナレッジベース必要
       |
       v
[2] plugin-finder（プラグイン検索）
       発見: Difyマーケットプレイスの公式Slackプラグイン
       |
       v（プラグインが見つからない場合）
[3] api-researcher -----> [4] integration-builder
       外部API調査               HTTPノード設定を構築
       |
       v
[5] knowledge-architect（ナレッジ設計）
       設計: RAG検索戦略、top-k、スコア閾値
       |
       v
[6] node-planner（ノード計画）
       ノードグラフ計画を作成 -> ユーザーに提示 -> 承認待ち
       |
       v（ユーザー承認後）
[7] prompt-engineer（プロンプト作成）
       全LLMノードのシステム・ユーザープロンプトを作成
       |
       v
[8] error-strategy（エラー戦略）
       リトライロジック、フォールバック分岐、エラーメッセージを設計
       |
       v
[9] dsl-generator（DSL生成）
       完全なYAML DSLファイルを組み立て -> output/に書き込み
       |
       v
[10] dsl-validator（自動バリデーション）
       スキーマ、ノード参照、必須フィールドを検証
       |
       v
    output/your_chatbot_YYYYMMDD_HHMMSS.yaml
    （Difyにインポート可能）
```

ステップ3、4、5、8は条件付きで、要件に該当コンポーネントが含まれる場合のみ実行されます。ステップ1、6、7、9、10は常に実行されます。

---

### 必要要件

- **Claude Code** — バージョン1.0以降、プラグインサポートが有効であること
- **Difyインスタンス** — セルフホストまたはDify Cloudアカウント
- **Python 3.8以上** — 検証・ユーティリティスクリプトに必要
- **インターネット接続** — docs.dify.aiからドキュメントを取得し、Difyマーケットプレイスを検索するために必要

---

### ライセンス

MIT

---

---

## English

A Claude Code plugin that generates production-ready Dify DSL YAML files through a conversational, multi-agent pipeline. Describe what you want to build — the plugin handles requirements analysis, integration research, node planning, prompt engineering, and YAML generation, producing a file you can import directly into Dify.

---

### What It Does

Dify applications are defined by YAML DSL files that describe node graphs, LLM configurations, integrations, and conversation logic. Authoring these files by hand requires deep knowledge of the schema, node types, and Dify-specific conventions.

This plugin eliminates that barrier. You describe your use case conversationally, and a pipeline of specialized agents handles every step:

- Analyzes your requirements and determines whether to build a chatflow or workflow
- Searches the Dify marketplace for existing plugins before resorting to raw API integration
- Researches external APIs when no plugin is available and builds HTTP node configurations
- Designs knowledge base retrieval strategies for RAG use cases
- Plans the full node graph and presents it for your approval before generating anything
- Engineers system and user prompts for every LLM node
- Designs error handling and fallback logic for external calls
- Generates a complete, validated YAML file ready for immediate import

---

### Installation

#### Method 1 — Import ZIP into Claude.ai

This is the quickest way to get started. No git or terminal required.

##### Step 1 — Download the plugin ZIP

Download `skills/dify.zip` from this repository:

- Go to [github.com/A1sh-4/dify-dsl-generator](https://github.com/A1sh-4/dify-dsl-generator)
- Navigate to `skills/` → click `dify.zip` → click **Download**

##### Step 2 — Open Claude Code on Claude.ai

- Go to [claude.ai/code](https://claude.ai/code) and sign in
- Open the **Settings** panel (gear icon, top right)

##### Step 3 — Import the plugin

- Click **Plugins** in the left sidebar
- Click **Import Plugin** (or the **+** button)
- Select the `dify.zip` file you downloaded
- Claude Code will extract and register the plugin automatically

##### Step 4 — Verify the install

Type `/dify` in any Claude Code conversation. If you see the skill trigger, the plugin is active.

```text
/dify Build a customer support chatbot that searches our FAQ knowledge base
```

---

#### Method 2 — Install via VS Code

This method clones the repository directly and uses it inside the Claude Code VS Code extension.

##### Step 1 — Check if Git is installed

Open the VS Code terminal (`Ctrl + `` ` `` `` on Windows / `Cmd + `` ` `` `` on Mac) and run:

```bash
git --version
```

If you see a version number (e.g. `git version 2.45.0`), Git is already installed — skip to Step 2.

If you get an error or "command not found", install Git:

| Platform | Download |
| --- | --- |
| Windows | [git-scm.com/download/win](https://git-scm.com/download/win) — run the installer with default settings |
| macOS | Run `xcode-select --install` in Terminal, or download from [git-scm.com/download/mac](https://git-scm.com/download/mac) |
| Linux (Ubuntu/Debian) | `sudo apt update && sudo apt install git` |

After installing, **restart VS Code** and re-open the terminal, then confirm with `git --version`.

##### Step 2 — Configure Git with your GitHub credentials

Tell Git your name and email (these appear in commit history):

```bash
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Then authenticate with GitHub using the GitHub CLI:

```bash
# Install GitHub CLI if not already installed
# Windows (winget):  winget install --id GitHub.cli
# macOS (brew):      brew install gh
# Linux:             https://cli.github.com/manual/installation

# Authenticate
gh auth login
```

Follow the prompts — select **GitHub.com**, **HTTPS**, and **Login with a web browser**. This stores a secure token so all future `git` and `gh` commands work without a password.

> **Alternative (no GitHub CLI):** Generate a Personal Access Token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope, then use it as your password when Git prompts during clone or push.

##### Step 3 — Clone the repository

Choose a folder where you want the plugin to live, then run:

```bash
git clone https://github.com/A1sh-4/dify-dsl-generator.git
cd dify-dsl-generator
```

##### Step 4 — Install the Claude Code VS Code extension

- Open VS Code
- Go to the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`)
- Search for **Claude Code** (by Anthropic)
- Click **Install**
- Sign in with your Anthropic / Claude account when prompted

##### Step 5 — Open the plugin folder in VS Code

```bash
code .
```

Or via VS Code: **File → Open Folder** → select the `dify-dsl-generator` folder.

##### Step 6 — Set up the Python virtual environment

The plugin's validation scripts require Python 3.8+:

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install pyyaml pytest
```

##### Step 7 — Verify the install

Open a Claude Code conversation inside VS Code and type:

```text
/dify Build a document summarization workflow that accepts a PDF and posts a summary to Notion
```

If the skill triggers, the plugin is working correctly.

---

### Quick Start

1. Open Claude Code (on claude.ai or inside VS Code).
2. Type `/dify` and press Enter.
3. Describe what you want to build:

   ```text
   /dify

   I want to build a customer support chatbot that:
   - Searches our product documentation knowledge base
   - Answers questions using GPT-4o
   - Escalates unresolved issues to our Slack #support channel
   - Logs all conversations to a Notion database
   ```

4. The pipeline asks clarifying questions, then presents a node plan for your approval.
5. After you approve, it generates the YAML and saves it to `output/`.
6. Import the file into Dify via **Settings → DSL Import**.

---

### Agent Pipeline

```text
User: /dify "build a support chatbot with Slack escalation"
       |
       v
[1] requirements-analyzer
       Determines: chatflow, needs Slack plugin, needs knowledge base
       |
       v
[2] plugin-finder
       Finds: official Slack plugin on Dify marketplace
       |
       v (no plugin found path)
[3] api-researcher ---------> [4] integration-builder
       Research external API        Build HTTP node config
       |
       v
[5] knowledge-architect
       Designs: RAG retrieval strategy, top-k, score threshold
       |
       v
[6] node-planner
       Produces node graph plan -> SHOWS TO USER -> WAITS FOR APPROVAL
       |
       v (after user approves)
[7] prompt-engineer
       Writes system + user prompts for every LLM node
       |
       v
[8] error-strategy
       Designs retry logic, fallback branches, error messages
       |
       v
[9] dsl-generator
       Assembles complete YAML DSL file -> writes to output/
       |
       v
[10] dsl-validator (auto-triggered by hook)
       Validates schema, node references, required fields
       |
       v
    output/your_chatbot_YYYYMMDD_HHMMSS.yaml
    (ready to import into Dify)
```

Steps 3, 4, 5, and 8 are conditional — they only run when relevant components are present in your requirements. Steps 1, 6, 7, 9, and 10 always run.

---

### Requirements

- **Claude Code** — version 1.0 or later, with plugin support enabled
- **Dify instance** — self-hosted or Dify Cloud account for importing and running the generated YAML
- **Python 3.8+** — required for validation and utility scripts
- **Internet access** — the plugin fetches current docs from docs.dify.ai and searches the Dify marketplace

---

### License

MIT

---

---
