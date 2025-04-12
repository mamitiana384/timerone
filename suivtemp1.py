import streamlit as st # type: ignore
import math
import json
import os
from streamlit_autorefresh import st_autorefresh # type: ignore
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # ✅ Gère le fuseau horaire

# ✅ Fonction pour toujours utiliser le bon fuseau horaire
def now_local():
    return datetime.now(ZoneInfo("Indian/Antananarivo"))

# --- Fonctions de Sauvegarde/Chargement ---
DATA_FILE = "console_data.json"

def save_state():
    # Crée un dictionnaire contenant l'état actuel à sauvegarder
    data = {
        "consoles": st.session_state.consoles,
        # Convertit les objets datetime en chaînes ISO pour la sérialisation JSON
        "start_times": {k: v.isoformat() if v else None for k, v in st.session_state.start_times.items()},
        "paused_elapsed": st.session_state.paused_elapsed,
        "is_paused": st.session_state.is_paused,
        "intervals": st.session_state.intervals,
        "interval_counts": st.session_state.interval_counts,
        # Convertit les objets datetime en chaînes ISO
        "session_initial_start": {k: v.isoformat() if v else None for k, v in st.session_state.session_initial_start.items()},
        # Gère la sérialisation du résumé, y compris les datetimes
        "last_stop_summary": {
            k: {
                "start": v["start"].isoformat(),
                "end": v["end"].isoformat(),
                "duration": v["duration"]
            } if v and isinstance(v, dict) and "start" in v and "end" in v and "duration" in v else None
            for k, v in st.session_state.last_stop_summary.items()
        }
    }
    # Écrit les données dans le fichier JSON
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4) # Ajout de l'indentation pour la lisibilité

def load_state():
    # Vérifie si le fichier de données existe
    if os.path.exists(DATA_FILE):
        try:
            # Ouvre et lit le fichier JSON
            with open(DATA_FILE, "r") as f:
                data = json.load(f)

            # Charge les données dans st.session_state, avec des valeurs par défaut
            st.session_state.consoles = data.get("consoles", {})
            # Reconvertit les chaînes ISO en objets datetime
            st.session_state.start_times = {
                k: datetime.fromisoformat(v) if v else None for k, v in data.get("start_times", {}).items()
            }
            st.session_state.paused_elapsed = data.get("paused_elapsed", {})
            st.session_state.is_paused = data.get("is_paused", {})
            st.session_state.intervals = data.get("intervals", {})
            st.session_state.interval_counts = data.get("interval_counts", {})
            # Reconvertit les chaînes ISO en objets datetime
            st.session_state.session_initial_start = {
                k: datetime.fromisoformat(v) if v else None for k, v in data.get("session_initial_start", {}).items()
            }
            # Reconvertit les données du résumé, y compris les datetimes
            st.session_state.last_stop_summary = {
                k: {
                    "start": datetime.fromisoformat(v["start"]),
                    "end": datetime.fromisoformat(v["end"]),
                    "duration": v["duration"]
                } if v and isinstance(v, dict) and "start" in v and "end" in v and "duration" in v else None
                for k, v in data.get("last_stop_summary", {}).items()
            }

            # S'assure que tous les états nécessaires existent pour chaque console chargée
            # Cela évite les erreurs si de nouveaux états ont été ajoutés au code depuis la dernière sauvegarde
            loaded_consoles = list(st.session_state.consoles.keys())
            for console in loaded_consoles:
                st.session_state.start_times.setdefault(console, None)
                st.session_state.paused_elapsed.setdefault(console, 0.0)
                st.session_state.is_paused.setdefault(console, False)
                st.session_state.intervals.setdefault(console, 30) # Intervalle par défaut (ex: 30 min)
                st.session_state.interval_counts.setdefault(console, 0)
                st.session_state.session_initial_start.setdefault(console, None)
                st.session_state.last_stop_summary.setdefault(console, None)

        except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
             # Affiche une erreur si le chargement échoue (fichier corrompu, format invalide)
             st.error(f"Erreur lors du chargement des données depuis {DATA_FILE}: {e}. Le fichier pourrait être corrompu ou d'un format ancien. Réinitialisation de l'état.")
             # Réinitialise à un état vide en cas d'échec
             initialize_empty_state()
    else:
        # Si le fichier n'existe pas, initialise simplement un état vide
        initialize_empty_state()


