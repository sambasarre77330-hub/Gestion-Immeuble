from datetime import datetime
import json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestion Immeuble & Trésorerie Pro",
    page_icon="🏢",
    layout="wide",
)

DOSSIER_RACINE = Path(".")
FICHIER_DATA = DOSSIER_RACINE / "donnees_immeuble.json"
DOSSIER_BACKUPS = DOSSIER_RACINE / "backups"
DOSSIER_BACKUPS.mkdir(exist_ok=True)


def safe_int(val):
  if val is None or pd.isna(val):
    return 0
  try:
    return int(float(val))
  except (ValueError, TypeError):
    return 0


def safe_str(val):
  if val is None or pd.isna(val):
    return ""
  return str(val).strip()


MODES_PAIEMENT = [
    "Espèces",
    "Wave",
    "Orange Money",
    "Virement bancaire",
    "Chèque",
]

CATEGORIES_CHARGES = [
    "Charges fixes (Gardiennage, Nettoyage)",
    "Factures collectives (Eau/Senelec communs)",
    "Maintenance & Travaux (Plomberie, Vidange...)",
    "Taxes & Impôts (TOM, Foncier)",
    "Autres imprévus",
]

DATA_DEFAUT_SEPTEMBRE = [
    {
        "Lot": "Magasin 1",
        "Locataire": "MOUBARAK",
        "Prévu": 350000,
        "Versé": 350000,
        "Mode": "Wave",
    },
    {
        "Lot": "Magasin 2",
        "Locataire": "KARA",
        "Prévu": 140000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 3",
        "Locataire": "ESSOTINA",
        "Prévu": 150000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 4 (Ch.1)",
        "Locataire": "DJAMBALA",
        "Prévu": 100000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 4 (Ch.2)",
        "Locataire": "ANISSA",
        "Prévu": 100000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 5 (Ch.1)",
        "Locataire": "KINDO",
        "Prévu": 100000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 5 (Ch.2)",
        "Locataire": "APONIKPE",
        "Prévu": 90000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 5 (Ch.3)",
        "Locataire": "JOSIAS",
        "Prévu": 80000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 6",
        "Locataire": "KAMONA",
        "Prévu": 200000,
        "Versé": 200000,
        "Mode": "Wave",
    },
    {
        "Lot": "Appt 7",
        "Locataire": "(Nom non renseigné)",
        "Prévu": 150000,
        "Versé": 150000,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 8 (Ch.1)",
        "Locataire": "AIDARA",
        "Prévu": 110000,
        "Versé": 110000,
        "Mode": "Wave",
    },
    {
        "Lot": "Appt 8 (Ch.2)",
        "Locataire": "ANDREE",
        "Prévu": 90000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 9",
        "Locataire": "ISSAKHA",
        "Prévu": 200000,
        "Versé": 200000,
        "Mode": "Orange Money",
    },
    {
        "Lot": "Appt 10",
        "Locataire": "AKAMBI",
        "Prévu": 150000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 11 (Ch.1)",
        "Locataire": "ANTHONY",
        "Prévu": 100000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 11 (Ch.2)",
        "Locataire": "MAMANE ABDOU",
        "Prévu": 100000,
        "Versé": 100000,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 12 (Ch.1)",
        "Locataire": "NORBERT",
        "Prévu": 85000,
        "Versé": 85000,
        "Mode": "Wave",
    },
    {
        "Lot": "Appt 12 (Ch.2)",
        "Locataire": "MALANDA MOSSIBA",
        "Prévu": 90000,
        "Versé": 90000,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 12 (Ch.3)",
        "Locataire": "NZIAOU",
        "Prévu": 80000,
        "Versé": 0,
        "Mode": "Espèces",
    },
    {
        "Lot": "Appt 13",
        "Locataire": "DIBANGOU",
        "Prévu": 150000,
        "Versé": 150000,
        "Mode": "Wave",
    },
    {
        "Lot": "Appt 14",
        "Locataire": "BA",
        "Prévu": 150000,
        "Versé": 0,
        "Mode": "Espèces",
    },
]


