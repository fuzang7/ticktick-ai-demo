# TickTick (Dida365) AI Demo 🚀

A sophisticated Python AI task management system that integrates TickTick (Dida365) with Large Language Models for intelligent goal decomposition, strategic planning, and daily productivity auditing.

## ✨ Core Features

### 🎯 **Intelligent Planning System**
- **AI-Powered Goal Decomposition**: Convert high-level goals into actionable tasks using LLMs
- **Smart Task Scheduling**: Automatic time planning with parent-child relationships
- **Strategic Task Planning**: Break down goals into daily executable tasks with logical sequencing

### 📊 **Comprehensive Review & Analysis**
- **Daily Review Generation**: AI-assisted progress reports with strategic insights
- **Global Task Dashboard**: System-wide task analysis and health monitoring
- **Strategic Auditor Persona**: Rational, data-driven productivity coaching with distinct AI personalities

### 🏢 **Continuous Productivity Management**
- **Strategic War Room**: Real-time status reporting with AI guidance throughout the day
- **Daily Log Management**: Automated logging and audit trail generation
- **Real-time AI Feedback**: Instant productivity coaching and course correction

### 🔧 **Advanced System Features**
- **OAuth2 Authentication**: Full OAuth2 flow implementation for secure TickTick API access
- **Centralized Prompt Management**: Modular prompt templates for easy persona customization
- **Project & Task Management**: Complete CRUD operations for TickTick tasks and projects
- **Error Handling & Logging**: Comprehensive error handling and detailed activity logging

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+**
- **TickTick Developer Account**: Register at [TickTick Developer Portal](https://developer.dida365.com/openapi)
- **DeepSeek API Key**: Get API key from [DeepSeek](https://platform.deepseek.com/) (or use OpenAI-compatible LLM provider)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ticktick-ai-demo.git
cd ticktick-ai-demo

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Create `.env` file** in project root:

```env
# TickTick OAuth2 Credentials (required)
TICKTICK_CLIENT_ID=your_client_id_here
TICKTICK_CLIENT_SECRET=your_client_secret_here
TICKTICK_REDIRECT_URI=http://localhost:8080/callback

# DeepSeek API (required for AI features)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Optional: Inbox ID for inbox-specific operations
TICKTICK_INBOX_ID=your_inbox_id_here

# Optional: Obsidian integration for daily notes
OBSIDIAN_DAILY_PATH=/path/to/your/obsidian/daily/note.md
```

2. **Authenticate with TickTick**:

```bash
python refresh_token.py
```
Follow the terminal instructions to complete the OAuth2 flow.

3. **Launch the AI Project Manager**:

```bash
python main.py
```

## 🎯 Main Features in Detail

### 1. Intelligent Planning System (`AIProjectManager.run_planner()`)

Break down complex goals into actionable tasks with AI-powered decomposition:

```python
# Example: Goal decomposition into 7-day learning plan
goal = "Learn Linux driver development in one week"

# AI automatically generates:
# 1. Parent task for the overall goal
# 2. Child tasks with logical sequencing
# 3. Time allocation across days
# 4. Due dates and dependencies
```

**Key Benefits**:
- **Parent-Child Relationships**: Maintain task hierarchy in TickTick
- **Time Planning**: Automatic due date assignment based on complexity
- **Logical Sequencing**: AI ensures tasks follow natural learning progression

### 2. Daily Review & Auditing (`AIProjectManager.run_auditor()`)

Generate structured daily progress reports with the Strategic Auditor persona:

```python
# Features include:
# • Task completion tracking
# • Progress analysis across three domains
# • ROI (Return on Investment) audit
# • Strategic recommendations
# • Export to Markdown/Obsidian
```

**Audit Modules**:
- **Module I**: Strategic Vacuum Period Audit (morning focus)
- **Module II**: Dual-Front Review (career & side projects)
- **Module III**: ROI Leverage Audit (high-impact behavior tracking)
- **Module IV**: Dynamic Tactical Scaling (energy-based planning)
- **Module V**: Final Verdict (objective performance assessment)

### 3. Global Task Dashboard (`AIProjectManager.run_dashboard()`)

System-wide task analysis for proactive management:

```python
# Dashboard provides:
# • Total active task count
# • Overdue task identification
# • Priority distribution analysis
# • Task categorization by project
# • Health risk assessment
# • Actionable optimization recommendations
```

**Analytical Perspectives**:
- **Risk Exposure**: Identify systemic vulnerabilities
- **Low ROI Task Detection**: Eliminate "pseudo-productivity"
- **Resource Misalignment**: Balance across strategic domains
- **Tactical Restructuring**: Immediate action recommendations

### 4. Strategic War Room (`AIProjectManager.run_strategic_war_room()`)

Continuous real-time productivity coaching throughout the day:

```bash
# Available commands:
/done [task_name]    # Quick task completion recording
/review              # Generate end-of-day summary
/quit or /exit       # Exit without daily review
```

**Real-time Features**:
- **Silent Logging**: Automatic capture of user activities
- **Negative Emotion Detection**: Flag and address emotional states
- **Quantitative Focus**: Enforce measurable metrics
- **Context-Aware Guidance**: Personalized responses based on activity history


## 🏗️ System Architecture

### Core Components

#### 1. **AIProjectManager** (`main.py`)
The main application orchestrator that provides four core functionalities:
- **Planner**: Goal decomposition with parent-child task relationships
- **Auditor**: Daily review generation with strategic auditing
- **Dashboard**: Global task analysis and system health monitoring
- **Strategic War Room**: Continuous real-time productivity coaching

#### 2. **DailyLogManager** (`main.py`)
Manages daily activity logs for continuous recording and evening summarization:
- Automatic directory creation and JSON log storage
- Timestamp tracking and log retrieval
- Formatting for AI analysis and audit prompts
- Obsidian integration support

#### 3. **PromptManager** (`prompt_manager.py`)
Centralized prompt management system with persona definitions:
- **Strategic Auditor Persona**: Data-driven, rational productivity coaching
- Context-aware prompt generation for different use cases
- Modular template system for easy customization
- Support for JSON response formatting for planning tasks

#### 4. **DidaClient** (`dida_client.py`)
Enhanced TickTick API client with dashboard support:
- Complete OAuth2 authentication and token management
- Parent-child task creation with due date support
- Dashboard data collection and analysis
- Comprehensive error handling and logging

#### 5. **LLMClient** (`llm_client.py`)
AI client supporting multiple LLM providers:
- DeepSeek API compatibility (OpenAI SDK format)
- Configurable temperature and token limits
- JSON response parsing for structured data

### Key Classes & Methods Examples

```python
# Initialize the complete system
from main import AIProjectManager
manager = AIProjectManager()

# Start the interactive application
manager.start()  # Shows menu with 4 main functions

# Direct method access
manager.run_planner()      # Goal decomposition
manager.run_auditor()      # Daily review
manager.run_dashboard()    # Global analysis
manager.run_strategic_war_room()  # Continuous coaching

# Log management
from main import DailyLogManager
logs = DailyLogManager()
logs.add_log_entry("task_completion", "Finished API integration")
logs.get_today_logs()  # Retrieve all today's logs

# Prompt management
from prompt_manager import PromptManager, UserContext
pm = PromptManager(UserContext(
    core_learning="IELTS/Technical Advancements",
    side_hustle="Novel Writing/Open Source Projects",
    career_field="Embedded Development"
))
prompt = pm.render_auditor_prompt(tasks_data, daily_logs, user_input)

# TickTick client with dashboard support
from dida_client import DidaClient
dida = DidaClient()
dashboard_data = dida.prepare_dashboard_data_for_llm(max_tasks=50)
```

## 📋 Configuration Guide

### Complete `.env` Configuration

```env
# ===== REQUIRED: TickTick API Credentials =====
# Register at: https://developer.dida365.com/openapi
TICKTICK_CLIENT_ID=your_client_id_here
TICKTICK_CLIENT_SECRET=your_client_secret_here
TICKTICK_REDIRECT_URI=http://localhost:8080/callback

# ===== REQUIRED: LLM API Key =====
# DeepSeek: https://platform.deepseek.com/
# OpenAI: https://platform.openai.com/
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# ===== OPTIONAL: Advanced Configuration =====
# Inbox ID (find via TickTick API)
TICKTICK_INBOX_ID=your_inbox_id_here

# Obsidian integration for daily notes
OBSIDIAN_DAILY_PATH=/path/to/your/obsidian/daily/note.md

# LLM Configuration (DeepSeek by default)
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com
```

### Step-by-Step Setup Walkthrough

#### 1. **TickTick Developer Account**
1. Visit [TickTick Developer Portal](https://developer.dida365.com/openapi)
2. Click "Create Application"
3. Fill in required information:
   - **Application Name**: e.g., "AI Task Assistant"
   - **Description**: Your application description
   - **Redirect URI**: `http://localhost:8080/callback`
4. Save your **Client ID** and **Client Secret**

#### 2. **DeepSeek API Key**
1. Go to [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Generate a new API key

#### 3. **Inbox ID Discovery**
```bash
# After authentication, run this Python snippet
python -c "
from dida_client import DidaClient
import json
client = DidaClient()
# This will list all projects, find INBOX type
projects = client.get_projects()  # if available
print(json.dumps(projects, indent=2))
"
```

## 🔧 Deployment & Usage Scenarios

### Local Development Setup

```bash
# 1. Clone and install
git clone https://github.com/yourusername/ticktick-ai-demo.git
cd ticktick-ai-demo

# 2. Configure environment
cp .env.example .env  # Create env file
nano .env  # Edit with your credentials
python refresh_token.py  # Complete OAuth2 authentication
python main.py  # Launch AI Project Manager
```

### Scheduled Daily Review (via Cron/Linux)

```bash
# Create daily review script
cat > daily_review.sh << 'EOF'
#!/bin/bash
cd /path/to/ticktick-ai-demo
source venv/bin/activate  # If using virtual env
python -c "
from main import AIProjectManager
app = AIProjectManager()
app.run_auditor()
" > daily_review_$(date +%Y%m%d).log 2>&1
EOF

# Make executable and schedule
chmod +x daily_review.sh
# Add to crontab for 6 PM daily
# 0 18 * * * /path/to/daily_review.sh
```

### Integration with Other Productivity Tools

#### Obsidian Integration
```yaml
# .env configuration for Obsidian
OBSIDIAN_DAILY_PATH=/Users/username/Obsidian/Daily/$(date +%Y-%m-%d).md

# Features:
# • Daily reviews appended to Obsidian daily notes
# • Searchable archive of AI-generated reports
# • Linking capability between reviews and related notes
```

#### Custom Prompt Customization
```python
# Example of customizing the Strategic Auditor persona
from prompt_manager import PromptManager, UserContext

# Define your personal context
context = UserContext(
    core_learning="Machine Learning/Deep Learning",
    side_hustle="AI Tutoring/Research Papers",
    career_field="Data Science"
)

pm = PromptManager(context)
# Now all generated prompts will reflect your specific domains
```

## ⚠️ Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **"Token file not found"** | Run `python refresh_token.py` to authenticate |
| **"Invalid OAuth2 credentials"** | Verify `TICKTICK_CLIENT_ID` and `TICKTICK_CLIENT_SECRET` in `.env` |
| **"Authorization code invalid"** | Get new auth code by restarting `refresh_token.py` |
| **"LLM API key invalid"** | Verify `DEEPSEEK_API_KEY` is correctly set |
| **"Inbox not accessible"** | Ensure correct `TICKTICK_INBOX_ID` or use default inbox detection |

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Also run with debug flag
python main.py --debug
```

### Security Best Practices
- **Never commit `.env` file** to version control
- **Secure `.token-oauth` file**: Contains access tokens
- **Use environment-specific configs**: Development vs Production
- **Regular token rotation**: Tokens expire, system handles refresh automatically
- **API key management**: Rotate keys periodically and use least-privilege principle

## 🤝 Contributing

We welcome contributions from the community! This is an open-source project designed to help people integrate AI with their task management workflow.

### How to Contribute

1. **Report Bugs**: Use GitHub Issues to report bugs with detailed reproduction steps
2. **Suggest Features**: Propose new features or improvements to existing ones
3. **Submit Pull Requests**: Follow the standard GitHub flow:
   - Fork the repository
   - Create a feature branch: `git checkout -b feature/my-awesome-feature`
   - Commit changes: `git commit -m 'feat: add awesome feature'`
   - Push to branch: `git push origin feature/my-awesome-feature`
   - Open a Pull Request

### Development Guidelines
- Follow existing code style and patterns
- Add tests for new features
- Update documentation when changing functionality
- Keep pull requests focused on a single change

### Project Structure Areas for Contribution
- **AI Prompt Engineering**: Enhance the Strategic Auditor persona
- **Integration Plugins**: Connect with other productivity tools
- **UI/UX Improvements**: Better CLI interface or web dashboard
- **Performance Optimization**: Faster task processing and LLM calls

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### MIT License Summary
- ✅ Free to use for personal, educational, and commercial purposes
- ✅ Can modify and distribute the software
- ✅ Private use allowed
- ✅ Include original copyright and license notice in copies

## 🙏 Acknowledgments

### Core Technologies
- **[TickTick](https://ticktick.com/)**: Excellent task management API and platform
- **[DeepSeek AI](https://deepseek.com/)**: Powerful and accessible LLM API
- **[ticktick-py](https://github.com/your-repo/ticktick-py)**: OAuth2 implementation for TickTick

### Inspiration & Philosophy
This project embodies principles from:
- **Physicalism & Rational Productivity**: Focus on measurable outcomes over feelings
- **Negative Entropy Thinking**: Systems should reduce disorder and increase focus
- **Strategic Execution**: AI as a thinking partner, not just a tool

### Contributors & Community
Thanks to all contributors and users who have provided feedback, bug reports, and feature suggestions.

## 📞 Support & Community

### Getting Help
- **GitHub Issues**: [Issue Tracker](https://github.com/yourusername/ticktick-ai-demo/issues)
- **Documentation**: Always check this README first
- **Community Discussions**: Coming soon!

### Issue Reporting Best Practices
When reporting an issue, please include:
1. **Environment Details**: Python version, OS, dependency versions
2. **Steps to Reproduce**: Clear, step-by-step instructions
3. **Expected vs Actual Behavior**: What should happen vs what actually happens
4. **Logs/Error Messages**: Copy-paste any error messages
5. **Screenshots**: If applicable

### Roadmap & Future Development
- [ ] Web dashboard interface
- [ ] Mobile app companion
- [ ] More AI persona options
- [ ] Advanced analytics and insights
- [ ] Plugin system for additional integrations

### Stay Updated
- ⭐ **Star the repository** to show support
- 🔔 **Watch the repository** for notifications
- 📢 **Share with friends** who might find it useful