# --- Fonction d'Initialisation ---
def initialize_empty_state():
    # Définit toutes les clés nécessaires dans st.session_state avec des dictionnaires vides
    st.session_state.consoles = {}
    st.session_state.start_times = {}
    st.session_state.paused_elapsed = {}
    st.session_state.is_paused = {}
    st.session_state.intervals = {}
    st.session_state.interval_counts = {}
    st.session_state.session_initial_start = {}
    st.session_state.last_stop_summary = {}

# --- Point d'Entrée Principal ---
# Vérifie si l'état a déjà été initialisé dans cette session Streamlit
if 'consoles' not in st.session_state:
    # Si non initialisé, charge l'état depuis le fichier (ou initialise si le fichier n'existe pas / est corrompu)
    load_state()

# --- Configuration de la Page Streamlit et Auto-Refresh ---
st.set_page_config(page_title="Suivi des consoles", layout="wide")
st.title("🎮 Suivi du temps d'utilisation des consoles")
# Rafraîchit automatiquement la page toutes les 15 secondes pour mettre à jour les timers
st_autorefresh(interval=15000, limit=None, key="console_refresher")

# --- Formulaire d'Ajout de Console ---
with st.form("add_console", clear_on_submit=True): # clear_on_submit=True vide le champ après ajout
    new_console = st.text_input("Nom de la nouvelle console")
    submitted = st.form_submit_button("Ajouter Console")
    if submitted and new_console.strip(): # Vérifie que le nom n'est pas vide
        console_name = new_console.strip()
        if console_name not in st.session_state.consoles:
            # Initialise tous les états pour la nouvelle console
            st.session_state.consoles[console_name] = 0 # Cumul initial à 0
            st.session_state.start_times[console_name] = None
            st.session_state.paused_elapsed[console_name] = 0.0
            st.session_state.is_paused[console_name] = False
            st.session_state.intervals[console_name] = 30 # Intervalle par défaut
            st.session_state.interval_counts[console_name] = 0
            st.session_state.session_initial_start[console_name] = None
            st.session_state.last_stop_summary[console_name] = None
            save_state() # Sauvegarde immédiatement après l'ajout
            st.success(f"Console '{console_name}' ajoutée.")
            st.rerun() # Rafraîchit pour afficher la nouvelle console
        else:
            st.warning(f"La console '{console_name}' existe déjà.")
    elif submitted:
        st.warning("Veuillez entrer un nom pour la console.")

st.divider() # Ligne de séparation visuelle

# --- Affichage des Consoles Existantes ---
if not st.session_state.consoles:
    st.info("Aucune console ajoutée pour le moment. Utilisez le formulaire ci-dessus pour en ajouter une.")
