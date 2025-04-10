import streamlit as st
from datetime import datetime
import math # Needed for floor division

# Import the auto-refresh component
from streamlit_autorefresh import st_autorefresh

# --- Session State Initialization ---
# (Initialization code remains the same as previous version)
if 'consoles' not in st.session_state: st.session_state.consoles = {}
if 'start_times' not in st.session_state: st.session_state.start_times = {}
if 'paused_elapsed' not in st.session_state: st.session_state.paused_elapsed = {}
if 'is_paused' not in st.session_state: st.session_state.is_paused = {}
if 'intervals' not in st.session_state: st.session_state.intervals = {}
if 'interval_counts' not in st.session_state: st.session_state.interval_counts = {}
if 'session_initial_start' not in st.session_state: st.session_state.session_initial_start = {}
if 'last_stop_summary' not in st.session_state: st.session_state.last_stop_summary = {}


# --- Page Config and Auto-Refresh ---
st.set_page_config(page_title="Suivi des consoles", layout="wide")
st.title("🎮 Suivi du temps d'utilisation des consoles")

# Auto-refresher (e.g., every 15 seconds)
refresh_interval_ms = 15000
count = st_autorefresh(interval=refresh_interval_ms, limit=None, key="console_refresher")

# --- Add Console Form ---
# (Add Console form code remains the same)
with st.form("add_console"):
    new_console = st.text_input("Nom de la nouvelle console")
    submitted = st.form_submit_button("Ajouter")
    if submitted and new_console:
        if new_console not in st.session_state.consoles:
            st.session_state.consoles[new_console] = 0
            st.session_state.start_times[new_console] = None
            st.session_state.paused_elapsed[new_console] = 0.0
            st.session_state.is_paused[new_console] = False
            st.session_state.intervals[new_console] = 2
            st.session_state.interval_counts[new_console] = 0
            st.session_state.session_initial_start[new_console] = None
            st.session_state.last_stop_summary[new_console] = None
            st.success(f"Console '{new_console}' ajoutée (intervalle par défaut: 2 min).")
        else:
            st.warning(f"La console '{new_console}' existe déjà.")

st.divider()

# --- Display Consoles ---
if not st.session_state.consoles:
    st.info("👋 Ajoutez une console en utilisant le formulaire ci-dessus pour commencer le suivi.")