def charger_donnees():
  if not FICHIER_DATA.exists():
    initial = {
        "tresorerie_depart": 0,
        "cautions": [],
        "historique_mois": {
            "09-2026": {
                "loyers": DATA_DEFAUT_SEPTEMBRE,
                "charges": [],
                "extras": [],
            }
        },
    }
    sauvegarder_donnees(initial, creer_backup=False)
    return initial

  with open(FICHIER_DATA, "r", encoding="utf-8") as f:
    data = json.load(f)

  if "cautions" not in data or not isinstance(data["cautions"], list):
    data["cautions"] = []

  cautions_propres = []
  for c in data["cautions"]:
    if isinstance(c, dict):
      cautions_propres.append({
          "Lot": safe_str(c.get("Lot")),
          "Locataire": safe_str(c.get("Locataire")),
          "Montant": safe_int(c.get("Montant")),
          "Date": safe_str(c.get("Date"))
          or datetime.now().strftime("%d/%m/%Y"),
      })
  data["cautions"] = cautions_propres

  if "historique_mois" not in data:
    data = {
        "tresorerie_depart": 0,
        "cautions": data.get("cautions", []),
        "historique_mois": {
            "09-2026": {
                "loyers": data.get("loyers", DATA_DEFAUT_SEPTEMBRE),
                "charges": data.get("charges", []),
                "extras": data.get("extras", []),
            }
        },
    }

  for m_k, m_v in data["historique_mois"].items():
    for row in m_v.get("loyers", []):
      if "Mode" not in row or row["Mode"] not in MODES_PAIEMENT:
        row["Mode"] = "Espèces"
      row["Prévu"] = safe_int(row.get("Prévu"))
      row["Versé"] = safe_int(row.get("Versé"))

  return data