else:
    st.subheader("🕹️ Consoles en suivi")
    # Crée une copie de la liste des clés pour éviter les problèmes lors de la suppression
    active_consoles = list(st.session_state.consoles.keys())

    for console in active_consoles:
        # Vérifie si la console existe toujours (au cas où elle aurait été supprimée dans une itération précédente)
        if console not in st.session_state.consoles:
            continue

        # Récupération sûre des états avec .get() pour éviter les KeyError si une clé manque accidentellement
        total_minutes = st.session_state.consoles.get(console, 0)
        start = st.session_state.start_times.get(console)
        paused = st.session_state.paused_elapsed.get(console, 0.0)
        is_paused = st.session_state.is_paused.get(console, False)
        interval = st.session_state.intervals.get(console, 30)
        interval_count_state = st.session_state.interval_counts.get(console, 0)
        initial = st.session_state.session_initial_start.get(console)
        summary = st.session_state.last_stop_summary.get(console)

        # --- Affichage du Résumé de la Dernière Session (si disponible) ---
        if summary:
            # Utilise un expander pour ne pas prendre trop de place par défaut
            with st.expander(f"📄 Résumé dernière session : {console}", expanded=False):
                st.markdown(f"""
                - **Début :** {summary['start'].strftime('%Y-%m-%d %H:%M:%S')}
                - **Fin :** {summary['end'].strftime('%Y-%m-%d %H:%M:%S')}
                - **Durée :** {summary['duration']:.1f} minutes
                """)
            # Le résumé reste affiché jusqu'à ce qu'une nouvelle session soit démarrée ou arrêtée

        # --- Section Principale d'Affichage et Contrôles ---
        col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1]) # Ajustement des largeurs des colonnes

        with col1: # Colonne Informations et Statut
            st.markdown(f"### 🎮 {console}")
            status = "⚪ Idle" # Statut par défaut
            now = now_local()
            running_minutes = 0.0 # Temps écoulé depuis le dernier 'start' ou 'resume'

            if initial: # Si une session a une heure de début initiale enregistrée
                if start and not is_paused: # Si le timer est actif
                    running_minutes = (now - start).total_seconds() / 60
                    status = f"🟢 En cours (démarrée à {initial.strftime('%H:%M:%S')})"
                elif is_paused: # Si le timer est en pause
                    # Pas de calcul de running_minutes si en pause
                    status = f"⏸️ En pause (démarrée à {initial.strftime('%H:%M:%S')})"
                # Si 'initial' existe mais 'start' est None et not is_paused -> vient d'être stoppé (état transitoire avant rerun)
            # Si 'initial' est None, la console est inactive (Idle)

            # Calcul du temps total de la session actuelle (temps pausé + temps en cours)
            total_session_minutes = paused + running_minutes
            # Calcul du temps global (cumul historique + session actuelle)
            total_global_minutes = total_minutes + total_session_minutes

            st.markdown(f"**Statut :** {status}")
            # Affiche le temps de la session en cours
            st.info(f"⏱️ Session actuelle : **{total_session_minutes:.1f} min**")
            # Affiche le temps total cumulé
            st.success(f"💡 Cumul total : **{total_global_minutes:.1f} min**")

        with col2: # Colonne Intervalles
            # Champ pour modifier la durée de l'intervalle
            new_interval = st.number_input(
                "Intervalle (min)",
                min_value=1,
                value=interval,
                step=1,
                key=f"interval_{console}",
                help="Durée d'un intervalle en minutes."
            )
            # Si l'utilisateur change la valeur de l'intervalle
            if new_interval != interval:
                st.session_state.intervals[console] = new_interval
                interval = new_interval # Met à jour la variable locale pour le calcul immédiat
                save_state()
                # Pas besoin de rerun ici, le calcul ci-dessous utilisera la nouvelle valeur

            # Calcul du nombre d'intervalles complétés pendant la session actuelle
            completed_intervals = math.floor(total_session_minutes / interval) if interval > 0 else 0

            # Met à jour l'état du compteur d'intervalles si nécessaire (utile avec auto-refresh)
            if completed_intervals != interval_count_state:
                st.session_state.interval_counts[console] = completed_intervals
                # Pas de save_state ici, sera sauvé par d'autres actions ou à la fin
                # Pas de rerun ici pour éviter les boucles avec autorefresh

            # Affiche le nombre d'intervalles complétés
            st.metric("Intervalles complétés", st.session_state.interval_counts.get(console, 0))

        with col3: # Colonne Boutons Start/Pause/Resume
             # Affiche "Démarrer" seulement si la console est inactive (Idle)
             if start is None and not is_paused:
                 if st.button("▶️ Démarrer", key=f"start_{console}"):
                     now_start = now_local()
                     st.session_state.start_times[console] = now_start
                     st.session_state.session_initial_start[console] = now_start # Heure de début de la session globale
                     st.session_state.paused_elapsed[console] = 0.0 # Réinitialise le temps pausé
                     st.session_state.is_paused[console] = False
                     st.session_state.interval_counts[console] = 0 # Réinitialise les compteurs d'intervalles
                     # Efface le résumé de la session précédente quand on démarre une nouvelle
                     st.session_state.last_stop_summary[console] = None
                     save_state()
                     st.rerun() # Rafraîchit l'interface

             # Affiche "Pause" seulement si le timer est en cours
             elif start and not is_paused:
                 if st.button("⏸️ Pause", key=f"pause_{console}"):
                     now_pause = now_local()
                     elapsed_since_last_start = (now_pause - start).total_seconds() / 60
                     # Ajoute le temps écoulé depuis le dernier start/resume au temps pausé total
                     st.session_state.paused_elapsed[console] += elapsed_since_last_start
                     st.session_state.start_times[console] = None # Met start à None pour indiquer la pause
                     st.session_state.is_paused[console] = True
                     save_state()
                     st.rerun()

             # Affiche "Reprendre" seulement si le timer est en pause
             elif is_paused:
                 if st.button("▶️ Reprendre", key=f"resume_{console}"):
                     st.session_state.start_times[console] = now_local() # Redémarre le chrono interne
                     st.session_state.is_paused[console] = False
                     save_state()
                     st.rerun()

        with col4: # Colonne Boutons Stop/Supprimer
            # Affiche "Stop" si la session est en cours ou en pause
            if start or is_paused:
                if st.button("⏹️ Stop", key=f"stop_{console}", type="primary"):
                    end_time = now_local()
                    final_session_duration = paused # Commence avec le temps déjà accumulé pendant les pauses

                    if start: # Si le chrono tournait au moment du stop, ajoute le dernier segment de temps actif
                        final_session_duration += (end_time - start).total_seconds() / 60

                    # Enregistre le résumé de la session qui vient de se terminer (utile pour l'affichage)
                    initial_start_time = initial if initial else end_time
                    st.session_state.last_stop_summary[console] = {
                        "start": initial_start_time,
                        "end": end_time,
                        "duration": final_session_duration
                    }

                    # --- CHANGEMENT PRINCIPAL ICI ---
                    # Au lieu d'ajouter au cumul, on remet le compteur de cumul à ZÉRO
                    st.session_state.consoles[console] = 0
                    # ---------------------------------

                    # Réinitialise les états de suivi de la session pour cette console
                    st.session_state.start_times[console] = None
                    st.session_state.paused_elapsed[console] = 0.0
                    st.session_state.is_paused[console] = False
                    st.session_state.session_initial_start[console] = None
                    st.session_state.interval_counts[console] = 0 # Remet aussi le compteur d'intervalles à zéro

                    save_state() # Sauvegarde l'état réinitialisé (avec cumul à 0)
                    st.rerun() # Rafraîchit l'interface

            # Bouton pour supprimer la console (toujours visible pour une console existante)
            # ... (le code pour le bouton Supprimer reste inchangé) ...
            with st.expander("Supprimer"):
                 st.warning(f"Attention, ceci supprimera la console '{console}' et son historique.")
                 if st.button("❌ Confirmer la Suppression", key=f"delete_{console}"):
                     # Supprime la console de tous les dictionnaires d'état
                     for state_key in [
                         "consoles", "start_times", "paused_elapsed", "is_paused",
                         "intervals", "interval_counts", "session_initial_start", "last_stop_summary"
                     ]:
                         if console in st.session_state[state_key]:
                             st.session_state[state_key].pop(console)
                     save_state()
                     st.success(f"Console '{console}' supprimée.")
                     st.rerun() # Rafraîchit pour enlever la console de l'affichage

          

        # --- Section d'Ajustement Manuel ---
        # Utilise un expander pour ne pas surcharger l'interface principale
        with st.expander("🔧 Ajustement Manuel (si session démarrée avant l'app)"):
            # Désactive les contrôles d'ajustement si une session est déjà active (en cours ou en pause)
            # L'ajustement doit se faire quand la console est 'Idle' dans l'application
            manual_disabled = start is not None or is_paused

            # Divise en colonnes pour un meilleur alignement date/heure
            col_date_manual, col_time_manual = st.columns(2)
            with col_date_manual:
                # Sélecteur pour la date de début réelle
                manual_start_date = st.date_input(
                    "Date de début réelle",
                    value=now_local().date(), # Défaut à aujourd'hui
                    key=f"manual_start_date_{console}",
                    disabled=manual_disabled,
                    help="Entrez la date à laquelle la session a *vraiment* commencé."
                )
            with col_time_manual:
                # Sélecteur pour l'heure de début réelle
                 manual_start_time = st.time_input(
                     "Heure de début réelle",
                     # Défaut à l'heure actuelle (arrondie à la minute) - l'utilisateur doit changer
                     value=now_local().time().replace(second=0, microsecond=0),
                     key=f"manual_start_time_{console}",
                     disabled=manual_disabled,
                     step=timedelta(minutes=1), # Permet d'ajuster par minute
                     help="Entrez l'heure à laquelle la session a *vraiment* commencé."
                 )

            # Champ pour entrer le nombre d'intervalles déjà complétés
            manual_intervals = st.number_input(
                "Intervalles déjà complétés",
                min_value=0,
                step=1,
                value=0, # Défaut à 0
                key=f"manual_intervals_{console}",
                disabled=manual_disabled,
                help="Combien d'intervalles (selon la config actuelle) étaient terminés au moment où vous faites cet ajustement ?"
            )

            # Bouton pour appliquer l'ajustement manuel
            if st.button("Appliquer l'ajustement", key=f"apply_manual_{console}", disabled=manual_disabled):
                # Combine la date et l'heure sélectionnées en un objet datetime
                try:
                    if manual_start_date and manual_start_time:
                        manual_start_dt = datetime.combine(manual_start_date, manual_start_time).replace(tzinfo=ZoneInfo("Indian/Antananarivo"))
                    else:
                         st.error("Date ou heure manuelle invalide.")
                         manual_start_dt = None # Empêche la suite

                    if manual_start_dt: # Si la combinaison a réussi
                        now_apply = now_local()
                        # Vérifie que l'heure de début est bien dans le passé
                        if manual_start_dt >= now_apply:
                            st.error("L'heure de début manuelle doit être dans le passé.")
                        else:
                            # Calcule le temps écoulé entre le début manuel et maintenant (en minutes)
                            elapsed_manual_minutes = (now_apply - manual_start_dt).total_seconds() / 60

                            # --- Mise à jour de l'état ---
                            # Heure de début réelle de la session
                            st.session_state.session_initial_start[console] = manual_start_dt
                            # Heure à laquelle le *tracking de l'app* commence (maintenant)
                            st.session_state.start_times[console] = now_apply
                            # Pré-charge le temps déjà passé comme s'il avait été "pausé"
                            st.session_state.paused_elapsed[console] = elapsed_manual_minutes
                             # Applique le nombre d'intervalles manuels
                            st.session_state.interval_counts[console] = manual_intervals
                            # S'assure que l'état est actif (pas en pause)
                            st.session_state.is_paused[console] = False

                            # Efface le résumé précédent, car on commence une nouvelle session (ajustée)
                            st.session_state.last_stop_summary[console] = None

                            save_state() # Sauvegarde le nouvel état ajusté
                            st.success(f"Ajustement appliqué pour {console}. Session démarrée à {manual_start_dt.strftime('%Y-%m-%d %H:%M:%S')}, temps actuel {elapsed_manual_minutes:.1f} min, {manual_intervals} intervalles.")
                            st.rerun() # Rafraîchit l'interface pour refléter l'ajustement

                except Exception as e:
                    st.error(f"Erreur lors de l'application de l'ajustement : {e}")

        st.divider() # Séparateur visuel entre chaque console

