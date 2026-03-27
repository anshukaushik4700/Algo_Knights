## 🔐 Configuration & Credentials Management

### Project Structure

```
Algo_Knights/
├── .env                 ← YOUR API CREDENTIALS (KEEP PRIVATE!)
├── .env.template        ← Template reference (safe to share)
├── .gitignore          ← Excludes .env from git
├── Strategy_01/
│   ├── run_bot.py      ← Reads from root .env
│   ├── setup_api.py    ← Reads from root .env
│   └── (other files)
└── Strategy_02/
    └── (will also read from root .env)
```

### 📋 Setup Steps

#### Step 1: Rename Template to Active File

At root folder (`Algo_Knights/`):

```bash
# Copy the template to create your actual .env
cp .env.template .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.template .env
```

#### Step 2: Add Your Credentials

Edit `Algo_Knights/.env` and fill in:

```
# Dhan API Credentials (from https://www.dhan.co/settings/api-keys)
DHAN_CLIENT_ID=your_actual_client_id_here
DHAN_ACCESS_TOKEN=your_actual_access_token_here
DHAN_API_KEY=your_actual_api_key_here

# Trading Mode
PAPER_TRADING=True        # Change to False after 10 days validation

# Strategy Parameters (optional - use defaults if not set)
EMA_FAST=20
EMA_SLOW=200
MAX_TRADES_DAY=4
RR_RATIO=2.5
```

#### Step 3: Verify Settings

Both Strategy_01 and Strategy_02 will automatically find and load this file.

```bash
cd Strategy_01
python setup_api.py    # Check if credentials are loaded correctly
```

### ✅ How It Works

**When you run Strategy_01:**

```
run_bot.py launches
    ↓
Looks for .env in Strategy_01/ folder
    ↓
If found → Uses it
If NOT found → Looks in parent folder (Algo_Knights/)
    ↓
Loads credentials automatically
```

This means:
- ✅ You can have ONE `.env` at root shared by all strategies
- ✅ Or you can have individual `.env` files in each strategy folder
- ✅ The strategy will find whichever one exists

### 🔒 Security

**IMPORTANT - DO NOT commit `.env` to git!**

The `.gitignore` file already excludes it:
```
.env          ← Git will ignore this file
.env.local    ← Also ignored
```

**Verify it's protected:**
```bash
git status     # Should NOT show .env in the list
```

If `.env` appears in git status:
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### 📁 File Roles

| File | Location | Purpose | Keep Private? |
|------|----------|---------|---------------|
| `.env.template` | Root | Reference/template | ❌ No - safe to share |
| `.env` | Root | YOUR credentials | ✅ YES - keep private! |
| `.gitignore` | Root | Tells git to ignore .env | ❌ No - safe to share |

### ⚙️ Multi-Strategy Support

**Option 1: Shared Credentials (Recommended)**
```
Algo_Knights/.env          ← Single .env with shared credentials
Strategy_01/               ← Reads from parent .env
Strategy_02/               ← Also reads from parent .env
```

**Option 2: Individual Credentials (Advanced)**
```
Algo_Knights/.env          ← Root .env with default credentials
Strategy_01/.env           ← Individual Strategy_01 credentials (overrides root)
Strategy_02/.env           ← Individual Strategy_02 credentials (overrides root)
```

For most users, **Option 1 (shared) is recommended**.

### 🧪 Testing Configuration

**Check if your .env is being loaded:**

```bash
cd Strategy_01
python setup_api.py
```

Expected output:
```
✅ Environment Validation
   ✅ Dhan Client ID: ****...****
   ✅ Dhan Access Token: ****...****
   ✅ Dhan API Key: ****...****
```

### ❓ Common Questions

**Q: I have different strategies with different API keys?**
A: Create individual `.env` files in each strategy folder. They will use those instead of the root `.env`.

**Q: Can I have multiple trading accounts?**
A: Yes - keep separate `.env` files in each strategy folder with different credentials.

**Q: What if I forget to create `.env`?**
A: The bot will run in PAPER TRADING mode (virtual trades). This is safe but won't connect to real API.

**Q: How do I know if it's reading the right .env?**
A: Run `python setup_api.py` - it will tell you which file it loaded from.

**Q: Can I commit the `.env.template` file?**
A: Yes! It's just a template with no real credentials. It's safe to share.

### 🔧 Environment Variables Reference

```bash
# Dhan API (Required for live trading)
DHAN_CLIENT_ID         # From dhan.co dashboard
DHAN_ACCESS_TOKEN      # From dhan.co dashboard
DHAN_API_KEY           # From dhan.co dashboard

# Trading Mode
PAPER_TRADING=True     # Default: True (virtual trading)
                       # False: Real trading (real capital)

# Strategy Parameters (Optional - uses defaults if not set)
EMA_FAST=20            # Fast EMA for signal
EMA_SLOW=200           # Slow EMA for trend
MAX_TRADES_DAY=4       # Max entries per day
RR_RATIO=2.5           # Risk:Reward ratio
KILLSWITCH_SL=2        # SL hits before stopping
```

### 📚 Related Files

- `.env.template` - Keep as reference
- `.gitignore` - Protects your credentials
- `run_bot.py` - Loads .env automatically
- `setup_api.py` - Validates .env before trading

---

**Summary:** 
- ✅ Copy `.env.template` to `.env` at root
- ✅ Add your credentials to `.env`
- ✅ Both strategies automatically read from it
- ✅ Keep `.env` private, never commit to git
- ✅ `.env.template` can be shared/committed
