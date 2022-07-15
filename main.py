import streamlit as st
import requests
import os
import json
from PIL import Image
import random

st.set_page_config(page_title="Defect Detection", page_icon="🔎", layout="wide", initial_sidebar_state="collapsed")

if 'if_logged' not in st.session_state:
    st.session_state['if_logged'] = False
    st.session_state['access_token'] = ''

# cola, colb= st.columns([10,1])
# with colb:
logout_button = st.button(label = 'Logout', disabled=False)

if logout_button:
    st.session_state['if_logged'] = False




if st.session_state['if_logged'] == False:
    # logout_button = st.button(label = 'Logout', disabled=True)
    st.title('Welcome, Login to Continue')
    with st.form(key = 'login', clear_on_submit=True):
        # st.subheader("Login")
        username = st.text_input('Your Email ✉️')
        password = st.text_input("Your Password", type="password")
        submit = st.form_submit_button("Submit")
        if submit:
            # TODO: Change URL
            url = "https://maasapi.anandpiyush.com/login"
            payload={'username': username, 'password': password}
            # payload={'username': "test", 'password': "testpw"}
            response = requests.request("POST", url, data=payload)
            if response.status_code == 200:
                json_data = json.loads(response.text)
                # st.text(json_data["access_token"])
                st.session_state['access_token'] = json_data["access_token"]
                st.session_state['if_logged'] = True
                st.text("Login Successful")
                st.experimental_rerun()
                # logout_button.enabled = True
            else:
                st.text("Invalid Credentials ⚠️")
# else :
if st.session_state['if_logged'] == True:

    st.markdown("""
    # Metal Casting Quality Inspection
    Welcome to the Interactive Dashboard to detect manufacturing defect in metal casting process.

    ## To use this interface:
    1. Select a model for prediction
    2. Upload a photo of the manufactured product

    ---
    """)
    with st.expander("Sample Images"):
        st.header("Sample images from both the category")
        defect_img_file = random.choice(os.listdir("dataset/defect"))
        okay_img_file = random.choice(os.listdir("dataset/okay"))
        # TODO: Change file path
        defect_img = Image.open(os.path.join("dataset/defect", defect_img_file))
        okay_img = Image.open(os.path.join("dataset/okay", okay_img_file))
        col1, col2, col3= st.columns(3)
        with col1:
            st.subheader("Sample 1")
            st.image(defect_img, width = 300, caption='Defective Product')

        with col3:
            st.subheader("Sample 2")
            st.image(okay_img, width = 300, caption='Non Defective Product')

        with col2:
            st.subheader("Download Sample Images")
            with open("/Users/piyush/Sandbox/Streamlit_03/dataset/mini_sample.zip", "rb") as fp:
                st.download_button(
                    label="Download",
                    data = fp,
                    file_name='sample.zip',
                    mime='application/octet-stream',
                )
            
        
    with st.expander("Explore by uploading an image"):
        with st.container():
            model_name = st.radio(
            "Select a model",
            ('Cutmix', 'Mixup', 'Augmix'),
            help= "Models are trained using Data Augmentation technique",
            horizontal = True
            )

            uploaded_file = st.file_uploader("Choose a file")

            if uploaded_file is not None:
                try:
                    image = Image.open(uploaded_file)
                    st.image(image, width = 300, caption='You have uploaded')
                except Exception as e:
                    st.error("Please select a valid image *.jpeg")
                

            find_btn = st.button("Find Out")
        
        with st.container():    
            if find_btn:
                with st.spinner('Predicting ...'):
                    bytes_data = uploaded_file.getvalue()
                    files={'file': bytes_data}
                    # TODO: Change URL
                    url = f"https://maasapi.anandpiyush.com/maas/predict?model_name={model_name.lower()}"
                    headers = {}
                    headers['Authorization'] = f"Bearer {st.session_state['access_token']}"
                    response = requests.request("POST", url, headers=headers, files=files)
                    if response.status_code == 200:
                        json_data = json.loads(response.text)
                        # st.json(response.text)
                        # json_data["confidence"] = 35.00
                        if float(json_data["confidence"]) >= 75.00:
                            st.metric("This part is :", json_data["prediction"] , delta=f"with confidence {json_data['confidence']} %", delta_color="normal")
                        elif float(json_data["confidence"]) >= 25.00:
                            st.metric("This par is :", json_data["prediction"] , delta=json_data["confidence"], delta_color="off")
                        else:
                            st.metric("This par is :", json_data["prediction"] , delta=json_data["confidence"], delta_color="inverse")
                        st.balloons()
                        st.success('Done !')
                    elif response.status_code == 400:
                        st.error('Pass a correct file')
                    else:
                        st.write(response.status_code)
                        st.error('ERROR !')
                

