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
from utils.thread_manager import ThreadManager

st.set_page_config(page_title="CORAL.py", page_icon="🐠", layout="centered", initial_sidebar_state="collapsed")
state = st.session_state

# Initialize ThreadManager in session state
if "thread_manager" not in state:
    state.thread_manager = ThreadManager()

exit_app = st.sidebar.button("Shut Down")

if exit_app:
    state.thread_manager.stop_all()
    time.sleep(1)
    os._exit(0)

try:
    pm = pymem.Pymem("cs2.exe")
    # Only show toast once
    if "loaded" not in state:
        state.msg = st.toast("cs2.exe found! loading...", icon="🎉")
        module = pymem.process.module_from_name(pm.process_handle, "client.dll")
        if isinstance(module, MODULEINFO):
            client = module.lpBaseOfDll
            state.client = client
            state.pm = pm
        time.sleep(1)
        state.msg.toast("coral.py loaded", icon="💯")
        state.loaded = True
    else:
        # Restore from state if they exist
        if "pm" in state:
            pm = state.pm
        if "client" in state:
            client = state.client

except pymem.pymem.exception.ProcessNotFound:
    st.error("cs2.exe not found!", icon="🚨")
    # Stop execution of the rest of the app if not found, to avoid errors
    st.stop()


# App design + layout
with open("assets/style.css") as f:
    css = f.read()

# Custom title using CSS file
st.html(f"<style>{css}</style>")
st.html(
    '<h1 class="title-font">C<span style="color:#fdc4b6;">o</span><span style="color:#e59572;">r</span><span style="color:#2694ab;">a</span><span style="color:#4dbedf;">l</span>🐠</h1>'
)

ballons = st.balloons()

tab1, tab2, tab3 = st.tabs(["Aim", "ESP", "Misc"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        enable_trigger = st.toggle("Enable trigger bot")
        state.thread_manager.config.enable_trigger = enable_trigger

        if not enable_trigger:
            state.disable_keys = True
        else:
            state.disable_keys = False
            # Start trigger thread if not running
            if not state.thread_manager.is_running("tbot"):
                state.thread_manager.start_thread("tbot", trig, (pm, client))

        enable_rcs = st.toggle("Enable RCS")
        state.thread_manager.config.enable_rcs = enable_rcs

        if not enable_rcs:
            state.disable_slider = True
        else:
            state.disable_slider = False
            # Start RCS thread if not running
            if not state.thread_manager.is_running("rcs"):
                state.thread_manager.start_thread("rcs", rcs, (pm, client))

    with col2:
        trigkey = st.selectbox(
            "Trigger bot key (*x* and *x2* are mouse side-butttons)",
            config.keys,
            placeholder="Choose a key",
            disabled=state.disable_keys,
        )
        # Update config directly
        state.thread_manager.config.trigger_key = trigkey

        amt = st.slider("RCS Amount", 0.0, 2.0, 2.0, 0.1, disabled=state.disable_slider)
        # Update config directly
        state.thread_manager.config.rcs_amount = amt

with tab2:
    enable_esp = st.toggle("Enable ESP")
    state.thread_manager.config.enable_esp = enable_esp

    if enable_esp:

        def run_esp_wrapper(stop_event, config, pm, client):
            esp_controller = ESPController(pm, client)
            esp_controller.run_esp(stop_event, config)

        if not state.thread_manager.is_running("esp"):
            state.thread_manager.start_thread("esp", run_esp_wrapper, (pm, client))

if not enable_trigger and state.thread_manager.is_running("tbot"):
    state.thread_manager.stop_thread("tbot")

if not enable_rcs and state.thread_manager.is_running("rcs"):
    state.thread_manager.stop_thread("rcs")

if not enable_esp and state.thread_manager.is_running("esp"):
    state.thread_manager.stop_thread("esp")