else:
    st.subheader("🕹️ Consoles en suivi")

    for console in list(st.session_state.consoles.keys()):
        # --- Display Last Stop Summary ---
        # (Summary display logic remains the same)
        summary = st.session_state.last_stop_summary.get(console)
        if summary:
            with st.expander(f"📄 Résumé de la dernière session pour {console}", expanded=True):
                 st.markdown(f"""
                 - **Début session :** {summary['start'].strftime('%Y-%m-%d %H:%M:%S')}
                 - **Fin session :** {summary['end'].strftime('%Y-%m-%d %H:%M:%S')}
                 - **Durée session :** {summary['duration']:.1f} minutes
                 """)
            st.session_state.last_stop_summary[console] = None

        # Get current state for this console
        total_recorded_minutes = st.session_state.consoles.get(console, 0)
        start_time = st.session_state.start_times.get(console) # Start of current segment
        paused_elapsed_minutes = st.session_state.paused_elapsed.get(console, 0.0)
        is_paused_status = st.session_state.is_paused.get(console, False)
        interval_minutes = st.session_state.intervals.get(console, 1)
        initial_start_time = st.session_state.session_initial_start.get(console) # The very first start time

        col_info, col_interval, col_actions, col_stop_delete = st.columns([3, 1, 1, 1])

        # --- Column 1: Information Display ---
        with col_info:
            st.markdown(f"### 🎮 {console}")

            current_segment_elapsed_minutes = 0.0
            status_message = "⚪ Idle" # Default status

            # --- MODIFIED STATUS LOGIC ---
            if initial_start_time: # Session has been started at least once
                if start_time is not None and not is_paused_status: # Currently Running
                    now = datetime.now()
                    current_segment_elapsed_minutes = (now - start_time).total_seconds() / 60
                    # Use initial_start_time in the status message
                    status_message = f"🟢 En cours (Session initiée à **{initial_start_time.strftime('%H:%M:%S')}**)"
                elif is_paused_status: # Currently Paused
                    # Use initial_start_time in the status message
                    status_message = f"⏸️ En Pause (Session initiée à **{initial_start_time.strftime('%H:%M:%S')}**)"
            # --- END OF MODIFIED STATUS LOGIC ---

            st.markdown(f"**Statut:** {status_message}")

            # --- REMOVED the separate italicized initial start time display ---
            # if initial_start_time:
            #    st.markdown(f"*Session démarrée initialement le {initial_start_time.strftime('%Y-%m-%d %H:%M:%S')}*") # No longer needed here

            # Calculate and display times (logic unchanged)
            total_session_active_time = paused_elapsed_minutes + current_segment_elapsed_minutes
            st.info(f"⏱️ Session Actuelle Active : **{total_session_active_time:.1f} min**") # Renamed label slightly for clarity
            display_total_cumulative = total_recorded_minutes + total_session_active_time
            st.success(f"💡 Temps total cumulé : **{display_total_cumulative:.1f} min**")

        # --- Column 2: Interval Settings & Count ---
        # (Interval logic remains the same)
        with col_interval:
            new_interval = st.number_input(
                f"Intervalle (min)", min_value=1, value=interval_minutes, step=1,
                key=f"interval_{console}", help="Durée en minutes pour le compteur d'intervalles."
            )
            if new_interval != interval_minutes:
                 st.session_state.intervals[console] = new_interval

            completed_intervals = 0
            if new_interval > 0:
                completed_intervals = math.floor(total_session_active_time / new_interval)
            st.session_state.interval_counts[console] = completed_intervals
            st.metric(label="Intervalles Complétés", value=completed_intervals)


        # --- Column 3: Action Buttons (Start/Pause/Resume) ---
        # (Button logic remains the same - Start still sets initial_start_time)
        with col_actions:
            # START
            if start_time is None and not is_paused_status:
                if st.button("▶️ Démarrer", key=f"start_{console}"):
                    now = datetime.now()
                    st.session_state.start_times[console] = now
                    st.session_state.session_initial_start[console] = now # Store initial start
                    st.session_state.paused_elapsed[console] = 0.0
                    st.session_state.is_paused[console] = False
                    st.session_state.interval_counts[console] = 0
                    st.rerun()
            # PAUSE
            if start_time is not None and not is_paused_status:
                if st.button("⏸️ Pause", key=f"pause_{console}"):
                    now = datetime.now()
                    current_segment_elapsed_minutes = (now - start_time).total_seconds() / 60
                    st.session_state.paused_elapsed[console] += current_segment_elapsed_minutes
                    st.session_state.start_times[console] = None
                    st.session_state.is_paused[console] = True
                    st.rerun()
            # RESUME
            if is_paused_status:
                 if st.button("▶️ Reprendre", key=f"resume_{console}"):
                     st.session_state.start_times[console] = datetime.now() # Resumes count from now
                     st.session_state.is_paused[console] = False
                     # Note: session_initial_start remains unchanged
                     st.rerun()


        # --- Column 4: Stop & Delete Buttons ---
        # (Stop/Delete logic remains the same)
        with col_stop_delete:
            session_is_active = start_time is not None or is_paused_status
            # STOP
            if session_is_active:
                if st.button("⏹️ Stop & Enregistrer", key=f"stop_{console}", help="Arrête le suivi et ajoute le temps de session au total enregistré."):
                    end_time = datetime.now()
                    final_session_time = paused_elapsed_minutes
                    if start_time is not None and not is_paused_status: # Was running
                        current_segment_elapsed_minutes = (end_time - start_time).total_seconds() / 60
                        final_session_time += current_segment_elapsed_minutes

                    retrieved_initial_start = initial_start_time if initial_start_time else end_time
                    st.session_state.last_stop_summary[console] = {
                        "start": retrieved_initial_start, "end": end_time, "duration": final_session_time
                    }
                    st.session_state.consoles[console] += int(final_session_time)
                    st.session_state.start_times[console] = None
                    st.session_state.paused_elapsed[console] = 0.0
                    st.session_state.is_paused[console] = False
                    st.session_state.interval_counts[console] = 0
                    st.session_state.session_initial_start[console] = None
                    st.rerun()
            # DELETE
            if st.button("❌ Supprimer", key=f"delete_{console}"):
                st.session_state.consoles.pop(console, None)
                st.session_state.start_times.pop(console, None)
                st.session_state.paused_elapsed.pop(console, None)
                st.session_state.is_paused.pop(console, None)
                st.session_state.intervals.pop(console, None)
                st.session_state.interval_counts.pop(console, None)
                st.session_state.session_initial_start.pop(console, None)
                st.session_state.last_stop_summary.pop(console, None)
                st.warning(f"Console '{console}' supprimée.")
                st.rerun()

        st.divider()

# --- Reset All Button ---
# (Reset All logic remains the same)
st.divider()
if st.button("🔄 Réinitialiser TOUTES les consoles"):
    st.session_state.consoles = {}
    st.session_state.start_times = {}
    st.session_state.paused_elapsed = {}
    st.session_state.is_paused = {}
    st.session_state.intervals = {}
    st.session_state.interval_counts = {}
    st.session_state.session_initial_start = {}
    st.session_state.last_stop_summary = {}
    st.success("Toutes les données des consoles ont été réinitialisées.")
    st.rerun()