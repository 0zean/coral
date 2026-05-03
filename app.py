import os
import time

import pymem  # type: ignore
import pymem.process  # type: ignore
import streamlit as st
from pymem.ressources.structure import MODULEINFO

from functions.esp import ESPController
from functions.rcs import rcs
from functions.trig import trig
from utils.config import config
from utils.memory import ProcessMemory
from utils.structs import ScreenSize
from utils.thread_manager import ThreadManager

st.set_page_config(
    page_title="CORAL.py",
    page_icon="🐠",
    layout="centered",
    initial_sidebar_state="collapsed",
)
state = st.session_state

if st.sidebar.button("Shut Down"):
    if "thread_mgr" in state:
        state.thread_mgr.stop_all()
    time.sleep(1)
    os._exit(0)

# process attachment
if "loaded" not in state:
    try:
        mem = ProcessMemory("cs2.exe")
    except pymem.pymem.exception.ProcessNotFound:
        st.error("cs2.exe not found!", icon="🚨")
        st.stop()

    module = pymem.process.module_from_name(mem.pymem.process_handle, "client.dll")
    if not isinstance(module, MODULEINFO):
        st.error("client.dll not found in cs2.exe!", icon="🚨")
        st.stop()

    state.mem = mem
    state.client = module.lpBaseOfDll
    state.thread_mgr = ThreadManager()

    msg = st.toast("cs2.exe found! loading...", icon="🎉")
    time.sleep(1)
    msg.toast("coral.py loaded", icon="💯")
    state.loaded = True


mem: ProcessMemory = state.mem
client: int = state.client
thread_mgr: ThreadManager = state.thread_mgr


# App design + layout
with open("assets/style.css") as f:
    st.html(f"<style>{f.read()}</style>")

st.html(
    '<h1 class="title-font">'
    'C<span style="color:#fdc4b6;">o</span>'
    '<span style="color:#e59572;">r</span>'
    '<span style="color:#2694ab;">a</span>'
    '<span style="color:#4dbedf;">l</span>🐠'
    "</h1>"
)
st.balloons()

tab_aim, tab_esp, tab_misc = st.tabs(["Aim", "ESP", "Misc"])

# Aim Tab
with tab_aim:
    col_toggle, col_control = st.columns(2)

    with col_toggle:
        # Trigger bot
        enable_trigger = st.toggle("Enable trigger bot")
        thread_mgr.config.enable_trigger = enable_trigger

        if enable_trigger and not thread_mgr.is_running("tbot"):
            thread_mgr.start_thread("tbot", trig, (mem, client))

        # RCS
        enable_rcs = st.toggle("Enable RCS")
        thread_mgr.config.enable_rcs = enable_rcs

        if enable_rcs and not thread_mgr.is_running("rcs"):
            thread_mgr.start_thread("rcs", rcs, (mem, client))

    with col_control:
        trigkey = st.selectbox(
            "Trigger key  (*x* / *x2* = mouse side-buttons)",
            config.keys,
            placeholder="Choose a key",
            disabled=not enable_trigger,
        )
        thread_mgr.config.trigger_key = trigkey

        amt = st.slider(
            "RCS amount",
            min_value=0.0,
            max_value=2.0,
            value=2.0,
            step=0.1,
            disabled=not enable_rcs,
        )
        thread_mgr.config.rcs_amount = amt

# ESP Tab
with tab_esp:
    enable_esp = st.toggle("Enable ESP")
    thread_mgr.config.enable_esp = enable_esp

    if enable_esp and not thread_mgr.is_running("esp"):
        screen = ScreenSize(width=config.SCREEN_WIDTH, height=config.SCREEN_HEIGHT)

        def _esp_thread(
            stop_event,
            cfg,
            _mem: ProcessMemory = mem,
            _client: int = client,
            _screen: ScreenSize = screen,
        ) -> None:
            controller = ESPController(_mem, _client, _screen)
            controller.run(stop_event, cfg)

        thread_mgr.start_thread("esp", _esp_thread, ())

    if not enable_esp and thread_mgr.is_running("esp"):
        thread_mgr.stop_thread("esp")