# --- Actions Globales dans la Sidebar ---
st.sidebar.header("⚠️ Actions Globales")

# Bouton pour forcer la sauvegarde manuelle de l'état actuel
if st.sidebar.button("💾 Forcer Sauvegarde"):
     try:
         save_state()
         st.sidebar.success("État actuel sauvegardé avec succès.")
     except Exception as e:
         st.sidebar.error(f"Erreur lors de la sauvegarde manuelle: {e}")

# Bouton pour réinitialiser toutes les données (avec confirmation)
st.sidebar.markdown("---") # Séparateur dans la sidebar
if st.sidebar.button("🔄 Réinitialiser TOUTES les consoles"):
    # Utilise un expander dans la sidebar pour la confirmation
    with st.sidebar.expander("Confirmation de Réinitialisation", expanded=True):
        st.warning("Ceci effacera TOUTES les données sauvegardées (consoles, temps, etc.). Êtes-vous absolument sûr ?")
        # Bouton de confirmation finale
        if st.button("OUI, TOUT RÉINITIALISER DÉFINITIVEMENT", key="confirm_reset_all"):
            initialize_empty_state() # Réinitialise st.session_state
            # Supprime le fichier de sauvegarde s'il existe
            if os.path.exists(DATA_FILE):
                try:
                    os.remove(DATA_FILE)
                    st.success("Fichier de données supprimé.")
                except OSError as e:
                    st.error(f"Impossible de supprimer le fichier de données ({DATA_FILE}): {e}")
            st.success("Toutes les données ont été réinitialisées.")
            st.rerun() # Rafraîchit l'application pour montrer l'état vide
