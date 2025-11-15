import streamlit as st

def show_dmaic_phase():
    st.title("📋 Fases DMAIC")
    current_phase = st.session_state.get('current_dmaic_phase', 'define')
    st.info(f"Fase {current_phase.upper()} - será implementada nas próximas etapas")