def sauvegarder_donnees(data, creer_backup=True):
  with open(FICHIER_DATA, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

  if creer_backup:
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier_backup = DOSSIER_BACKUPS / f"sauvegarde_{horodatage}.json"
    with open(fichier_backup, "w", encoding="utf-8") as f:
      json.dump(data, f, indent=4, ensure_ascii=False)

    fichiers = sorted(DOSSIER_BACKUPS.glob("sauvegarde_*.json"))
    if len(fichiers) > 25:
      for f_old in fichiers[:-25]:
        f_old.unlink()


donnees = charger_donnees()

liste_mois = sorted(
    donnees["historique_mois"].keys(),
    key=lambda x: datetime.strptime(x, "%m-%Y"),
)

# ----------------- BARRE LATÉRALE -----------------
st.sidebar.title("🏢 Navigation")

mois_choisi = st.sidebar.selectbox(
    "Mois de travail :", options=liste_mois, index=len(liste_mois) - 1
)

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Nouveau mois")
with st.sidebar.form("form_nouveau_mois"):
  nouveau_mois = st.text_input("Mois (MM-AAAA, ex: 10-2026)")
  btn_creer = st.form_submit_button("Ouvrir le mois")
  if btn_creer and nouveau_mois.strip():
    nom_m = nouveau_mois.strip()
    try:
      datetime.strptime(nom_m, "%m-%Y")
      if nom_m in donnees["historique_mois"]:
        st.sidebar.warning("Ce mois existe déjà !")
      else:
        dernier = liste_mois[-1]
        reprise = []
        for l in donnees["historique_mois"][dernier]["loyers"]:
          reprise.append({
              "Lot": l["Lot"],
              "Locataire": l["Locataire"],
              "Prévu": safe_int(l["Prévu"]),
              "Versé": 0,
              "Mode": "Espèces",
          })
        donnees["historique_mois"][nom_m] = {
            "loyers": reprise,
            "charges": [],
            "extras": [],
        }
        sauvegarder_donnees(donnees)
        st.sidebar.success(f"Mois {nom_m} ouvert.")
        st.rerun()
    except ValueError:
      st.sidebar.error("Format invalide. Utilisez MM-AAAA.")

st.sidebar.markdown("---")
backups_existants = sorted(
    DOSSIER_BACKUPS.glob("sauvegarde_*.json"), reverse=True
)
st.sidebar.caption(
    f"🛡️ {len(backups_existants)} sauvegardes automatiques conservées."
)

# ----------------- CALCUL DE TRÉSORERIE MULTI-MOIS -----------------
solde_reporte = safe_int(donnees.get("tresorerie_depart", 0))
synthese_globale = []

for m in liste_mois:
  m_obj = donnees["historique_mois"][m]
  encaisses = sum(safe_int(x.get("Versé")) for x in m_obj.get("loyers", []))
  depenses = sum(safe_int(x.get("Montant")) for x in m_obj.get("charges", []))
  extras = sum(safe_int(x.get("Montant")) for x in m_obj.get("extras", []))
  net = encaisses + extras - depenses

  dep = solde_reporte
  solde_reporte += net

  synthese_globale.append({
      "Mois": m,
      "Report Début": dep,
      "Loyers Encaissés": encaisses,
      "Extras": extras,
      "Charges": depenses,
      "Flux Net": net,
      "Trésorerie Fin": solde_reporte,
  })

  if m == mois_choisi:
    report_actuel = dep
    treso_actuelle = solde_reporte

# ----------------- CONTENU DU MOIS SÉLECTIONNÉ -----------------
mois_data = donnees["historique_mois"][mois_choisi]
st.title(f"🏢 Tableau de Bord - {mois_choisi}")

zone_indicateurs = st.container()

# Préparation du tableau interactif des lots
df_base = pd.DataFrame(mois_data["loyers"])

df_edite = st.data_editor(
    df_base,
    column_config={
        "Lot": st.column_config.TextColumn("Lot", disabled=True),
        "Locataire": st.column_config.TextColumn("Locataire"),
        "Prévu": st.column_config.NumberColumn(
            "Loyer Prévu (FCFA)", format="%d FCFA"
        ),
        "Versé": st.column_config.NumberColumn(
            "Montant Versé (FCFA)", format="%d FCFA"
        ),
        "Mode": st.column_config.SelectboxColumn(
            "Mode de Paiement",
            options=MODES_PAIEMENT,
            required=True,
            default="Espèces",
        ),
    },
    hide_index=True,
    key=f"editeur_{mois_choisi}",
)

df_edite["Prévu"] = df_edite["Prévu"].apply(safe_int)
df_edite["Versé"] = df_edite["Versé"].apply(safe_int)
df_edite["Reste Dû"] = df_edite["Prévu"] - df_edite["Versé"]
df_edite["Statut"] = df_edite.apply(
    lambda r: "✅ Réglé"
    if r["Reste Dû"] <= 0
    else ("⏳ Partiel" if r["Versé"] > 0 else "❌ Non perçu"),
    axis=1,
)

cols_sauve = ["Lot", "Locataire", "Prévu", "Versé", "Mode"]
if not df_edite[cols_sauve].equals(df_base[cols_sauve]):
  donnees["historique_mois"][mois_choisi]["loyers"] = df_edite[
      cols_sauve
  ].to_dict(orient="records")
  sauvegarder_donnees(donnees)
  st.rerun()

# ----------------- CALCULS FINANCIERS & JAUGE RECOUVREMENT -----------------
total_attendu = int(df_edite["Prévu"].sum())
total_loyers = int(df_edite["Versé"].sum())
total_impayes = int(df_edite["Reste Dû"].sum())
total_charges = sum(
    safe_int(c.get("Montant")) for c in mois_data.get("charges", [])
)
total_extras = sum(
    safe_int(e.get("Montant")) for e in mois_data.get("extras", [])
)
treso_dispo = report_actuel + total_loyers + total_extras - total_charges
total_cautions_actives = sum(
    safe_int(c.get("Montant")) for c in donnees.get("cautions", [])
)

taux_recouvrement = (total_loyers / total_attendu) if total_attendu > 0 else 0.0
pct_affiche = round(taux_recouvrement * 100, 1)

with zone_indicateurs:
  c1, c2, c3, c4, c5 = st.columns(5)
  c1.metric("Loyer Attendu", f"{total_attendu:,} FCFA".replace(",", " "))
  c2.metric("Loyers Encaissés", f"{total_loyers:,} FCFA".replace(",", " "))
  c3.metric(
      "Arriérés (Impayés)",
      f"{total_impayes:,} FCFA".replace(",", " "),
      delta="- à recouvrer",
      delta_color="inverse",
  )
  c4.metric(
      "Trésorerie Disponible",
      f"{treso_dispo:,} FCFA".replace(",", " "),
      delta=f"Report : {report_actuel:,} FCFA".replace(",", " "),
  )
  c5.metric(
      "Cautions Détenues",
      f"{total_cautions_actives:,} FCFA".replace(",", " "),
      help="Fonds de garantie isolés",
  )

  st.markdown(
      f"**Progression du Recouvrement : {pct_affiche} %** ({total_loyers:,} FCFA"
      f" reçus sur {total_attendu:,} FCFA attendus)".replace(",", " ")
  )
  st.progress(min(max(taux_recouvrement, 0.0), 1.0))

# ----------------- SYNTHÈSE PRODUITS VS CHARGES (COMPTE DE RÉSULTAT) -----------------
with st.expander(
    "📊 Synthèse Produits vs Charges (Résultat Net d'Exploitation)",
    expanded=True,
):
  total_produits = total_loyers + total_extras
  benefice_net = total_produits - total_charges
  taux_marge = (
      (benefice_net / total_produits * 100) if total_produits > 0 else 0.0
  )

  r1, r2, r3, r4 = st.columns(4)
  r1.metric(
      "Total Produits Encaissés", f"{total_produits:,} FCFA".replace(",", " ")
  )
  r2.metric(
      "Total Charges Payées",
      f"{total_charges:,} FCFA".replace(",", " "),
      delta=f"-{total_charges:,} FCFA".replace(",", " "),
      delta_color="inverse",
  )
  r3.metric(
      "Résultat Net Restant",
      f"{benefice_net:,} FCFA".replace(",", " "),
      delta="Bénéfice net",
  )
  r4.metric("Taux de Marge Nette", f"{taux_marge:.1f} %")

st.markdown("---")
st.subheader("📋 Tableau des 21 Lots")
st.caption(
    "💡 Édition directe : double-cliquez sur une case pour modifier le montant"
    " ou le locataire. Le mode de paiement par défaut est **Espèces**."
)

# ----------------- MODULE : FICHE HISTORIQUE PAR LOCATAIRE -----------------
st.markdown("---")
with st.expander("👤 Fiche Historique Individuelle par Locataire"):
  locataires_tous = sorted(
      list({
          safe_str(row.get("Locataire"))
          for m_dict in donnees["historique_mois"].values()
          for row in m_dict.get("loyers", [])
          if safe_str(row.get("Locataire"))
      })
  )

  if locataires_tous:
    locataire_sel = st.selectbox(
        "Consulter le dossier d'un locataire :", options=locataires_tous
    )

    historique_loc = []
    for m_k in liste_mois:
      m_content = donnees["historique_mois"][m_k]
      for row in m_content.get("loyers", []):
        if safe_str(row.get("Locataire")).lower() == locataire_sel.lower():
          p = safe_int(row.get("Prévu"))
          v = safe_int(row.get("Versé"))
          reste = p - v
          stt = "✅ Réglé" if reste <= 0 else ("⏳ Partiel" if v > 0 else "❌ Non perçu")
          historique_loc.append({
              "Mois": m_k,
              "Lot": row.get("Lot", ""),
              "Loyer Prévu": p,
              "Montant Versé": v,
              "Reste Dû": reste,
              "Mode": row.get("Mode", "Espèces"),
              "Statut": stt,
          })

    if historique_loc:
      df_loc = pd.DataFrame(historique_loc)
      tot_prevu_loc = int(df_loc["Loyer Prévu"].sum())
      tot_verse_loc = int(df_loc["Montant Versé"].sum())
      tot_du_loc = int(df_loc["Reste Dû"].sum())

      caut_loc = sum(
          safe_int(c.get("Montant"))
          for c in donnees.get("cautions", [])
          if safe_str(c.get("Locataire")).lower() == locataire_sel.lower()
      )

      h1, h2, h3, h4 = st.columns(4)
      h1.metric(
          "Total Loyers Facturés", f"{tot_prevu_loc:,} FCFA".replace(",", " ")
      )
      h2.metric(
          "Total Payé Cumulé", f"{tot_verse_loc:,} FCFA".replace(",", " ")
      )
      h3.metric(
          "Arriérés Globaux",
          f"{tot_du_loc:,} FCFA".replace(",", " "),
          delta="- dette" if tot_du_loc > 0 else "En règle",
          delta_color="inverse" if tot_du_loc > 0 else "normal",
      )
      h4.metric("Caution Déposée", f"{caut_loc:,} FCFA".replace(",", " "))

      st.dataframe(df_loc, hide_index=True)
  else:
    st.write("Aucun locataire enregistré pour le moment.")

# ----------------- VENTILATION DES MODES DE PAIEMENT -----------------
with st.expander("💳 Ventilation des encaissements par canal (Mois en cours)"):
  df_modes = (
      df_edite[df_edite["Versé"] > 0]
      .groupby("Mode")["Versé"]
      .sum()
      .reset_index()
  )
  if not df_modes.empty:
    col_pie1, col_pie2 = st.columns([1, 2])
    with col_pie1:
      for _, row_m in df_modes.iterrows():
        st.write(
            f"• **{row_m['Mode']}** : {row_m['Versé']:,} FCFA".replace(",", " ")
        )
    with col_pie2:
      st.bar_chart(df_modes.set_index("Mode"))
  else:
    st.write("Aucun versement enregistré pour ce mois.")

# ----------------- SECTION CHARGES & EXTRAS -----------------
st.markdown("---")
col_g, col_d = st.columns(2)

with col_g:
  st.subheader("➖ Charges Ventilées par Catégorie")
  with st.form(f"form_charge_{mois_choisi}", clear_on_submit=True):
    cat_c = st.selectbox("Catégorie de dépense", options=CATEGORIES_CHARGES)
    motif_c = st.text_input("Détail / Motif")
    montant_c = st.number_input(
        "Montant de la dépense (FCFA)", min_value=0, step=5000
    )
    if st.form_submit_button("Valider la dépense") and motif_c and montant_c > 0:
      mois_data["charges"].append({
          "Categorie": cat_c,
          "Motif": motif_c,
          "Montant": int(montant_c),
          "Date": datetime.now().strftime("%d/%m/%Y"),
      })
      sauvegarder_donnees(donnees)
      st.rerun()

  if mois_data["charges"]:
    for ch in mois_data["charges"]:
      st.write(
          f"• **[{ch.get('Categorie', 'Autres')}]** {ch['Motif']} :"
          f" -{safe_int(ch.get('Montant')):,} FCFA".replace(",", " ")
      )
    if st.button("Effacer les charges de ce mois"):
      mois_data["charges"] = []
      sauvegarder_donnees(donnees)
      st.rerun()

with col_d:
  st.subheader("➕ Rentrées Extras du Mois")
  with st.form(f"form_extra_{mois_choisi}", clear_on_submit=True):
    motif_e = st.text_input("Motif de l'entrée extra")
    montant_e = st.number_input(
        "Montant reçu (FCFA)", min_value=0, step=10000
    )
    if st.form_submit_button("Valider la rentrée") and motif_e and montant_e > 0:
      mois_data["extras"].append({
          "Motif": motif_e,
          "Montant": int(montant_e),
          "Date": datetime.now().strftime("%d/%m/%Y"),
      })
      sauvegarder_donnees(donnees)
      st.rerun()

  if mois_data["extras"]:
    for ex in mois_data["extras"]:
      st.write(
          f"• **{ex['Motif']}** : +{safe_int(ex.get('Montant')):,} FCFA".replace(
              ",", " "
          )
      )
    if st.button("Effacer les extras de ce mois"):
      mois_data["extras"] = []
      sauvegarder_donnees(donnees)
      st.rerun()

# ----------------- MODULE CAUTIONS DYNAMIQUE -----------------
st.markdown("---")
with st.expander("🔒 Gestion des Cautions & Dépôts de Garantie"):
  st.caption(
      "Les dépôts de garantie sont isolés de la trésorerie d'exploitation. Vous"
      " pouvez modifier une cellule au double-clic ou supprimer une ligne"
      " directement."
  )
  col_caut_form, col_caut_table = st.columns([1, 2])

  with col_caut_form:
    st.markdown("**Enregistrer une nouvelle caution :**")
    with st.form("form_caution", clear_on_submit=True):
      lot_caut = st.selectbox(
          "Lot", options=[l["Lot"] for l in mois_data["loyers"]]
      )
      nom_caut = st.text_input("Nom du locataire (ou provisoire)")
      mont_caut = st.number_input(
          "Montant de la caution (FCFA)", min_value=0, step=10000
      )
      if (
          st.form_submit_button("Encaisser la caution")
          and nom_caut
          and mont_caut > 0
      ):
        donnees["cautions"].append({
            "Lot": lot_caut,
            "Locataire": nom_caut,
            "Montant": int(mont_caut),
            "Date": datetime.now().strftime("%d/%m/%Y"),
        })
        sauvegarder_donnees(donnees)
        st.rerun()

  with col_caut_table:
    st.markdown("**Registre modifiable des cautions :**")
    if donnees["cautions"]:
      df_caut = pd.DataFrame(donnees["cautions"])
      caut_edite = st.data_editor(
          df_caut,
          num_rows="dynamic",
          column_config={
              "Lot": st.column_config.TextColumn("Lot"),
              "Locataire": st.column_config.TextColumn("Locataire"),
              "Montant": st.column_config.NumberColumn(
                  "Montant (FCFA)", format="%d FCFA"
              ),
              "Date": st.column_config.TextColumn("Date d'encaissement"),
          },
          hide_index=True,
          key="editeur_cautions",
      )

      caut_liste_propre = []
      for row_c in caut_edite.to_dict(orient="records"):
        lot_val = safe_str(row_c.get("Lot"))
        loc_val = safe_str(row_c.get("Locataire"))
        mt_val = safe_int(row_c.get("Montant"))
        date_val = (
            safe_str(row_c.get("Date")) or datetime.now().strftime("%d/%m/%Y")
        )
        if lot_val or loc_val or mt_val > 0:
          caut_liste_propre.append({
              "Lot": lot_val,
              "Locataire": loc_val,
              "Montant": mt_val,
              "Date": date_val,
          })

      if caut_liste_propre != donnees["cautions"]:
        donnees["cautions"] = caut_liste_propre
        sauvegarder_donnees(donnees)
        st.rerun()
    else:
      st.write("Aucune caution enregistrée actuellement.")

# ----------------- QUITTANCE WHATSAPP -----------------
st.markdown("---")
with st.expander("📱 Générateur de Quittance WhatsApp"):
  locataires_payeurs = df_edite[df_edite["Versé"] > 0]
  if not locataires_payeurs.empty:
    choix_loc = st.selectbox(
        "Sélectionner le locataire :",
        options=locataires_payeurs["Lot"]
        + " - "
        + locataires_payeurs["Locataire"],
    )
    lot_sel = choix_loc.split(" - ")[0]
    row_sel = locataires_payeurs[locataires_payeurs["Lot"] == lot_sel].iloc[0]

    date_jour = datetime.now().strftime("%d/%m/%Y")
    texte_quittance = f"""🏢 *QUITTANCE DE LOYER*
━━━━━━━━━━━━━━━━━━━━
*Période :* {mois_choisi}
*Bénéficiaire :* {row_sel['Locataire']}
*Logement :* {row_sel['Lot']}
*Montant versé :* {row_sel['Versé']:,} FCFA
*Mode de règlement :* {row_sel['Mode']}
*Solde restant dû :* {row_sel['Reste Dû']:,} FCFA
*Statut :* {'Soldé (En règle)' if row_sel['Reste Dû'] <= 0 else 'Acompte partiel'}
*Date d'émission :* {date_jour}
━━━━━━━━━━━━━━━━━━━━
_Reçu émis pour valoir ce que de droit._""".replace(
        ",", " "
    )

    st.text_area(
        "Texte prêt à copier pour WhatsApp :", texte_quittance, height=220
    )
  else:
    st.write(
        "Aucun loyer n'a encore été versé ce mois-ci pour générer un reçu."
    )

# ----------------- SYNTHÈSE GLOBALE & TÉLÉCHARGEMENT -----------------
st.markdown("---")
with st.expander("📈 Synthèse d'Accumulation Multi-Mois"):
  st.dataframe(pd.DataFrame(synthese_globale), hide_index=True)

st.download_button(
    label=f"📥 Télécharger le rapport de {mois_choisi} (Excel / CSV)",
    data=df_edite.to_csv(index=False, sep=";").encode("utf-8-sig"),
    file_name=f"bilan_loyers_{mois_choisi}.csv",
    mime="text/csv",
)