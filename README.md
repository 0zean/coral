<h1 align="center">
    <img src="/assets/banner.png" width="450"/>
</h1>


<p align="center">
    <a href="https://raw.githubusercontent.com/0zean/coral/main/LICENSE" target="_blank">MIT License</a>
</p>


<div align="center">
    <img src="https://img.shields.io/github/stars/0zean/oasis?style=for-the-badge&logo=github&color=fdc4b6"/>
    <img src="https://img.shields.io/github/issues/0zean/oasis?style=for-the-badge&logo=github&color=2694ab"/>
    <img src="https://img.shields.io/github/commit-activity/t/0zean/oasis?style=for-the-badge&logo=github&color=e59572"/>
    <img src="https://img.shields.io/github/forks/0zean/oasis?style=for-the-badge&logo=github&color=4dbedf"/>
</div>


A streamlit web-app framework for Counter-Strike 2 mods built using Python. **For Educational purposes only.**

<div align="center">
<img src="/assets/demo.png" alt="icon"/>
</div>

# Setup

You'll need [a2x's cs2-dumper](https://github.com/a2x/cs2-dumper) for updating offsets at launch. You can find the `cs2-dumper.exe` under releases or, preferably, compile it yourself so its up to date.

Once downloaded, place it in the same folder as this repo after cloning.

## 🎚️ Features:
- [x] RCS (amount slider)
- [x] Trigger Bot (trigger key)
- [X] ESP (box, health, name, skeleton) 
- [ ] Misc


### 🧬 1. Clone the Repo

```bash
git clone https://github.com/0zean/coral.git
```

### 🛠️ 2. Create virtual 

Using pyenv, create a new virtual environment:

```bash
pyenv local 3.10.11
python -m venv .venv
```

### 📦 3. Install libraries

Install dependencies via `poetry`:

```bash
pip install poetry
poetry install
```

### 🚀 4. Run the application

To start the streamlit app, have CS2 running and double-click `start.bat`. This will run the offset dumper and start the streamlit server.

The web app will compile and then start running at `http://localhost:8501` which will be automatically copied to the clipboard.

Because the streamlit app is hosted on localhost, it can optionally be accessed through your phone if you create an exception for port `8501` in your firewall Inbound Rules.

### ⚠️ Warning

Cheating in Counter-Strike 2 is not condoned and there is no guarentee this app won't result in a ban. This project is intended for educational purposes showcasing read-only memory applications. **Use at your own risk!**
