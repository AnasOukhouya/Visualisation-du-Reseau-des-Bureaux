import streamlit as st
import json
import os
import folium
from streamlit.components.v1 import html

# Charger les données des bureaux à partir du fichier JSON
DATA_FILE = 'offices_data.json'
IMAGES_FOLDER = 'images'

def load_offices():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_offices(offices):
    with open(DATA_FILE, 'w') as f:
        json.dump(offices, f)

# Créer le dossier d'images s'il n'existe pas
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

# Initialiser l'application
st.set_page_config(layout="wide")
st.title("Visualisation du Réseau de Bureaux")

# Charger les données des bureaux
if 'offices' not in st.session_state:
    st.session_state.offices = load_offices()

# Contrôles dans la barre latérale
st.sidebar.header("Ajouter ou Modifier un Bureau")
edit_office_mode = st.sidebar.radio("Mode", ["Ajouter un Bureau", "Modifier un Bureau"])

office_name = st.sidebar.text_input("Nom du Bureau")
latitude = st.sidebar.text_input("Latitude")
longitude = st.sidebar.text_input("Longitude")
is_sub_office = st.sidebar.checkbox("Est-ce un Sous-Bureau ?", key='checkbox1')
parent_office = None

if is_sub_office:
    parent_office = st.sidebar.selectbox("Sélectionner le Bureau Parent", [""] + [office['name'] for office in st.session_state.offices])

if edit_office_mode == "Ajouter un Bureau":
    if st.sidebar.button("Ajouter le Bureau"):
        if office_name and latitude and longitude:
            new_office = {
                'name': office_name,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'switches': [],
                'is_sub_office': is_sub_office,
                'parent_office': parent_office
            }
            st.session_state.offices.append(new_office)
            save_offices(st.session_state.offices)
            st.sidebar.success(f"{office_name} ajouté")
            st.query_params.office_name = office_name
elif edit_office_mode == "Modifier un Bureau":
    office_to_edit = st.sidebar.selectbox("Sélectionner le Bureau à Modifier", [office['name'] for office in st.session_state.offices])
    
    if office_to_edit:
        office = next(off for off in st.session_state.offices if off['name'] == office_to_edit)
        new_office_name = st.sidebar.text_input("Nouveau Nom du Bureau", value=office['name'])
        new_latitude = st.sidebar.text_input("Nouvelle Latitude", value=str(office['latitude']))
        new_longitude = st.sidebar.text_input("Nouvelle Longitude", value=str(office['longitude']))
        new_is_sub_office = st.sidebar.checkbox("Est-ce un Sous-Bureau ?", value=office['is_sub_office'], key='checkbox2')
        new_parent_office = None
        if new_is_sub_office:
            new_parent_office = st.sidebar.selectbox("Sélectionner le Nouveau Bureau Parent", [""] + [off['name'] for off in st.session_state.offices if off['name'] != office_to_edit])

        if st.sidebar.button("Mettre à Jour le Bureau"):
            office['name'] = new_office_name
            office['latitude'] = float(new_latitude)
            office['longitude'] = float(new_longitude)
            office['is_sub_office'] = new_is_sub_office
            office['parent_office'] = new_parent_office

            save_offices(st.session_state.offices)
            st.sidebar.success(f"{new_office_name} mis à jour")
            st.query_params.office_name = new_office_name

# Afficher les détails du bureau
st.header("Localisations des Bureaux")
office_selected = st.selectbox("Sélectionner un Bureau", [office['name'] for office in st.session_state.offices])

# Maintenir l'état pour le bureau sélectionné et ses commutateurs
if office_selected not in st.session_state:
    st.session_state[office_selected] = {
        "show_details": False,
        "switch_name": "",
        "ip_address": "",
        "picture": None,
        "edit_switch_index": None
    }

if st.button(f"Voir {office_selected}"):
    st.session_state[office_selected]["show_details"] = not st.session_state[office_selected]["show_details"]

# Montrer les détails du bureau si sélectionné
if st.session_state[office_selected]["show_details"]:
    office = next(office for office in st.session_state.offices if office['name'] == office_selected)
    st.write(f"**Nom du Bureau :** {office['name']}")
    st.write(f"**Latitude :** {office['latitude']}")
    st.write(f"**Longitude :** {office['longitude']}")
    
    if office['is_sub_office']:
        st.write(f"**Bureau Parent :** {office['parent_office']}")
    
    google_maps_link = f"https://www.google.com/maps/search/?api=1&query={office['latitude']},{office['longitude']}"
    st.markdown(f"[Voir sur Google Maps]({google_maps_link})")
    
    office_map = folium.Map(location=[office['latitude'], office['longitude']], zoom_start=13)
    folium.Marker(
        [office['latitude'], office['longitude']],
        popup=f"{office['name']} ({office['latitude']}, {office['longitude']})",
        icon=folium.Icon(color="blue", icon="building", prefix="fa"),
    ).add_to(office_map)
    
    if office['is_sub_office']:
        parent_office_data = next(off for off in st.session_state.offices if off['name'] == office['parent_office'])
        folium.PolyLine(
            [(office['latitude'], office['longitude']), (parent_office_data['latitude'], parent_office_data['longitude'])],
            color="green"
        ).add_to(office_map)
    
    map_html = office_map._repr_html_()
    html(map_html, height=500)
    
    st.subheader("Gérer les Commutateurs")
    st.write(f"**Commutateurs Actuels :**")
    for j, switch in enumerate(office['switches']):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"- **Nom :** {switch['name']}, **Adresse IP :** {switch['ip_address']}")
            if switch['picture']:
                st.image(os.path.join(IMAGES_FOLDER, switch['picture']), caption=f"Image de {switch['name']}", use_column_width=True)
        with col2:
            if st.button(f"Modifier", key=f"edit_switch_{j}"):
                st.session_state[office_selected]["edit_switch_index"] = j
                st.session_state[office_selected]["switch_name"] = switch['name']
                st.session_state[office_selected]["ip_address"] = switch['ip_address']
                st.session_state[office_selected]["picture"] = switch['picture']
            if st.button(f"Supprimer", key=f"delete_switch_{j}"):
                office['switches'].pop(j)
                save_offices(st.session_state.offices)
                st.query_params.view_office = office_selected

    # Ajouter ou modifier un commutateur
    st.subheader("Ajouter/Modifier un Commutateur")
    switch_name = st.text_input("Nom du Commutateur", value=st.session_state[office_selected]["switch_name"])
    ip_address = st.text_input("Adresse IP", value=st.session_state[office_selected]["ip_address"])
    picture = st.file_uploader("Télécharger une Image", type=["jpg", "jpeg", "png"], key=f"uploader_{office_selected}")
    
    if st.session_state[office_selected]["edit_switch_index"] is None:
        if st.button("Ajouter le Commutateur"):
            if switch_name and ip_address:
                new_switch = {
                    'name': switch_name,
                    'ip_address': ip_address,
                    'picture': picture.name if picture else None
                }
                if picture:
                    with open(os.path.join(IMAGES_FOLDER, picture.name), "wb") as f:
                        f.write(picture.getbuffer())
                office['switches'].append(new_switch)
                save_offices(st.session_state.offices)
                st.session_state[office_selected]["switch_name"] = ""
                st.session_state[office_selected]["ip_address"] = ""
                st.query_params.view_office = office_selected
    else:
        if st.button("Mettre à Jour le Commutateur"):
            index = st.session_state[office_selected]["edit_switch_index"]
            office['switches'][index]['name'] = switch_name
            office['switches'][index]['ip_address'] = ip_address
            if picture:
                office['switches'][index]['picture'] = picture.name
                with open(os.path.join(IMAGES_FOLDER, picture.name), "wb") as f:
                    f.write(picture.getbuffer())
            save_offices(st.session_state.offices)
            st.session_state[office_selected]["switch_name"] = ""
            st.session_state[office_selected]["ip_address"] = ""
            st.session_state[office_selected]["edit_switch_index"] = None
            st.query_params.view_office = office_selected
    
    # Supprimer un bureau
    st.subheader("Supprimer le Bureau")
    if st.button("Supprimer ce Bureau"):
        delete_sub_offices = st.checkbox("Supprimer également les sous-bureaux ?", value=True, key='checkbox3')
        if delete_sub_offices:
            st.session_state.offices = [off for off in st.session_state.offices if off['name'] != office_selected and off['parent_office'] != office_selected]
        else:
            st.session_state.offices = [off for off in st.session_state.offices if off['name'] != office_selected]
        save_offices(st.session_state.offices)
        st.query_params.view_office = None

# Effacer les paramètres de requête lors de la navigation entre les pages
st.query_params.clear()
